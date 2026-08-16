#!/usr/bin/env python3
"""절제 v3 최종 집계 v2: 로그의 '블록 -> CSV 경로' 직접 매핑 + 원장 귀속."""
import csv, os, re
R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
pairs = []  # (seed, arm, csvpath)
cur = None
for line in open(f"{R}/ablation_v3.log", errors="ignore"):
    m = re.match(r"===== (S\d+R?) (A\d) ", line)
    if m:
        cur = [m.group(1), m.group(2), None]
        pairs.append(cur)
        continue
    m2 = re.search(r"\[runner\] 1 cases -> (\S+\.csv)", line)
    if m2 and cur is not None and cur[2] is None:
        cur[2] = m2.group(1)
hits = [float(l.split()[0]) for l in open(f"{R}/collision_live.log") if "walker" in l]
rows = []
for seed, arm, path in pairs:
    if not path or not os.path.exists(path):
        rows.append({"seed": seed, "arm": arm, "runner_label": "MISSING",
                     "walker_hits": 0, "verdict": "NO_DATA"}); continue
    with open(path) as f:
        rr = list(csv.DictReader(f))
    label = rr[0]["outcome"] if rr else "NO_ROW"
    end = os.path.getmtime(path)
    start = end - 700
    ch = [h for h in hits if start < h <= end + 5]
    v = ("SIM_FAIL" if label in ("CARLA_DIED", "SETUP_FAIL") else
         "COLLISION" if ch else "AVOID")
    rows.append({"seed": seed, "arm": arm, "runner_label": label,
                 "walker_hits": len(ch), "verdict": v})
w = csv.DictWriter(open(f"{R}/ablation_final_table.csv", "w"),
                   fieldnames=["seed","arm","runner_label","walker_hits","verdict"])
w.writeheader(); w.writerows(rows)
for r in rows:
    print(f"{r['seed']:5s} {r['arm']} {r['verdict']:9s} hits={r['walker_hits']:2d} {r['runner_label']}")
