#!/usr/bin/env bash
# [2026-11-09] 세기 사다리 고르게 채우기 (B안: 단계당 10런). 사용자 결정 15:35 "B 권장안으로 먼저".
# 순정 러너(--mrm-off, 제안 점수 기록, def 교통). mid/high 운용점은 순정 매트릭스 45런 재사용 → 제외(단, lcl 은 v5b q 가 필요해 5·25 도 채움).
#   lso 0.6 0.45 0.25 0.2 0.15 0.12 0.07 (:90)  rep 3-9   = 49   (기존 rep 0-2)
#   lcl 1 2 5 10 15 25 40                       rep 44-49 = 42   (기존 rep 40-43, CDR_LCL_SEV_CFG 켜고)
#   imn 0.05 0.1 0.25 1.0                       rep 3-9   = 28
#   cn  5 10 20 45                              rep 3-9   = 28   → 합계 147, ≈12 h
# rep 우선(모든 단계 rep k → k+1) 순서라 중간에 끊겨도 단계별 런 수가 고르다. 완료 목록 results/ladder_fill_done.txt
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LOG=experiments/results/noise_sweep_batch.log; LOG2=experiments/results/stock_matrix.log
DONE=experiments/results/ladder_fill_done.txt; touch $DONE
LCL_CFG=$(realpath experiments/results/retune_ext/lcl_sev_cfg.txt)
echo "$(date '+%F %T') chain: ladder fill B start (147 cells)" | tee -a $LOG $LOG2
run_cell () {  # fault value rep
  local f=$1 v=$2 rep=$3 key="$1 $2 $3"
  grep -qx "$key" $DONE && return 0
  [ -f experiments/results/DISK_FULL ] && { echo "$(date '+%F %T') DISK_FULL — stop" | tee -a $LOG $LOG2; exit 1; }
  echo "$(date '+%F %T') fill $f $v rep=$rep free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG $LOG2
  local OUT
  if [ "$f" = lcl ]; then OUT=$(CDR_LCL_SEV_CFG=$LCL_CFG $R --fault lcl --sev-value "$v" --rep "$rep" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback")
  else OUT=$($R --fault "$f" --sev-value "$v" --rep "$rep" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback"); fi
  echo "$OUT" | tee -a $LOG $LOG2
  if echo "$OUT" | grep -qE "CARLA_DIED|INTERRUPTED|SETUP_FAIL|Traceback" || [ -z "$OUT" ]; then return 0; fi
  echo "$key" >> $DONE
}
for pass in 1 2; do
  for k in 0 1 2 3 4 5 6; do
    for v in 1:1000 2:1100 5:1500 10:2100 15:2750 25:4000 40:5900; do run_cell lcl $v $((44 + k)); done
    for v in 5 10 20 45; do run_cell cn $v $((3 + k)); done
    for v in 0.6:90 0.45:90 0.25:90 0.2:90 0.15:90 0.12:90 0.07:90; do run_cell lso $v $((3 + k)); done
    for v in 0.05 0.1 0.25 1.0; do run_cell imn $v $((3 + k)); done
  done
done
echo "$(date '+%F %T') chain: ladder fill B done ($(wc -l < $DONE)/147)" | tee -a $LOG $LOG2
