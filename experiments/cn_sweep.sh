#!/usr/bin/env bash
# [2026-11-09] 카메라 잡음(cn) 세기 사다리 — 사용자 지시 "cn 지금 당장". 순정 러너(--mrm-off, 제안 방식 점수 기록), def 교통.
# 수준: σ 5·10·20·45 (mid 15·high 30 은 순정 매트릭스 45런씩이 있음) × rep 0-2 = 12런 ≈ 1 h. 완료 목록 results/cn_sweep_done.txt.
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LOG=experiments/results/noise_sweep_batch.log; LOG2=experiments/results/stock_matrix.log
DONE=experiments/results/cn_sweep_done.txt; touch $DONE
echo "$(date '+%F %T') chain: cn sweep start (12 cells: sigma 5 10 20 45 x rep 0-2)" | tee -a $LOG $LOG2
for pass in 1 2; do
  for v in 5 10 20 45; do for rep in 0 1 2; do
    grep -qx "$v $rep" $DONE && continue
    [ -f experiments/results/DISK_FULL ] && { echo "$(date '+%F %T') DISK_FULL — stop" | tee -a $LOG $LOG2; exit 1; }
    echo "$(date '+%F %T') cnsweep cn $v rep=$rep free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG $LOG2
    OUT=$($R --fault cn --sev-value "$v" --rep "$rep" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback")
    echo "$OUT" | tee -a $LOG $LOG2
    if echo "$OUT" | grep -qE "CARLA_DIED|INTERRUPTED|SETUP_FAIL|Traceback" || [ -z "$OUT" ]; then continue; fi
    echo "$v $rep" >> $DONE
  done; done
done
echo "$(date '+%F %T') chain: cn sweep done ($(wc -l < $DONE)/12)" | tee -a $LOG $LOG2
