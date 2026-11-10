#!/usr/bin/env python3
"""신호등 인식 정확도(연속 지표) — 카메라 잡음 세기 곡선을 매끄럽게: 런마다 GT 신호 색(G/R/Y, GT csv 'tl' 열)이 있는 시각에서
Autoware /perception/traffic_light_recognition/traffic_signals 의 최근(≤0.5 s) 메시지 중 최고 신뢰도 요소 색이 GT 와 같으면 성공.
출력 results/alibi/../tl_acc.csv: tag, fault, sev, rep, n_frames(신호 있는 GT 틱), n_match, acc, acc_post(주입 후만), acc_pre.
사용: tl_recog_acc.py OUT.csv tag..."""
import sys, csv, os, numpy as np, re
from pathlib import Path
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results")
COL = {1: "R", 2: "Y", 3: "G"}   # TrafficLightElement.color: RED=1 AMBER=2 GREEN=3
out = sys.argv[1]; done = {r["tag"] for r in csv.DictReader(open(out))} if os.path.exists(out) else set()
fh = open(out, "a", newline=""); w = csv.writer(fh)
if not done: w.writerow(["tag", "fault", "sev", "rep", "n_frames", "n_match", "acc", "n_pre", "acc_pre", "n_post", "acc_post"])
for tag in sys.argv[2:]:
    if tag in done: continue
    try:
        m = re.match(r"stock-([a-z]+)-([^-]+)-(def|none|agg)-r(\d+)-", tag); fault, sev, rep = m.group(1), m.group(2), m.group(4)
        gt = [r for r in csv.DictReader(open(RES / "gt" / f"{tag}.csv")) if r["kind"] == "ego"]
        reader = rosbag2_py.SequentialReader(); reader.open(rosbag2_py.StorageOptions(uri=str(RES / "bags" / tag), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
        types = {t.name: t.type for t in reader.get_all_topics_and_types()}
        topic = "/perception/traffic_light_recognition/traffic_signals"; cls = get_message(types[topic]); clk = get_message(types["/clock"]) if "/clock" in types else None
        rec = []  # (sim_t, color of top-confidence element over all groups)
        clock = []
        while reader.has_next():
            tp, data, t_ns = reader.read_next()
            if tp == "/clock" and clk is not None:
                mm = deserialize_message(data, clk); clock.append((t_ns * 1e-9, mm.clock.sec + mm.clock.nanosec * 1e-9))
            elif tp == topic:
                mm = deserialize_message(data, cls); best = None
                for g in mm.traffic_light_groups:
                    for e in g.elements:
                        if e.color in COL and (best is None or e.confidence > best[1]): best = (COL[e.color], e.confidence)
                rec.append((t_ns * 1e-9, best[0] if best else None))
        clock = np.array(clock); 
        def bag2sim(tb): return np.interp(tb, clock[:, 0], clock[:, 1])
        rt = bag2sim(np.array([r[0] for r in rec])) if rec else np.array([]); rc = [r[1] for r in rec]
        # GT sim time: 'sim_t' is leaderboard sim time; bag /clock is Autoware sim time (aw_sec) → use aw_sec
        n = nm = npre = mpre = npost = mpost = 0
        for r in gt:
            c = r["tl"]
            if c not in ("G", "R", "Y"): continue
            t = float(r["aw_sec"]); i = np.searchsorted(rt, t) - 1
            ok = i >= 0 and t - rt[i] <= 0.5 and rc[i] == c
            n += 1; nm += ok
            if r["fault"] == "1": npost += 1; mpost += ok
            else: npre += 1; mpre += ok
        w.writerow([tag, fault, sev, rep, n, nm, round(nm / n, 3) if n else "", npre, round(mpre / npre, 3) if npre else "", npost, round(mpost / npost, 3) if npost else ""]); fh.flush()
        print(tag, n, nm, round(nm / n, 3) if n else None, "post", npost, round(mpost / npost, 3) if npost else None, flush=True)
    except Exception as e:
        print(tag, "ERR", e, flush=True)
