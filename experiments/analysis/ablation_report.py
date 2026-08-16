#!/usr/bin/env python3
"""절제 v3 결과 집계: 시드×팔 판정(원장 시간창 귀속) + E_H + T_clear + 표.

사용: python3 ablation_report.py   (캠페인 완료 후)
판정: collision_live.log의 walker RAW-HIT를 케이스 시간창(ablation_v3.log의
블록 시각)에 귀속. E_H = t_detect 후 H=20s 동안 틱 CSV 속도 적분.
T_clear = footprint가 주행차선 이탈한 시각 - t_detect (틱 CSV의 에고 좌표
+ 차선폭 기반 근사; 미이탈 = censored).
"""
import csv, glob, os, re, subprocess
R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
H = 20.0

# 1) 케이스 시간창: ablation_v3.log 라인 mtime 대신 블록 순서 + results CSV 시각
blocks = []   # (seed, arm, start_epoch)
for line in open(f"{R}/ablation_v3.log", errors="ignore"):
    m = re.match(r"===== (S\d+) (A\d) ", line)
    if m:
        blocks.append([m.group(1), m.group(2), None, None])  # start/end 미정

# 2) 원장: walker RAW-HIT 시각 목록
hits = []
if os.path.exists(f"{R}/collision_live.log"):
    for line in open(f"{R}/collision_live.log"):
        p = line.split()
        if len(p) >= 3 and "walker" in line:
            hits.append(float(p[0]))

# 3) 틱 CSV: 케이스명(tick_<tag>_<epoch>.csv) — epoch로 블록 매칭
ticks = sorted(glob.glob(f"{R}/tick_*.csv"),
               key=lambda p: int(p.rsplit("_", 1)[1][:-4]))
print(f"blocks={len(blocks)} hits={len(hits)} ticks={len(ticks)}")
print("블록·틱·원장 시간 귀속은 캠페인 완료 후 CSV 시각으로 마감한다.")
# (완료 후: 각 팔 runner CSV의 파일시각으로 창 확정 -> hit 귀속 ->
#  E_H = sum(v*dt) over sim_t in [t_fire-3, +H] from tick csv ->
#  T_clear = 첫 |ego_y - lane_center| > lane_half + half_width 시각)
