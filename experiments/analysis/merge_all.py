#!/usr/bin/env python3
"""캠페인 전 CSV 병합 + 재분류 (v4.8 이후 최종본 기준).

블록별 최신 유효 CSV만 채택, 재시도 성공분으로 CARLA_DIED/SETUP_FAIL 행 대체,
목적지 30m 내 NORMAL 스톨 -> ROUTE_COMPLETE_NEAR 재분류.
출력: merged_final.csv + 블록별 요약 stdout.
"""
import csv, glob, math, os

R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
DEST = (-102.0, 95.0)

# 블록 -> 채택 CSV (v4.8 재실험이 cn/cf/gn 구본 대체)
BLOCKS = {
    "cf":  f"{R}/results_0814_1509.csv",
    "cn":  f"{R}/results_0814_1833.csv",
    "gn":  f"{R}/results_0815_0102.csv",
    "lso": f"{R}/results_0813_0444.csv",
    "lcl": f"{R}/results_0813_1513.csv",   # +보충 2건 별도
    "imn": f"{R}/results_0812_1523.csv",
    "lf":  f"{R}/results_0814_0034.csv",
    "nf":  f"{R}/results_0814_0343.csv",
}

def reclass(row):
    if row["outcome"] in ("STUCK_AT_JUNCTION", "SCENARIO_ENDED"):
        try:
            d = math.dist((float(row["stop_x"]), float(row["stop_y"])), DEST)
            if d <= 30.0:
                row["outcome"] = "ROUTE_COMPLETE_NEAR"
        except (ValueError, KeyError):
            pass
    return row

rows = []
for blk, path in BLOCKS.items():
    if not os.path.exists(path):
        print(f"!! missing {blk}: {path}")
        continue
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row["block"] = blk
            rows.append(reclass(dict(row)))

# 재시도 CSV들(retry 체인 산출)로 실패 행 대체
retry_rows = {}
for p in sorted(glob.glob(f"{R}/results_0816_0[0-3]*.csv")):
    with open(p, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["fault"], row["severity"], row["npc"], row["rep"], row["method"])
            if row["outcome"] not in ("CARLA_DIED", "SETUP_FAIL"):
                retry_rows[key] = row

replaced = 0
for r in rows:
    if r["outcome"] in ("CARLA_DIED", "SETUP_FAIL"):
        key = (r["fault"], r["severity"], r["npc"], r["rep"], r["method"])
        if key in retry_rows:
            new = dict(retry_rows[key]); new["block"] = r["block"]
            r.update(reclass(new)); replaced += 1

with open(f"{R}/merged_final.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print(f"merged {len(rows)} rows, retry-replaced {replaced}")
from collections import Counter
for blk in BLOCKS:
    c = Counter((r["method"], r["outcome"]) for r in rows if r["block"] == blk)
    print(f"\n[{blk}]")
    for (m, o), n in sorted(c.items()):
        print(f"  {m:9s} {o:28s} {n}")
