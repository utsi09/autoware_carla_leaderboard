#!/usr/bin/env bash
# 11/8 저녁 완료 루트 (2026-11-04 결정). 분석에 먼저 필요한 블록부터:
#   순정 def(진행 중) → 스윕 경량판 48 → 조우 A 80 → 순정 none·agg(+실패 셀 재실행) → 항법 확장 315
# 순정 def 195셀이 다 끝나는 순간 stock_matrix.sh 를 멈추고(막 시작한 none 셀 하나는 나중에 재실행) 순서를 바꾼다.
#   사용: nohup experiments/run_chain.sh > experiments/results/run_chain.log 2>&1 &
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
DONE=experiments/results/stock_done.txt
say() { echo "$(date '+%F %T') chain: $*" | tee -a $LOG; }
# 1) def 블록 끝 대기: 195 def 셀이 다 되거나, 매트릭스가 none 셀을 시작하면(실패 셀이 빠져 195 미만이어도) 끝난 것
COND=("cf mid" "cn mid" "cn high" "gn mid" "gn high" "lso mid" "lso high" "lcl mid" "lcl high" "imn mid" "imn high" "lf mid" "nf mid")
until grep -q "npc=none" $LOG || [ "$(grep -c " def [0-9]*$" $DONE)" -ge 195 ]; do sleep 30; done
say "def block finished ($(grep -c " def [0-9]*$" $DONE)/195 done) — stopping stock_matrix.sh to reorder"
pkill -f "^bash experiments/stock_matrix.sh" 2>/dev/null; pkill -f "^/bin/bash experiments/stock_matrix.sh" 2>/dev/null
pkill -f "^bash experiments/stock_case_video.sh" 2>/dev/null; pkill -f "^/bin/bash experiments/stock_case_video.sh" 2>/dev/null
pkill -INT -f "^python3 -u experiments/experiment_runner" 2>/dev/null
for i in $(seq 1 60); do pgrep -f "^python3 -u experiments/experiment_runner" >/dev/null || break; sleep 2; done
pkill -9 -f "^python3 -u experiments/experiment_runner" 2>/dev/null; pkill -f "x11grab" 2>/dev/null; pkill -9 -f "ros2 bag record" 2>/dev/null
sleep 10
# 1b) def 블록에서 빠진 셀(CARLA_DIED 등) 재실행 — 분석에 def 195 가 먼저 필요
for rep in $(seq 0 14); do
  for c in "${COND[@]}"; do
    set -- $c; f=$1; s=$2
    grep -qx "$f $s def $rep" $DONE && continue
    say "rerun missing def cell: $f $s rep$rep"
    experiments/stock_case_video.sh "$f" "$s" def "$rep" 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback" | tee -a $LOG
    echo "$f $s def $rep" >> $DONE
  done
done
# 2) 스윕 경량판
say "starting noise_sweep_lite (48)"
bash experiments/noise_sweep_lite.sh
say "sweep-lite finished"
# 3) 조우 블록 A (순정 vs 제안, 80)
say "starting encounter_block (80)"
bash experiments/encounter_block.sh
say "encounter block finished"
# 4) 순정 none → agg (+ def 의 실패 셀 재실행)
say "resuming stock_matrix (none, agg, failed def cells)"
bash experiments/stock_matrix.sh
# 5) 항법 확장
say "starting stock_navext (315)"
bash experiments/stock_navext.sh
say "ALL BLOCKS DONE"
