"""정차 후 관측창: MRC 도달 뒤 주변 NPC의 반응(상충 대리 지표)을 계측한다.

베이스라인(차로 내 정지)과 이동형 MRM(주차/노측)의 '2차 사고 노출' 비교용.
직접 충돌은 희귀사건이라 검정력이 없음 — 교통안전 표준인 대리 지표
(급감속 이벤트, 근접 통과, 최소 TTC)로 상충률을 잰다.

사용: source carla_envs.sh 후  python3 post_mrc_observe.py <window_s>
stdout 마지막 줄에 JSON 한 줄을 출력한다.
"""
import json
import math
import sys
import time

import carla

HARD_DECEL_MPS2 = -4.0   # 급감속 판정
CONFLICT_R = 35.0        # ego 주변 관심 반경 [m]
PASS_R = 6.0             # 근접 통과 판정 반경 [m]
DT = 0.25                # 샘플 주기 [s]


def main(window_s):
    client = carla.Client("localhost", 2000)
    client.set_timeout(5.0)
    world = client.get_world()

    ego = None
    for a in world.get_actors().filter("vehicle.*"):
        if a.attributes.get("role_name") in ("hero", "ego_vehicle"):
            ego = a
            break
    if ego is None:
        print(json.dumps({"error": "no ego"}))
        return

    el = ego.get_location()
    prev_speed = {}       # npc id -> (t, speed)
    prev_dist = {}        # npc id -> (t, dist)
    decel_latch = set()   # 이벤트 1회/접근 집계용
    hard_decel = 0
    pass_events = 0
    pass_latch = set()
    min_pass_gap = None
    min_ttc = None
    seen = set()

    t_end = time.time() + window_s
    while time.time() < t_end:
        t = time.time()
        try:
            actors = world.get_actors().filter("vehicle.*")
        except RuntimeError:
            break
        for v in actors:
            if v.attributes.get("role_name") in ("hero", "ego_vehicle"):
                continue
            loc = v.get_location()
            d = math.hypot(loc.x - el.x, loc.y - el.y)
            if d > 80.0:
                continue
            seen.add(v.id)
            vel = v.get_velocity()
            spd = math.hypot(vel.x, vel.y)

            # 급감속: ego 근방(CONFLICT_R)에서 dv/dt < HARD_DECEL
            pt, ps = prev_speed.get(v.id, (None, None))
            if pt is not None and t - pt > 0.0:
                acc = (spd - ps) / (t - pt)
                if d < CONFLICT_R and acc < HARD_DECEL_MPS2:
                    if v.id not in decel_latch:
                        hard_decel += 1
                        decel_latch.add(v.id)
                elif acc > -1.0:
                    decel_latch.discard(v.id)
            prev_speed[v.id] = (t, spd)

            # 근접 통과: PASS_R 이내를 주행 상태로 통과
            if d < PASS_R and spd > 1.0:
                if v.id not in pass_latch:
                    pass_events += 1
                    pass_latch.add(v.id)
                if min_pass_gap is None or d < min_pass_gap:
                    min_pass_gap = d
            elif d > PASS_R + 4.0:
                pass_latch.discard(v.id)

            # 최소 TTC: ego 로 접근 중(dist 감소율 > 0.5 m/s)일 때 d/closing
            dt_, dd = prev_dist.get(v.id, (None, None))
            if dt_ is not None and t - dt_ > 0.0:
                closing = (dd - d) / (t - dt_)
                if closing > 0.5 and d < CONFLICT_R:
                    ttc = d / closing
                    if min_ttc is None or ttc < min_ttc:
                        min_ttc = round(ttc, 2)
            prev_dist[v.id] = (t, d)
        time.sleep(DT)

    print(json.dumps({
        "obs_window_s": round(window_s, 1),
        "obs_hard_decel": hard_decel,
        "obs_pass_events": pass_events,
        "obs_min_pass_gap_m": round(min_pass_gap, 2) if min_pass_gap else "",
        "obs_min_ttc_s": min_ttc if min_ttc is not None else "",
        "obs_npc_seen": len(seen),
    }))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 110.0)
