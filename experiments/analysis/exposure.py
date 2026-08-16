#!/usr/bin/env python3
"""노출 지표: 고장 상태 주행거리(deg_dist_m) — 방법별/블록별 평균·중앙값.
'위험이 등장했을 때 도로 위를 달리고 있을 확률'의 대리 지표."""
import csv, statistics as st
R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
rows = list(csv.DictReader(open(f"{R}/merged_final.csv")))
print(f"{'block':6s} {'method':9s} {'n':>4s} {'deg_dist 평균':>12s} {'중앙값':>8s}")
for blk in ["cf","cn","gn","lso","lcl","imn","lf","nf"]:
    for m in ["ours","baseline"]:
        vals = [float(r["deg_dist_m"]) for r in rows
                if r["block"]==blk and r["method"]==m and r.get("deg_dist_m","")]
        if vals:
            print(f"{blk:6s} {m:9s} {len(vals):4d} {st.mean(vals):11.1f}m {st.median(vals):7.1f}m")
# 순정(관찰) 프로브: results_0815_08*.csv
import glob
sv = []
for p in glob.glob(f"{R}/results_0815_0[89]*.csv"):
    for r in csv.DictReader(open(p)):
        if r.get("deg_dist_m",""):
            sv.append((r["fault"], float(r["deg_dist_m"])))
if sv:
    print("\n[순정 프로브 deg_dist]")
    from collections import defaultdict
    d = defaultdict(list)
    for f, v in sv: d[f].append(v)
    for f, vs in sorted(d.items()):
        print(f"  {f:5s} n={len(vs)} 평균 {st.mean(vs):.0f}m")
