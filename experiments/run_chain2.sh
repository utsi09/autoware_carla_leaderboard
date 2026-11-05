#!/usr/bin/env bash
# 체인 2단계 (2026-11-05 14:40 교체): 순정 none 블록이 끝나면(agg 첫 셀 시작 감지) 매트릭스를 멈추고
#   조우 블록 A(80, 보행자 주입기 수정판) → 순정 agg(+빠진 셀) → 항법 확장 315 → "ALL BLOCKS DONE"(after_chain.sh 가 스윕 재실행)
#   사용: nohup experiments/run_chain2.sh > experiments/results/run_chain2.log 2>&1 &
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
say() { echo "$(date '+%F %T') chain: $*" | tee -a $LOG; }
until grep -q "npc=agg" $LOG; do sleep 30; done
say "none block finished — stopping stock_matrix.sh for the encounter block"
pkill -f "^bash experiments/stock_matrix.sh" 2>/dev/null; pkill -f "^/bin/bash experiments/stock_matrix.sh" 2>/dev/null
pkill -f "^bash experiments/stock_case_video.sh" 2>/dev/null
pkill -INT -f "^python3 -u experiments/experiment_runner" 2>/dev/null
for i in $(seq 1 60); do pgrep -f "^python3 -u experiments/experiment_runner" >/dev/null || break; sleep 2; done
pkill -9 -f "^python3 -u experiments/experiment_runner" 2>/dev/null; pkill -f "^ffmpeg .*x11grab" 2>/dev/null; pkill -9 -f "^ros2 bag record" 2>/dev/null
sleep 10
say "starting encounter_block (80, stock vs ours)"
bash experiments/encounter_block.sh
say "encounter block finished — resuming stock_matrix (agg + missing cells)"
bash experiments/stock_matrix.sh
say "starting stock_navext (315)"
bash experiments/stock_navext.sh
say "ALL BLOCKS DONE"
