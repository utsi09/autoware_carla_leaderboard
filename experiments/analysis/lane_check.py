#!/usr/bin/env python3
"""정지 위치가 자기 차로인지 판정: GT(ego) 최종 위치 ↔ 무고장 기준 궤적(같은 교통의 stock-nf-mid-<npc> GT) 최근접 거리.
사용: lane_check.py <gt.csv> [npc]  → 'offset=<m> verdict=<in_lane|off_lane>'  (문턱 1.2 m; 차로폭 3.5 m, 반대 차로 중심 ≈ 3.5 m)"""
import sys, csv, glob, numpy as np
RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"
def ego_xy(path):
    pts = [(float(r["x"]), float(r["y"]), float(r.get("speed") or 0)) for r in csv.DictReader(open(path)) if r.get("kind") == "ego"]
    return np.array(pts)
gt = sys.argv[1]; npc = sys.argv[2] if len(sys.argv) > 2 else "agg"
ref = np.concatenate([ego_xy(p)[:, :2] for p in sorted(glob.glob(f"{RES}/gt/stock-nf-mid-{npc}-*.csv")) if not p.endswith("_tl.csv")])
e = ego_xy(gt); final = e[-1, :2]
d = np.sqrt(((ref - final) ** 2).sum(1)).min()
print(f"offset={d:.2f} verdict={'in_lane' if d < 1.2 else 'off_lane'} final=({final[0]:.1f},{final[1]:.1f}) ref_pts={len(ref)}")
