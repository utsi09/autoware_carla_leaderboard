#!/usr/bin/env python3
"""[2026-11-07] 완료 목록(stock_done.txt, encounter_done.txt)에서 '마지막 실행 결과가 CARLA_DIED/INTERRUPTED/DRY' 인 셀을 지운다.
블록 스크립트는 결과와 무관하게 done 에 적으므로, 재실행 전에 이걸 한 번 돌려야 실패 셀이 다시 돈다."""
import re
R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
FAIL = ("CARLA_DIED", "INTERRUPTED", "DRY")
def last_results(log, pat, key):
    last = {}; cur = None
    for ln in open(log, errors="replace"):
        m = re.match(pat, ln)
        if m: cur = key(m); continue
        m = re.match(r"VIDEO .*result=(\w+)", ln)
        if m and cur: last[cur] = m[1]; cur = None
    return last
def prune(done_file, last):
    lines = [l.strip() for l in open(done_file) if l.strip()]
    bad = [l for l in lines if last.get(l) in FAIL]
    if bad:
        open(done_file, "w").write("\n".join(l for l in lines if l not in bad) + "\n")
    print(f"{done_file}: removed {len(bad)} {bad}")
import csv
# 순정: 로그상 마지막이 실패여도 stock_outcomes.csv 에 유효한(judge 가 실패 아님) 행이 있으면 다른 경로로 재실행된 것 → 유지 (11/05 def 재실행 5건)
stock_last = last_results(f"{R}/stock_matrix.log",
      r"\S+ \S+ stock (\w+)-(\w+) npc=(\w+) rep=(\d+)", lambda m: f"{m[1]} {m[2]} {m[3]} {m[4]}")
for r in csv.DictReader(open(f"{R}/stock_outcomes.csv")):
    k = f"{r['fault']} {r['sev']} {r['npc']} {r['rep']}"
    if r.get("judge") and r["judge"] not in FAIL and stock_last.get(k) in FAIL: stock_last[k] = r["judge"]
# [2026-11-08] 출발 직후 Autoware 비상정지(MRM state 3)에서 못 풀려 차가 한 번도 안 움직이고 고장 타이머도 안 걸린 채
#   SCENARIO_ENDED 로 끝난 셀(11/06 nf-mid-agg-r4, 11/08 gb-mid-agg-r2)은 결과가 아니라 하네스 실패 → 다시 돌린다.
#   판정: 셀의 마지막 실행 로그(run_stock-<f>-<s>-<npc>-r<rep>.log, 재실행 때 덮어씀)의 hazard watch 줄이 2개 이상이고 전부 'speed=0.0 fault=no'.
#   (CSV 보정 뒤에 적용해야 stock_outcomes.csv 의 SCENARIO_ENDED 행이 이 셀을 되살리지 않는다)
import os
def never_moved(k):
    f, s, n, rep = k.split()
    p = f"{R}/run_stock-{f}-{s}-{n}-r{rep}.log"
    if not os.path.exists(p): return False
    w = [l for l in open(p, errors="replace") if "hazard watch" in l]
    return len(w) >= 2 and all("speed=0.0 fault=no" in l for l in w)
for k in [l.strip() for l in open(f"{R}/stock_done.txt") if l.strip()]:
    if stock_last.get(k) not in FAIL and never_moved(k): stock_last[k] = "NEVER_MOVED"
FAIL = FAIL + ("NEVER_MOVED",)
prune(f"{R}/stock_done.txt", stock_last)
prune(f"{R}/encounter_done.txt", last_results(f"{R}/encounter_block.log",
      r"\S+ \S+ enc-(\w+)-(\w+)-(\S+)-r(\d+)", lambda m: f"{m[2]} {m[3].replace('_', ':')} {m[1]} {m[4]}"))
