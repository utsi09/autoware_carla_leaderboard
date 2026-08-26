#!/usr/bin/env python3
"""v4.9 엣지 케이스 주입기 (0815 사용자 승인: 1 보행자 돌발 / 2 정지 장애물 / 3 갓길 점유).

tl_v2x_relay와 같은 패턴: LB 컨테이너(클라이언트 0.9.16)에서 독립 프로세스로 실행,
에이전트/러너 케이스 기계는 무수정. 러너는 케이스마다 이 프로세스를 hazard 인자와
함께 띄우기만 한다 (HAZARD env — launch_edge_battery.sh 참조).

모드:
  ped=<delay>:<dist>:<speed>      고장 t + delay 초에 에고 전방 dist m 우측 보도에서
                                  보행자가 speed m/s로 도로를 가로지름
  obstacle=<delay>:<dist>         고장 t + delay 초에 에고 차선 전방 dist m 지점에
                                  정지 차량 스폰 (브레이크 잠금)
  shoulder=<x1>:<y1>[,<x2>:<y2>]  케이스 시작 직후 지정 좌표(CARLA 프레임)에 주차
                                  차량 스폰 — 갓길 점유. AW 좌표는 y 부호 반전 주의.

트리거 시계: 에고가 처음 1 m/s를 넘는 순간을 주행 시작으로 보고, 그로부터
fault_t + delay 시뮬 초 뒤 발사(러너 케이스 타임라인과 동일 기준). 시드 무관
결정적 — 두 방법(순정/우리)이 같은 순간 같은 위치에서 같은 위험을 만난다.
"""
import argparse
import math
import sys
import time

import carla


def find_ego(world):
    for a in world.get_actors().filter("vehicle.*"):
        if a.attributes.get("role_name") in ("hero", "ego_vehicle"):
            return a
    return None


# [v4.9h] CARLA get_actors()가 외부 클라이언트에 빈 목록을 주는 상태(0815 실측:
# 프레시 서버에서도 케이스 내내 veh 0, 그러나 스폰·센서는 정상) — 에고 위치를
# ROS /localization/kinematic_state에서 읽는다 (AW->CARLA y 반전).
_ros = {"pose": None, "speed": 0.0, "t": 0.0}

def start_ros_ego_listener():
    # [v4.9t] 재호출 가능 — spin 스레드가 케이스 중반 DDS 이벤트로 죽는
    # 실측(0816: MRM 정지 직후 브레드크럼 영구 침묵) 대응 워치독이 다시 부른다
    import rclpy
    from nav_msgs.msg import Odometry
    import threading, math as _m

    try:
        rclpy.init()
    except RuntimeError:
        pass                                # 이미 init 됨 (재시작 경로)
    old = _ros.get("node")
    if old is not None:
        try:
            old.destroy_node()
        except Exception:
            pass
    _ros["gen"] = _ros.get("gen", 0) + 1
    node = rclpy.create_node(f"hazard_ego_listener_{_ros['gen']}")
    _ros["node"] = node

    def cb(msg):
        p = msg.pose.pose.position
        v = msg.twist.twist.linear
        _ros["pose"] = (p.x, -p.y)          # AW -> CARLA
        _ros["speed"] = _m.hypot(v.x, v.y)
        _ros["t"] = time.time()
        # [v5] 주행 시작 벽시계 (감지 래치 무장 기준점)
        if _ros["speed"] > 1.0 and "drive_t" not in _ros:
            _ros["drive_t"] = time.time()

    node.create_subscription(Odometry, "/localization/kinematic_state", cb, 10)

    # [v5-fix5] 섀도 감지 시각 = supervisor 상태 전이 (NORMAL -> 그 외).
    # 근거: gn 감지는 /monitor/scores가 아니라 supervisor 내부 잔차 감지기
    # (loc_meas/jump)에서 나옴 (S01 스모크 4차 실측: 토픽 점수는 0.7 위 유지,
    # supervisor det_latency 3.4~3.6 s). A1은 SUP_SHADOW=1 supervisor
    # (전이만·무행동)를 러너가 띄워 4팔 동일 감지기 보장.
    try:
        from std_msgs.msg import String as _Str

        def stcb(msg):
            # [sd 0827] settle 게이트용 현재 상태 — 래치와 무관하게 항상 갱신
            _ros["sup_state"] = msg.data.split(":")[0]
            if _ros.get("t_detect") or not _ros.get("detect_armed"):
                return
            st = _ros["sup_state"]
            if st not in ("NORMAL", "", "IDLE"):
                _ros["t_detect"] = time.time()
                _p6 = _ros.get("pose")
                _v6 = _ros.get("speed", 0.0)
                print(f"[hazard] DETECT supervisor state={msg.data} "
                      f"pos=({_p6[0]:.1f},{_p6[1]:.1f}) v={_v6:.2f}"
                      if _p6 else
                      f"[hazard] DETECT supervisor state={msg.data}",
                      flush=True)
        from rclpy.qos import QoSProfile, DurabilityPolicy
        node.create_subscription(
            _Str, "/mrm_supervisor/state", stcb,
            QoSProfile(depth=1,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL))
    except Exception as e:
        print(f"[hazard] state sub failed: {e!r}", flush=True)

    # [v5-fix3] rclpy.spin 중복 실행 금지('generator already executing') —
    # 전용 실행기 + spin_once 루프. 노드가 교체되면 옛 스레드는 자연 종료.
    from rclpy.executors import SingleThreadedExecutor
    _ex = SingleThreadedExecutor()
    _ex.add_node(node)

    def _spin():
        try:
            while rclpy.ok() and _ros.get("node") is node:
                _ex.spin_once(timeout_sec=0.2)
        except Exception as e:
            print(f"[hazard] ros spin died: {e!r}", flush=True)
        finally:
            try:
                _ex.remove_node(node)
            except Exception:
                pass

    th = threading.Thread(target=_spin, daemon=True)
    th.start()

def ros_ego():
    if _ros["pose"] is not None and time.time() - _ros["t"] < 3.0:
        return _ros["pose"], _ros["speed"]
    return None, 0.0


def speed_of(actor):
    v = actor.get_velocity()
    return math.hypot(v.x, v.y)


def spawn_ped_crossing(world, ego, dist, walk_speed):
    """에고 전방 dist의 도로 우측 가장자리에서 좌측으로 횡단하는 보행자.

    [v4.9b] 1차 설계(우측 7 m 보도 스폰)는 가드레일 바깥 풀밭에 떨어져
    보행자가 도로 진입을 못 하는 허수아비가 됨(0815 스크린샷 실측) —
    전방 도로 waypoint의 차선 우측 끝(+0.5 m)으로 스폰해 횡단을 보장한다."""
    tf = ego.get_transform()
    m = world.get_map()
    wp = m.get_waypoint(tf.location)
    nxt = wp.next(float(dist))
    if not nxt:
        print("[hazard] ped waypoint FAILED", flush=True)
        return None
    wtf = nxt[0].transform
    wright = wtf.get_right_vector()
    lane_edge = nxt[0].lane_width / 2.0 + 0.5
    loc = wtf.location + carla.Location(wright.x * lane_edge, wright.y * lane_edge)
    loc.z = wtf.location.z + 1.0
    right = wright                       # 횡단 방향 계산용 (도로 기준 우측)
    bp = world.get_blueprint_library().filter("walker.pedestrian.0001")[0]
    bp.set_attribute("is_invincible", "false")
    ped = world.try_spawn_actor(bp, carla.Transform(loc))
    if ped is None:
        print("[hazard] ped spawn FAILED (collision at spawn point)", flush=True)
        return None
    direction = carla.Vector3D(-right.x, -right.y, 0.0)   # 도로 안쪽으로
    # [v4.9d] 스폰 직후 첫 틱 전에 준 컨트롤은 씹힐 수 있음 (0815 액터 추적
    # 실측: 12초간 0.00 m 마네킹) — 초기 1회 + 호출부 상주 루프에서 재적용
    time.sleep(0.5)
    ped.apply_control(carla.WalkerControl(direction=direction,
                                          speed=float(walk_speed)))
    print(f"[hazard] PED spawned {dist}m ahead, crossing at {walk_speed} m/s "
          f"at ({loc.x:.1f},{loc.y:.1f})", flush=True)
    return ped, direction


_collision = {"hit": False, "with": ""}
_keep = []   # [v4.9u] 센서 액터 참조 유지 — GC로 콜백 사망 방지 (0816 실측 경고)

def attach_collision_sensor(world, ped):
    """[v4.9p] 보행자에 충돌 센서 부착 — 에고 핸들 불필요한 접촉 판정 정공법."""
    try:
        bp = world.get_blueprint_library().find("sensor.other.collision")
        sen = world.spawn_actor(bp, carla.Transform(), attach_to=ped)

        def _cb(ev):
            if not _collision["hit"]:
                _collision["hit"] = True
                _collision["with"] = ev.other_actor.type_id
                print(f"[hazard] COLLISION-SENSOR hit by {ev.other_actor.type_id}",
                      flush=True)
                # [v4.9r] 즉시 장부 기록 (종료 대기 없이 — cleanup kill 면역)
                import os as _o
                with open("/home/taewook/autoware_carla_leaderboard/experiments/"
                          "results/encounter_metrics.csv", "a") as _f:
                    _f.write(f"{int(time.time())},"
                             f"{_o.environ.get('CASE_TAG','untagged')},,"
                             f"CONTACT-SENSOR({ev.other_actor.type_id})\n")
        sen.listen(_cb)
        _keep.append(sen)
        return sen
    except Exception as e:
        print(f"[hazard] collision sensor attach failed: {e}", flush=True)
        return None


def spawn_ped_xy(world, pos, dist, walk_speed, lat_jitter=0.0):
    """[v4.9h] 에고 '좌표' 기준: 현 위치 waypoint의 dist m 전방 차선 우측
    끝에 보행자 스폰 (에고 액터 핸들 불필요). [v5] lat_jitter: 시드 고정
    횡방향 섭동(±m). 스폰·에고 세계좌표와 상대거리를 로그."""
    m = world.get_map()
    wp = m.get_waypoint(carla.Location(x=pos[0], y=pos[1], z=0.3))
    if wp is None:
        print("[hazard] ped_xy: no waypoint", flush=True)
        return None
    nxt = wp.next(float(dist))
    if not nxt:
        print("[hazard] ped_xy waypoint FAILED", flush=True)
        return None
    wtf = nxt[0].transform
    wright = wtf.get_right_vector()
    lane_edge = nxt[0].lane_width / 2.0 + 0.5 + lat_jitter
    loc = wtf.location + carla.Location(wright.x * lane_edge, wright.y * lane_edge)
    loc.z = wtf.location.z + 1.0
    bp = world.get_blueprint_library().filter("walker.pedestrian.0001")[0]
    bp.set_attribute("is_invincible", "false")
    ped = world.try_spawn_actor(bp, carla.Transform(loc))
    if ped is None:
        print("[hazard] ped_xy spawn FAILED", flush=True)
        return None
    direction = carla.Vector3D(-wright.x, -wright.y, 0.0)
    # [v4.9q 공정성] 걷기가 실제로 시작될 때까지 재명령 — 출발 지연이
    # 측면 충돌(불공정 기하)을 만들던 원인 (0816 사용자 진단)
    t0 = time.time()
    while time.time() - t0 < 2.5:
        ped.apply_control(carla.WalkerControl(direction=direction,
                                              speed=float(walk_speed)))
        time.sleep(0.2)
        v = ped.get_velocity()
        if (v.x * v.x + v.y * v.y) ** 0.5 > 1.0:
            break
    _rl = math.hypot(loc.x - pos[0], loc.y - pos[1])
    print(f"[hazard] PED spawned {dist:.0f}m ahead at ({loc.x:.1f},{loc.y:.1f}) "
          f"walking={((v.x*v.x+v.y*v.y)**0.5):.1f}m/s "
          f"ego=({pos[0]:.1f},{pos[1]:.1f}) rel={_rl:.2f}m", flush=True)
    return ped, direction


def spawn_obstacle(world, ego, dist):
    """에고 차선 전방 dist m 도로 위 정지 차량 (도로 정렬은 waypoint 사용)."""
    m = world.get_map()
    wp = m.get_waypoint(ego.get_transform().location)
    nxt = wp.next(float(dist))
    if not nxt:
        print("[hazard] obstacle waypoint FAILED", flush=True)
        return None
    tf = nxt[0].transform
    tf.location.z += 0.3
    bp = world.get_blueprint_library().filter("vehicle.tesla.model3")[0]
    obs = world.try_spawn_actor(bp, tf)
    if obs is None:
        print("[hazard] obstacle spawn FAILED", flush=True)
        return None
    obs.apply_control(carla.VehicleControl(brake=1.0, hand_brake=True))
    print(f"[hazard] OBSTACLE spawned {dist}m ahead at "
          f"({tf.location.x:.1f},{tf.location.y:.1f})", flush=True)
    return obs


def spawn_shoulder_blockers(world, coords):
    """갓길 좌표(CARLA 프레임)에 주차 차량 — 케이스 시작 시 1회."""
    bp = world.get_blueprint_library().filter("vehicle.audi.tt")[0]
    m = world.get_map()
    out = []
    for x, y in coords:
        wp = m.get_waypoint(carla.Location(x=x, y=y, z=0.3),
                            lane_type=carla.LaneType.Any)
        tf = wp.transform if wp else carla.Transform(carla.Location(x=x, y=y, z=0.3))
        tf.location.z += 0.3
        v = world.try_spawn_actor(bp, tf)
        if v is not None:
            v.apply_control(carla.VehicleControl(brake=1.0, hand_brake=True))
            out.append(v)
            print(f"[hazard] SHOULDER blocker at ({x:.1f},{y:.1f})", flush=True)
        else:
            print(f"[hazard] shoulder blocker FAILED at ({x:.1f},{y:.1f})", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True)          # ped / obstacle / shoulder
    ap.add_argument("--spec", required=True)          # 모드별 파라미터 문자열
    ap.add_argument("--fault-t", type=float, default=0.0)
    args = ap.parse_args()

    client = carla.Client("localhost", 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    # [v4.9h] 에고 존재/위치는 ROS 오도메트리로 판정 (CARLA 액터목록 불신)
    start_ros_ego_listener()
    pose = None
    for _ in range(600):
        pose, _v = ros_ego()
        if pose is not None:
            break
        time.sleep(0.5)
    if pose is None:
        print("[hazard] ego odom never appeared — exit", flush=True)
        sys.exit(1)
    print(f"[hazard] ego odom live at ({pose[0]:.1f},{pose[1]:.1f})", flush=True)

    if args.mode == "shoulder":
        if args.spec == "auto":
            # [v4.9c 사용자 설계] 고정 좌표 대신 "슈퍼바이저가 고른 갓길"에
            # 즉시 스폰 — 조우 보장. 선택 좌표는 supervisor.log의
            # "MRM goal sent: shoulder_X (x, y)" (AW 프레임 -> y 반전).
            # 첫 선택만 막는다(폴백 품질 측정이 목적, 전부 막으면 소진 시험).
            import re
            LOG = ("/home/taewook/autoware_carla_leaderboard/experiments/"
                   "results/supervisor.log")
            pat = re.compile(r"MRM goal sent: (shoulder_\d+) \(([-0-9.]+), ([-0-9.]+)\)")
            spawned = False
            miss = 0
            while not spawned and miss < 300:
                try:
                    with open(LOG) as f:
                        mlist = pat.findall(f.read())
                except OSError:
                    mlist = []
                if mlist:
                    name, x, y = mlist[0]
                    spawn_shoulder_blockers(world, [(float(x), -float(y))])
                    print(f"[hazard] AUTO blocker on chosen {name}", flush=True)
                    spawned = True
                    break
                if find_ego(world) is None:
                    miss += 1
                time.sleep(1.0)
        else:
            coords = [tuple(float(v) for v in p.split(":")) for p in args.spec.split(",")]
            spawn_shoulder_blockers(world, coords)
        # 스폰 유지를 위해 케이스 끝(에고 소멸)까지 상주
        miss = 0
        while miss < 15:
            miss = miss + 1 if find_ego(world) is None else 0
            time.sleep(2.0)
        return

    if args.spec.startswith("fixed") or args.spec.startswith("dist"):
        # [v4.9m] fixed:<TTC초> | [v4.9s] dist:<정확한 스폰거리 m> (거리 사다리)
        _ttc = 2.5
        _dist_fixed = None
        _gate_v = 3.0       # [v4.9t] 발사 최저 속도 (저속 MRM 비교는 낮춰야 함)
        _arm_after = None   # [v4.9t] dist:<m>:<gate>:arm — 고장+MRM 진입 후에만 발사
        _time_trig = None   # [v5] t<초>: t_detect+delay에 속도 불문 발사
        _lat_jit = 0.0      # [v5] j<미터>: 스폰 횡방향 섭동 (시드 고정)
        _settle_band = None  # [sd 0827] s<lo>x<hi>: 정착 속도 밴드 트리거
        if args.spec.startswith("dist") and ":" in args.spec:
            _p = args.spec.split(":")
            _dist_fixed = float(_p[1])
            for _tok in _p[2:]:
                if _tok == "arm":
                    _arm_after = args.fault_t + 3.0
                elif _tok.startswith("s") and "x" in _tok:
                    _settle_band = tuple(float(v) for v in _tok[1:].split("x"))
                elif _tok.startswith("t"):
                    _time_trig = float(_tok[1:])
                elif _tok.startswith("w"):
                    _walk_override = float(_tok[1:])
                elif _tok.startswith("j"):
                    _lat_jit = float(_tok[1:])
                else:
                    _gate_v = float(_tok)
        elif ":" in args.spec:
            _ttc = float(args.spec.split(":")[1])
        delay, dist = 0.0, 22.0
        try:
            walk_speed = _walk_override   # [v5] w<speed> 토큰이 있으면 우선
        except NameError:
            walk_speed = 3.0
    else:
        parts = [float(v) for v in args.spec.split(":")]
        delay, dist = parts[0], parts[1]
        walk_speed = parts[2] if len(parts) > 2 else 3.0

    # [v4.9h] fixed 모드는 트리거 루프가 위치·속도를 직접 gate하므로
    # 액터목록 의존인 주행시작 대기를 통째로 건너뛴다
    if args.spec.startswith("fixed") or args.spec.startswith("dist"):
        t_drive = 0.0
    else:
        pass
    # 주행 시작(>1 m/s) 감지 → 시뮬 시계로 fault_t + delay 대기.
    # 액터 핸들은 낡을 수 있어(스모크 실측: is_alive 거짓 양성으로 조기 종료)
    # 매 반복 재조회하고, 연속 30초 미발견일 때만 종료한다.
    t_drive = None if not (args.spec.startswith("fixed") or args.spec.startswith("dist")) else 0.0
    miss = 0
    while not (args.spec.startswith("fixed") or args.spec.startswith("dist")):
        try:
            world = client.get_world()
            snap = world.get_snapshot()
        except Exception:
            time.sleep(0.5); continue
        ego = find_ego(world)
        if ego is None:
            miss += 1
            if miss > 150:      # 0.2s * 150 = 30s
                print("[hazard] ego gone before trigger — exit", flush=True)
                return
            time.sleep(0.2)
            continue
        miss = 0
        if t_drive is None and speed_of(ego) > 1.0:
            t_drive = snap.timestamp.elapsed_seconds
            print(f"[hazard] drive start at sim {t_drive:.1f}s; firing at "
                  f"+{args.fault_t + delay:.0f}s", flush=True)
        if t_drive is not None and \
                snap.timestamp.elapsed_seconds - t_drive >= args.fault_t + delay:
            break
        time.sleep(0.2)

    # [v5 절제] FREEZE_TL=1: 전 신호등 녹색 동결 — TL 위상이 부팅 지터로
    # 팔마다 달라지는 교란 제거 (S01 스모크 5차 실측: A2 적신호 정지 중 조우
    # vs A3 주행 중 조우). 신호 상호작용은 절제 범위 밖으로 명시 분리.
    import os as _oft
    if _oft.environ.get("FREEZE_TL") == "1":
        try:
            _w = client.get_world()
            _n_tl = 0
            for _tl in _w.get_actors().filter("traffic.traffic_light*"):
                _tl.set_state(carla.TrafficLightState.Green)
                _tl.freeze(True)
                _n_tl += 1
            print(f"[hazard] froze {_n_tl} traffic lights GREEN", flush=True)
        except Exception as e:
            print(f"[hazard] TL freeze failed: {e!r}", flush=True)

    ped = direction = None
    if args.mode == "ped":
        # [v4.9f 사용자 설계: 위치 고정 트리거] 리더보드 DynamicObjectCrossing
        # 방식 — 경로가 4개뿐이므로 임무·MRM 회랑의 길목에 트리거 지점을 박고,
        # 에고가 "주행 중" 그 지점을 지나는 순간 전방에 충돌 코스 스폰.
        # 타이밍 추정(고장+N초/속도 대기)의 불확실성 제거. CARLA 프레임 좌표.
        TRIGGERS = [(-2.0, -25.0),     # 임무 남북 직선로 (신호교차로 남측)
                    (-2.0, 25.0),      # 신호교차로 북측 (E 갓길 회랑)
                    (-55.0, -5.3),     # 서향 회랑 (S 갓길 경로)
                    (-96.5, -15.0),    # 서측 남북로 (W 갓길 경로)
                    (-50.0, -109.0)]   # 임무 서측 구간
        fired = False
        # [v5 절제] 시간 트리거: t_detect(cdr 점수<0.7) + delay 에 속도·상태
        # 불문, 에고 현재 위치 전방 dist m 발사. 정지 상태여도 발사 —
        # 발사가 treatment에 종속되지 않게 (전문가 검토 반영).
        if _time_trig is not None:
            t_wait0 = time.time()
            while not fired and time.time() - t_wait0 < 600.0:
                (pos, v) = ros_ego()
                if pos is None:
                    if _ros["t"] > 0 and time.time() - _ros["t"] > 6.0 and \
                            time.time() - globals().get("_last_restart", 0) > 10.0:
                        globals()["_last_restart"] = time.time()
                        print("[hazard] odom stale — listener restart", flush=True)
                        try:
                            start_ros_ego_listener()
                        except Exception as e:
                            print(f"[hazard] restart failed: {e!r}", flush=True)
                    time.sleep(0.2)
                    continue
                # [v5-fix] 감지 래치 무장: 주행 시작 + (fault_t - 2 s) 이후
                _dt0 = _ros.get("drive_t")
                if _dt0 and not _ros.get("detect_armed") and \
                        time.time() - _dt0 >= max(args.fault_t - 2.0, 0.0):
                    _ros["detect_armed"] = True
                    print(f"[hazard] detect latch armed "
                          f"(+{time.time()-_dt0:.0f}s)", flush=True)
                _td = _ros.get("t_detect")
                if _td is None or time.time() - _td < _time_trig:
                    time.sleep(0.05)
                    continue
                # 지터는 시드 파일에 부호 포함 고정값 — 같은 시드의 4팔이
                # 동일 오프셋을 받도록 그대로 사용 (재샘플링 금지)
                _j = _lat_jit
                print(f"[hazard] TIME-TRIGGER fire t_detect+{_time_trig:.1f}s "
                      f"ego v={v:.2f} at ({pos[0]:.1f},{pos[1]:.1f}) "
                      f"jit={_j:+.2f}m", flush=True)
                try:
                    world = client.get_world()
                except Exception:
                    world = None
                if world is not None:
                    r = spawn_ped_xy(world, pos, _dist_fixed, walk_speed,
                                     lat_jitter=_j)
                    if r is not None:
                        ped, direction = r
                        attach_collision_sensor(world, ped)
                fired = True
        # [sd 0827 speed-dose] 정착 트리거: supervisor가 MRM_MOVE 상태이고
        # 실측 속도가 [lo,hi] 밴드에 1.0 s 연속 머무를 때 현 위치 전방 D m 발사.
        # 과도구간 발사(t3.0)와 달리 '상한이 실제로 성립한 정착 상태'의 조우만
        # 만든다 — 조작 점검(manipulation check)이 트리거에 내장된 설계.
        # 420 s 내 미발사는 배치가 MANIPULATION_FAIL로 재실행.
        if _settle_band is not None and not fired:
            _lo, _hi = _settle_band
            _band_since = None
            _lastbc2 = 0.0
            t_wait0 = time.time()
            while not fired and time.time() - t_wait0 < 420.0:
                (pos, v) = ros_ego()
                if pos is None:
                    if _ros["t"] > 0 and time.time() - _ros["t"] > 6.0 and \
                            time.time() - globals().get("_last_restart", 0) > 10.0:
                        globals()["_last_restart"] = time.time()
                        print("[hazard] odom stale — listener restart", flush=True)
                        try:
                            start_ros_ego_listener()
                        except Exception as e:
                            print(f"[hazard] restart failed: {e!r}", flush=True)
                    _band_since = None
                    time.sleep(0.2)
                    continue
                _st = _ros.get("sup_state", "")
                if time.time() - _lastbc2 > 5.0:
                    _lastbc2 = time.time()
                    print(f"[hazard] settle-wait v={v:.2f} state={_st} "
                          f"({pos[0]:.1f},{pos[1]:.1f})", flush=True)
                if _st != "MRM_MOVE" or not (_lo <= v <= _hi):
                    _band_since = None
                elif _band_since is None:
                    _band_since = time.time()
                    print(f"[hazard] settle band entered v={v:.2f}", flush=True)
                elif time.time() - _band_since >= 1.0:
                    print(f"[hazard] SETTLE-TRIGGER fire v={v:.2f} "
                          f"band=[{_lo:.2f},{_hi:.2f}] at "
                          f"({pos[0]:.1f},{pos[1]:.1f})", flush=True)
                    try:
                        world = client.get_world()
                    except Exception:
                        world = None
                    if world is not None:
                        r = spawn_ped_xy(world, pos, _dist_fixed, walk_speed,
                                         lat_jitter=_lat_jit)
                        if r is not None:
                            ped, direction = r
                            attach_collision_sensor(world, ped)
                    fired = True
                time.sleep(0.05)
        t_wait0 = time.time()
        _lastbc = 0.0
        _t_drive_wall = None   # [v4.9t] 주행 시작 벽시계 (arm 기준점)
        _wait_max = 420.0 if _arm_after is not None else 300.0
        # [sd 0827] settle 모드는 위 전용 루프가 전담 — 일반 루프 진입 금지
        # (settle 미발사 시 길목 트리거가 대신 발사해 조작 점검을 오염 방지)
        while not fired and _settle_band is None and \
                time.time() - t_wait0 < _wait_max:
            (pos, v) = ros_ego()
            if pos is None:
                # [v4.9t] 오돔 6s 이상 정지면 리스너 재시작 (spin 스레드 사망 실측)
                if _ros["t"] > 0 and time.time() - _ros["t"] > 6.0 and \
                        time.time() - globals().get("_last_restart", 0) > 10.0:
                    globals()["_last_restart"] = time.time()
                    print(f"[hazard] odom stale "
                          f"{time.time() - _ros['t']:.0f}s — listener restart",
                          flush=True)
                    try:
                        start_ros_ego_listener()
                    except Exception as e:
                        print(f"[hazard] listener restart failed: {e!r}",
                              flush=True)
                time.sleep(0.3); continue
            if _t_drive_wall is None and v > 1.0:
                _t_drive_wall = time.time()
                if _arm_after is not None:
                    print(f"[hazard] drive start; arming at +{_arm_after:.0f}s "
                          f"(fault_t={args.fault_t:.0f})", flush=True)
            if time.time() - _lastbc > 5.0:
                _lastbc = time.time()
                print(f"[hazard] breadcrumb ({pos[0]:.1f},{pos[1]:.1f}) v={v:.1f}",
                      flush=True)
            # [v4.9t] arm 모드: 고장+MRM 진입 전엔 발사 금지 (MRM 저속 비교용)
            _armed = _arm_after is None or \
                (_t_drive_wall is not None and
                 time.time() - _t_drive_wall >= _arm_after)
            _in_corr = any(math.hypot(pos[0] - tx, pos[1] - ty) < 8.0
                           for tx, ty in TRIGGERS)
            # [v4.9t] 미발사 원인 가시화 (게이트/무장 상태 전이마다 1줄)
            if _in_corr and not fired:
                _why = ("ok" if (_armed and v >= _gate_v) else
                        "not-armed" if not _armed else "v<gate")
                if _why != globals().get("_last_why"):
                    globals()["_last_why"] = _why
                    print(f"[hazard] corridor pass v={v:.1f} armed={_armed} "
                          f"-> {_why}", flush=True)
            if not _armed:
                time.sleep(0.1); continue
            # [v4.9l] 저속(가속 구간) 발동이면 실명 차도 회피 가능 — 순항
            # 속도에서만 발동해 경계 강도가 감지거리를 실제로 시험하게 한다
            # [v4.9t] arm 모드는 길목 불문 — 무장(고장+MRM 진입) 후 주행 중이면
            # 현 위치에서 발사. 길목은 무장 전에 지나가 버리는 게 실측 원인.
            if v >= _gate_v and (_in_corr or _arm_after is not None):
                # [v4.9m] TTC 파라미터화 — 강도 스윕 (2.5=경계 ... 1.2=극한)
                # [v4.9s] 거리 사다리: 명시 거리 우선, 아니면 TTC 공식
                if _dist_fixed is not None:
                    dist = _dist_fixed
                else:
                    dist = min(max(v * _ttc + 4.0, 8.0), 30.0)
                print(f"[hazard] fixed-trigger spawn: ego v={v:.1f} -> "
                      f"dist={dist:.1f} at ({pos[0]:.1f},{pos[1]:.1f})", flush=True)
                try:
                    world = client.get_world()
                except Exception:
                    world = None
                if world is not None:
                    r = spawn_ped_xy(world, pos, dist, walk_speed)
                    if r is not None:
                        ped, direction = r
                        attach_collision_sensor(world, ped)
                fired = True
            time.sleep(0.1)
    elif args.mode == "obstacle":
        spawn_obstacle(world, ego, dist)

    # [v4.9g] 조우 자가 녹화: 스폰 주체가 곧 촬영 주체 — 타이밍 공백 없음.
    # 에고 추격캠 10fps, 30 s. 프레임은 pedcam_<ts>/ (호스트 인코더가 mp4화).
    rec_cam = None
    # [v5 절제] 물리 틱 동기 간격 기록 — wall-clock 폴링 대신 CARLA 프레임마다
    # (frame ID로 영상·충돌 이벤트와 정렬). 에고 좌표는 ROS 최신값 사용.
    if ped is not None:
        try:
            import os as _os5
            _tf5 = open("/home/taewook/autoware_carla_leaderboard/experiments/"
                        f"results/tick_{_os5.environ.get('CASE_TAG','case')}_"
                        f"{int(time.time())}.csv", "w", buffering=1)
            _tf5.write("frame,sim_t,ego_x,ego_y,ped_x,ped_y,gap,ego_v\n")
            _pedref5 = ped

            def _tcb5(snap):
                try:
                    _p5, _v5 = ros_ego()
                    if _p5 is None:
                        return
                    _wl5 = _pedref5.get_transform().location
                    _g5 = max(math.hypot(_p5[0] - _wl5.x,
                                         _p5[1] - _wl5.y) - 1.25, 0.0)
                    _tf5.write(f"{snap.frame},"
                               f"{snap.timestamp.elapsed_seconds:.3f},"
                               f"{_p5[0]:.2f},{_p5[1]:.2f},"
                               f"{_wl5.x:.2f},{_wl5.y:.2f},"
                               f"{_g5:.3f},{_v5:.2f}\n")
                except Exception:
                    pass
            world.on_tick(_tcb5)
        except Exception as e:
            print(f"[hazard] tick log failed: {e!r}", flush=True)
    rec_q = None
    rec_n = 0
    rec_dir = None
    if ped is not None:
        try:
            import os as _os, queue as _q
            _tag = _os.environ.get("CASE_TAG", "case")
            rec_dir = ("/home/taewook/autoware_carla_leaderboard/experiments/"
                       f"results/pvid_{_tag}_{int(time.time())}")
            _os.makedirs(rec_dir, exist_ok=True)
            _bp = world.get_blueprint_library().find("sensor.camera.rgb")
            _bp.set_attribute("image_size_x", "960")
            _bp.set_attribute("image_size_y", "540")
            _bp.set_attribute("sensor_tick", "0.1")
            _pl = ped.get_transform().location
            rec_cam = world.spawn_actor(
                _bp, carla.Transform(
                    carla.Location(x=_pl.x, y=_pl.y, z=_pl.z + 24.0),
                    carla.Rotation(pitch=-90.0)))
            rec_q = _q.Queue(maxsize=4)

            def _rcb(im):
                try:
                    rec_q.put_nowait(im)
                except Exception:
                    pass
            rec_cam.listen(_rcb)
            print(f"[hazard] self-recording -> {rec_dir}", flush=True)
        except Exception as e:
            print(f"[hazard] rec setup failed: {e}", flush=True)
            rec_cam = None

    # 사건 관찰 동안 상주 (러너 cleanup이 프로세스를 정리)
    # [v4.9d] 보행자 걷기 명령 1초마다 재적용 + 이동 실측 로그 (마네킹 방지)
    miss = 0
    p0 = ped.get_transform().location if ped is not None else None
    ticks = 0
    while miss < 15:
        miss = miss + 1 if find_ego(world) is None else 0
        if ped is not None:
            try:
                # [v4.9v] 관찰 루프에도 오돔 워치독 — gn 케이스 3건에서 리스너
                # 사망으로 간격 기록 0줄 -> 무근거 '회피' 오판 (0816 사용자 적발)
                _p, _ = ros_ego()
                if _p is None and _ros["t"] > 0 and \
                        time.time() - _ros["t"] > 6.0 and \
                        time.time() - globals().get("_last_restart", 0) > 10.0:
                    globals()["_last_restart"] = time.time()
                    print("[hazard] odom stale in obs loop — listener restart",
                          flush=True)
                    try:
                        start_ros_ego_listener()
                    except Exception as e:
                        print(f"[hazard] restart failed: {e!r}", flush=True)
                if _p is not None:
                    _wl = ped.get_transform().location
                    _d = math.hypot(_p[0] - _wl.x, _p[1] - _wl.y)
                    _g = max(_d - 1.25, 0.0)   # 표면 간격 (차 반폭+사람 반경 제외)
                    if not hasattr(main, "_min_gap") or _g < main._min_gap:
                        main._min_gap = _g
                        tag = " CONTACT-LIKELY" if _g <= 0.30 else ""
                        print(f"[hazard] MIN-GAP {_g:.2f}m{tag}", flush=True)
                # [v4.9u] 횡단 완료(12m) 후 정지 — 계속 걸으면 실험 기하 밖에서
                # 늦은 접촉이 생겨 8m 경계 지표를 오염 (0816 케이스7 실측)
                _pnow = ped.get_transform().location
                _moved_total = math.hypot(_pnow.x - p0.x, _pnow.y - p0.y)
                # [v4.9v] 물리 기반 접촉 오라클 — 워커 부착 충돌센서는 CARLA에서
                # 미작동 실측(공식 충돌 확정 4건에서도 전부 침묵). 충격 신호:
                # 보행 물리(실측 <=1.5m/s)로 불가능한 속도, 또는 1틱 순간이동.
                _wv = ped.get_velocity()
                _wspd = math.hypot(_wv.x, _wv.y)
                _lastwp = globals().get("_lastwp")
                _jump = (math.hypot(_pnow.x - _lastwp[0], _pnow.y - _lastwp[1])
                         if _lastwp else 0.0)
                globals()["_lastwp"] = (_pnow.x, _pnow.y)
                if (_wspd > 4.5 or _jump > 5.0) and not _collision["hit"]:
                    _collision["hit"] = True
                    _collision["with"] = "physics"
                    print(f"[hazard] CONTACT-PHYSICS wspd={_wspd:.1f} "
                          f"jump={_jump:.1f}m", flush=True)
                    import os as _o
                    with open("/home/taewook/autoware_carla_leaderboard/"
                              "experiments/results/encounter_metrics.csv",
                              "a") as _f:
                        _f.write(f"{int(time.time())},"
                                 f"{_o.environ.get('CASE_TAG','untagged')},,"
                                 f"CONTACT-PHYSICS\n")
                ped.apply_control(carla.WalkerControl(
                    direction=direction,
                    speed=0.0 if _moved_total > 12.0 else float(walk_speed)))
                ticks += 1
                if ticks in (3, 8):
                    print(f"[hazard] ped moved {_moved_total:.1f}m "
                          f"({_pnow.x:.1f},{_pnow.y:.1f})", flush=True)
            except Exception:
                ped = None          # 보행자 소멸(충돌/케이스 종료)
        # 자가 녹화 프레임 소화 (30 s = 300프레임 한도)
        if rec_cam is not None:
            t_end = time.time() + 1.0
            while time.time() < t_end and rec_n < 300:
                try:
                    im = rec_q.get(timeout=0.2)
                    im.save_to_disk(f"{rec_dir}/f{rec_n:04d}.png")
                    rec_n += 1
                    # [v4.9j] 10 Hz 정밀 최소간격 (1 Hz는 최근접점 놓침)
                    if ped is not None:
                        _p2, _ = ros_ego()
                        if _p2 is not None:
                            _w2 = ped.get_transform().location
                            _d2 = math.hypot(_p2[0] - _w2.x, _p2[1] - _w2.y)
                            _g2 = max(_d2 - 1.25, 0.0)
                            if not hasattr(main, "_min_gap") or _g2 < main._min_gap:
                                main._min_gap = _g2
                                tag = " CONTACT-LIKELY" if _g2 <= 0.30 else ""
                                print(f"[hazard] MIN-GAP {_g2:.2f}m{tag}",
                                      flush=True)
                except Exception:
                    break
            if rec_n >= 300:
                try:
                    rec_cam.destroy()
                except Exception:
                    pass
                rec_cam = None
                open(f"{rec_dir}/DONE", "w").write(str(rec_n))
                print(f"[hazard] self-recording done {rec_n} frames", flush=True)
        else:
            time.sleep(1.0)

    # [v4.9o 데이터 무결성] 케이스별 조우 장부 — 태그·최소간격·접촉을 한 줄로
    # 영구 기록 (로그 회전·짝짓기 오염 원천 차단)
    try:
        _tag = os.environ.get("CASE_TAG", "untagged") if "os" in dir() else "untagged"
    except Exception:
        _tag = "untagged"
    import os as _os2
    _tag = _os2.environ.get("CASE_TAG", "untagged")
    _mg = getattr(main, "_min_gap", None)
    if _collision["hit"]:
        _contact = f"CONTACT-SENSOR({_collision['with']})"
    elif _mg is not None and _mg <= 0.30:
        _contact = "CONTACT-GAP"
    elif _mg is None:
        _contact = "NO-ENCOUNTER"
    else:
        _contact = "CLEAR"
    with open("/home/taewook/autoware_carla_leaderboard/experiments/results/"
              "encounter_metrics.csv", "a") as _f:
        _f.write(f"{int(time.time())},{_tag},"
                 f"{'' if _mg is None else f'{_mg:.2f}'},{_contact}\n")
    print(f"[hazard] LEDGER {_tag} min_gap="
          f"{'' if _mg is None else f'{_mg:.2f}'} {_contact}", flush=True)


if __name__ == "__main__":
    main()
