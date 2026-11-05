#!/usr/bin/env python3
"""인식률(recall) 밖의 부작용 지표 — 허위 검출, 허위 정지, 급제동, 주행 지연, 추적 흔들림.
   (2026-11-05: "recall 만으로 건강도 적절성을 평가하면 범위가 좁다" 지적에 대한 보강. 기존 bag·GT 로 계산, 추가 실험 불필요)
사용: python3 side_effects.py <tag 패턴...>   예) side_effects.py lcl- lso- imn- nf-nf stock-lcl stock-lso stock-imn stock-nf
출력: results/side_effects.csv + 조건별 표(stdout)
지표(고장 뒤 구간):
  FP_s        차량·보행자 클래스 검출 중 GT 4 m 안에 아무것도 없는 것 / 초 (전방 50 m)
  FP_all_s    unknown 포함 허위 검출 / 초
  phantom_stops  신호(R/Y) 아님 + 앞 15 m 에 GT 객체 없음 + 목적지 아님 인데 2 s 이상 정지한 횟수 (GT)
  phantom_stop_s 그 정지 시간 합
  hard_brakes 제어 명령 가속도 < -3 m/s² 이벤트 수 (1 s 간격으로 분리)
  decel_events 가속도 < -2 m/s² 이벤트 수
  v_mean_active 고장 → 최종 정지(또는 끝) 구간 평균 속도 (적신호 대기 제외)
  t_to_goal   고장 → 목적지 30 m 이내 도달까지 시간 (못 가면 빈칸)
  track_churn 전방 50 m GT 차량 하나가 추적 ID 를 몇 번 갈아탔나 / 매칭된 분(min) 당
"""
import sys, csv, glob, math, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from noise_capability import read_gt, objects_frames, perception_metrics, nearest_tick, DET_TOPIC, DET_FALLBACK, MATCH_M, SECTOR_DEG, FAR_M, FP_M
TRK_TOPIC = "/perception/object_recognition/tracking/objects"   # TrackedObjects (pose_with_covariance, object_id)

RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results")
GOAL = (-102.0, 95.0)

def read_bag_sel(bag_dir, topics):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=str(bag_dir), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
    types = {t.name: t.type for t in r.get_all_topics_and_types()}
    out = collections.defaultdict(list); cls = {}; bad = set()
    while r.has_next():
        topic, data, t = r.read_next()
        if topic not in topics or topic in bad: continue
        if topic not in cls:
            try: cls[topic] = get_message(types[topic])
            except Exception: cls[topic] = None
        if cls[topic] is None: continue
        try: out[topic].append((t * 1e-9, deserialize_message(data, cls[topic])))
        except Exception: bad.add(topic)
    return out

STATIC_MASK = set()      # nf 런에서 반복되는 허위 검출 위치(5 m 격자) = GT 에 없는 정적 물체(주차 차량·구조물)

def fp_positions(frames, ego, actors, ts, t_fault, fid, lon_off=-1.4):
    """고장 뒤 전방 50 m 안 검출 중 GT(차량·보행자) 4 m 안에 없는 것의 (t, x, y) 목록과 프레임 수"""
    fps = []; n = 0
    for t, objs in frames:
        if t < t_fault: continue
        tk = nearest_tick(ts, t)
        if tk is None: continue
        n += 1
        e = ego[tk]; ex, ey, eyaw = e["x"], e["y"], math.radians(e["yaw_deg"])
        if fid != "map":
            bx, by = ex + lon_off * math.cos(eyaw), ey + lon_off * math.sin(eyaw); c, s_ = math.cos(eyaw), math.sin(eyaw)
            objs = [(bx + c * x - s_ * y, by + s_ * x + c * y, lab) for (x, y, lab) in objs]
        gts = [(a["x"], a["y"]) for a in actors.get(tk, [])]
        for (x, y, lab) in objs:
            dx, dy = x - ex, y - ey; d = math.hypot(dx, dy)
            if d > FAR_M: continue
            b = (math.degrees(math.atan2(dy, dx) - eyaw) + 180) % 360 - 180
            if abs(b) > SECTOR_DEG: continue
            if all(math.hypot(x - ax, y - ay) > FP_M for ax, ay in gts): fps.append((t, x, y))
    return fps, n

def cell(x, y): return (round(x / 5) * 5, round(y / 5) * 5)

def analyse(gt_path, bag_dir):
    tag = Path(gt_path).stem
    ego, actors, ts = read_gt(gt_path)
    rows = [ego[t] for t in ts]
    post = [r for r in rows if r["fault"] == 1]
    no_fault = not post
    if no_fault:
        t_go = next((r["aw_sec"] for r in rows if r["speed"] > 1.0), rows[0]["aw_sec"])
        post = [r for r in rows if r["aw_sec"] >= t_go + 30.0] or rows[len(rows) // 2:]
    t_fault = post[0]["aw_sec"]
    out = {"tag": tag, "no_fault": int(no_fault)}
    # ---- 활동 구간, 허위 정지, 목적지 도달
    def goal_d(r): return math.hypot(r["x"] - GOAL[0], r["y"] - GOAL[1])
    t_goal = next((r["aw_sec"] for r in post if goal_d(r) <= 30), None)
    out["t_to_goal"] = round(t_goal - t_fault, 1) if t_goal else ""
    t_stop = None
    for i in range(len(rows) - 1, -1, -1):
        if rows[i]["speed"] > 0.15: t_stop = rows[i + 1]["aw_sec"] if i + 1 < len(rows) else None; break
    act = [r for r in post if (t_stop is None or r["aw_sec"] < t_stop)]
    moving = [r for r in act if not (r.get("tl", "-") == "R" and r["speed"] < 0.15)]
    out["v_mean_active"] = round(sum(r["speed"] for r in moving) / len(moving), 2) if moving else ""
    # 정지 구간(2 s 이상) 중 설명 안 되는 것
    stops = []; cur = []
    for r in post:
        if r["speed"] < 0.15: cur.append(r)
        else:
            if len(cur) >= 40: stops.append(cur)
            cur = []
    if len(cur) >= 40: stops.append(cur)
    ph_n = 0; ph_s = 0.0
    for seg in stops:
        r0 = seg[0]
        if goal_d(r0) <= 30: continue
        if any(r.get("tl", "-") in ("R", "Y") for r in seg[:40]): continue
        lead = [a for a in actors.get(round(r0["aw_sec"], 3), []) if a["dist"] < 15 and abs(a["bearing_deg"]) < 30]
        if lead: continue
        ph_n += 1; ph_s += len(seg) / 20.0
    out["phantom_stops"] = ph_n; out["phantom_stop_s"] = round(ph_s, 1)
    # ---- bag: 허위 검출, 급제동, 추적 ID 흔들림
    bag = read_bag_sel(bag_dir, {DET_TOPIC, DET_FALLBACK, TRK_TOPIC, "/control/command/control_cmd"})
    det = bag.get(DET_TOPIC) or bag.get(DET_FALLBACK) or []
    if det:
        frames, fid = objects_frames(det)
        pm = perception_metrics(frames, ego, actors, ts, t_fault, MATCH_M, fid)
        out["R_h"] = round(pm.get("R_h", float("nan")), 2)
        fps, nfr = fp_positions(frames, ego, actors, ts, t_fault, fid)
        dur = max(1.0, (frames[-1][0] - max(t_fault, frames[0][0])))
        novel = [f for f in fps if cell(f[1], f[2]) not in STATIC_MASK]
        out["FP_s"] = round(len(fps) / dur, 2)                 # 전체 허위 검출/초 (정적 물체 포함)
        out["FP_novel_s"] = round(len(novel) / dur, 2)         # nf 에 없던 위치의 허위 검출/초 = 고장이 만든 유령
        out["FP_static_s"] = round((len(fps) - len(novel)) / dur, 2)
        out["_fp_cells"] = {cell(f[1], f[2]) for f in fps}
    cmds = [(t, m.longitudinal.acceleration) for t, m in bag.get("/control/command/control_cmd", []) if t >= t_fault]
    def events(th):
        n = 0; last = -1e9
        for t, a in cmds:
            if a < th and t - last > 1.0: n += 1; last = t
        return n
    out["hard_brakes"] = events(-3.0); out["decel_events"] = events(-2.0)
    # 추적 ID: GT 차량(전방 50 m)마다 2 m 안 추적객체 id 집합
    ids = collections.defaultdict(set); matched_frames = 0
    from noise_capability import stamp_s
    for _, m in bag.get(TRK_TOPIC, []):
        t = stamp_s(m.header)                      # bag 수신 시각이 아니라 헤더 스탬프(Autoware 시계)로 GT 와 정렬
        if t < t_fault: continue
        tk = nearest_tick(ts, t)
        if tk is None: continue
        e = ego[tk]
        trk = [(o.kinematics.pose_with_covariance.pose.position.x, o.kinematics.pose_with_covariance.pose.position.y, bytes(o.object_id.uuid)) for o in m.objects]
        for a in actors.get(tk, []):
            if a["kind"] != "veh" or a["dist"] > 50 or abs(a["bearing_deg"]) > 60: continue
            best = min(trk, key=lambda o: math.hypot(o[0] - a["x"], o[1] - a["y"]), default=None)
            if best and math.hypot(best[0] - a["x"], best[1] - a["y"]) <= MATCH_M:
                ids[a["id"]].add(best[2]); matched_frames += 1
    switches = sum(max(0, len(s) - 1) for s in ids.values())
    minutes = matched_frames / 10.0 / 60.0      # tracking ≈ 10 Hz
    out["track_churn"] = round(switches / minutes, 2) if minutes > 0.2 else ""
    out["n_tracked_veh"] = len(ids)
    return out

def main():
    pats = sys.argv[1:] or ["lcl-", "lso-", "imn-", "nf-nf", "stock-lcl", "stock-lso", "stock-imn", "stock-nf"]
    latest = {}
    for p in sorted(glob.glob(str(RES / "gt" / "*.csv"))):
        stem = Path(p).stem
        if not any(stem.startswith(x) for x in pats) or stem.startswith("eg-"): continue
        latest["-".join(stem.split("-")[:-1])] = p          # 같은 셀 여러 번이면 최신
    rows = []
    def ok_len(p):
        with open(p) as f:
            return sum(1 for _ in f) > 150 * 20 * 2      # 150 s 미만(CARLA 사망 등) 제외
    items = sorted(latest.items(), key=lambda kv: (0 if "nf-mid" in kv[0] or kv[0].startswith("nf-") or "-nf-nf-" in kv[0] else 1, kv[0]))
    for c, p in items:
        bag = RES / "bags" / Path(p).stem
        if not (bag / "metadata.yaml").exists() or not ok_len(p): continue
        try:
            r = analyse(p, bag)
            if ("nf-mid" in c or c.startswith("nf-") or "-nf-nf-" in c) and "_fp_cells" in r:
                STATIC_MASK.update(r["_fp_cells"])             # nf 런의 허위 검출 위치 → 정적 마스크
            r.pop("_fp_cells", None); rows.append(r)
            print("[ok]", c, {k: r[k] for k in ("FP_s", "FP_novel_s", "phantom_stops", "hard_brakes", "track_churn") if k in r}, flush=True)
        except Exception as e:
            print("[fail]", c, e, flush=True)
    print("static mask cells:", len(STATIC_MASK))
    if not rows: return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(RES / "side_effects.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    # 조건별 표: tag 의 fault / level
    def cond(tag):
        s = tag[6:] if tag.startswith("stock-") else tag
        p = s.split("-"); return p[0], p[1]
    g = collections.OrderedDict()
    for r in rows: g.setdefault(cond(r["tag"]), []).append(r)
    def mean(rs, k):
        v = [float(r[k]) for r in rs if r.get(k) not in ("", None) and not (isinstance(r.get(k), float) and math.isnan(r[k]))]
        return f"{sum(v)/len(v):.2f}" if v else "–"
    print("\n| fault | level | n | FP/s 전체 | FP/s 신규(유령) | 허위 정지 n | 허위 정지 s | 급제동 n | 감속 n | 활동 평균속도 | 목적지까지 s | 추적 ID 교체/분 |")
    print("|" + "---|" * 12)
    for (f, lv), rs in g.items():
        print(f"| {f} | {lv} | {len(rs)} | {mean(rs,'FP_s')} | {mean(rs,'FP_novel_s')} | {mean(rs,'phantom_stops')} | {mean(rs,'phantom_stop_s')} | {mean(rs,'hard_brakes')} | {mean(rs,'decel_events')} | {mean(rs,'v_mean_active')} | {mean(rs,'t_to_goal')} | {mean(rs,'track_churn')} |")
    print(f"\n-> {RES/'side_effects.csv'} ({len(rows)} cases)")

if __name__ == "__main__":
    main()
