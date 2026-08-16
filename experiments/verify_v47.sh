#!/bin/bash
# v4.7 ZUPT 검증: 정지 중 자이로 영속도 감시
#  1) imn mid: 감지 정상 유지 (정지 구간 있으면 더 빨라질 수 있음) -> DEFER
#  2) nf     : 신호 대기 정지에서 오탐 없어야 함 (역사적 상수 목적지 스톨은 OK)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for f in "imn mid" "nf mid"; do
  set -- $f
  echo "=== VERIFY fault=$1 sev=$2 ==="
  timeout 900 python3 experiments/experiment_runner.py \
    --method ours --fault $1 --sev $2 --npc def --reps 1 --t 20 \
    >> experiments/results/v47_verify.log 2>&1
  tail -1 $(ls -t experiments/results/results_*.csv | head -1)
done
echo V47_VERIFY_DONE
