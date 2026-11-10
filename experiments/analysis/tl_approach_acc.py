#!/usr/bin/env python3
"""신호등 인식 정확도 — 접근 거리대 기준(연속 지표; 정차 시간·주입 시점에 좌우되지 않음).  v2 (2026-11-10)
GT: results/gt/<tag>_tl.csv (kind=stop: 신호등별 정지선 x,y,yaw / kind=state: aw_sec, tl_id, 색 타임라인), results/gt/<tag>.csv ego 틱.
인식: bag /perception/traffic_light_recognition/traffic_signals — 틱마다 ≤0.5 s 이내 최근 메시지의 최고신뢰 요소. 색 ∈ {R,Y,G}; U(=UNKNOWN 요소)·빈 메시지·메시지 없음은 미인식.
틱 선택: 고장 주입 후(fault=1; nf 는 전체), 진행 방향 ±45° 안 전방 정지선까지 along ∈ (lo, hi] m, 횡 오프셋 ≤ 5 m, GT 색 R/Y/G 확정.
거리대 3종 × (전체 / 주행 중 v>0.5) = 6 변형을 한 번에 계산해 열로 저장: b20 = (3,20], b40 = (3,40], b60 = (3,60].
열: tag,fault,sev,npc,rep,n_enc, 그리고 각 변형 v∈{b20,b40,b60,b20m,b40m,b60m} 에 n_<v>, det_<v>(색 있음 비율), acc_<v>(GT 일치 비율)
사용: tl_approach_acc.py OUT.csv tag..."""
import sys, csv, os, re, math, collections, traceback, numpy as np
from pathlib import Path
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results")
COL = {1: "R", 2: "Y", 3: "G"}
TOPIC = "/perception/traffic_light_recognition/traffic_signals"
BANDS = {"b20": (3, 20), "b40": (3, 40), "b60": (3, 60)}
VARS = list(BANDS) + [b + "m" for b in BANDS]
def wrap(a): return (a + 180.0) % 360.0 - 180.0
out = sys.argv[1]; done = {r["tag"] for r in csv.DictReader(open(out))} if os.path.exists(out) else set()
fh = open(out, "a", newline=""); w = csv.writer(fh)
if not done: w.writerow(["tag", "fault", "sev", "npc", "rep", "n_enc"] + [f"{p}_{v}" for v in VARS for p in ("n", "det", "acc")])
for tag in sys.argv[2:]:
    if tag in done: continue
    try:
        m = re.match(r"stock-([a-z]+)-([^-]+)-(def|none|agg)-r(\d+)-", tag); fault, sev, npc, rep = m.groups()
        stops, states = {}, collections.defaultdict(list)
        for r in csv.DictReader(open(RES / "gt" / f"{tag}_tl.csv")):
            if r["kind"] == "stop": stops[r["tl_id"]] = (float(r["x"]), float(r["y"]), float(r["yaw_deg"]))
            elif r["kind"] == "state": states[r["tl_id"]].append((float(r["aw_sec"]), r["state"]))
        st_t = {k: np.array([a for a, _ in sorted(v)]) for k, v in states.items()}; st_c = {k: [c for _, c in sorted(v)] for k, v in states.items()}
        def gt_state(tl, t):
            if tl not in st_t or t < st_t[tl][0]: return None
            return st_c[tl][int(np.searchsorted(st_t[tl], t, side="right")) - 1]
        ego = [r for r in csv.DictReader(open(RES / "gt" / f"{tag}.csv")) if r["kind"] == "ego"]
        reader = rosbag2_py.SequentialReader(); reader.open(rosbag2_py.StorageOptions(uri=str(RES / "bags" / tag), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
        types = {t.name: t.type for t in reader.get_all_topics_and_types()}
        cls = get_message(types[TOPIC]); clk = get_message(types["/clock"])
        rec, clock = [], []
        while reader.has_next():
            tp, data, t_ns = reader.read_next()
            if tp == "/clock":
                mm = deserialize_message(data, clk); clock.append((t_ns * 1e-9, mm.clock.sec + mm.clock.nanosec * 1e-9))
            elif tp == TOPIC:
                mm = deserialize_message(data, cls); best = None
                for g in mm.traffic_light_groups:
                    for e in g.elements:
                        if e.color in COL and (best is None or e.confidence > best[1]): best = (COL[e.color], e.confidence)
                rec.append((t_ns * 1e-9, best[0] if best else None))
        clock = np.array(clock); rt = np.interp(np.array([r[0] for r in rec]), clock[:, 0], clock[:, 1]) if rec else np.array([]); rc = [r[1] for r in rec]
        def recog(t):
            i = int(np.searchsorted(rt, t)) - 1
            return None if (i < 0 or t - rt[i] > 0.5) else rc[i]
        cnt = {v: [0, 0, 0] for v in VARS}; enc = set()
        for r in ego:
            if fault != "nf" and r["fault"] != "1": continue
            t = float(r["aw_sec"]); ex, ey, yaw, v = float(r["x"]), float(r["y"]), float(r["yaw_deg"]), float(r["speed"])
            hx, hy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); best = None
            for tl, (sx, sy, syaw) in stops.items():
                dx, dy = sx - ex, sy - ey; along = dx * hx + dy * hy; lat = abs(dx * hy - dy * hx)
                if 3 < along <= 60 and lat <= 5 and abs(wrap(yaw - syaw)) <= 45 and (best is None or along < best[0]): best = (along, tl)
            if best is None: continue
            g = gt_state(best[1], t)
            if g not in ("R", "G", "Y"): continue
            c = recog(t); enc.add(best[1])
            for b, (lo, hi) in BANDS.items():
                if not (lo < best[0] <= hi): continue
                for key in ((b,) if v <= 0.5 else (b, b + "m")):
                    cnt[key][0] += 1; cnt[key][1] += (c is not None); cnt[key][2] += (c == g)
        row = [tag, fault, sev, npc, rep, len(enc)]
        for v in VARS:
            n, d, k = cnt[v]; row += [n, round(d / n, 3) if n else "", round(k / n, 3) if n else ""]
        w.writerow(row); fh.flush()
        print(tag, "enc", len(enc), " ".join(f"{v}:{cnt[v][0]}/{cnt[v][2]}" for v in VARS), flush=True)
    except Exception as e:
        print(tag, "ERR", type(e).__name__, e, flush=True)
