#!/bin/bash
# v4.9m 강도 스윕 (사용자 설계): TTC {2.5,2.0,1.6,1.2} x {순정, 우리-고정캡,
# 우리-비례캡} x {nf, lso high} x 2reps = 48케이스 (~4h). 그래프: 강도 vs
# 최소간격/충돌률 선 3개. 현 배터리 종료 후 실행.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/ttc_sweep.log
for TTC in 2.5 2.0 1.6 1.2; do
  for F in "nf mid" "lso high"; do
    set -- $F
    echo "===== SWEEP ttc=$TTC $1 $2 ====="
    HAZARD="ped=fixed:$TTC" python3 experiments/experiment_runner.py \
      --method ours --mrm-off --fault $1 --sev $2 --npc none --reps 2 >> $LOG 2>&1
    HAZARD="ped=fixed:$TTC" python3 experiments/experiment_runner.py \
      --method ours --fault $1 --sev $2 --npc none --reps 2 >> $LOG 2>&1
    HAZARD="ped=fixed:$TTC" MRM_CAP_MODE=scaled python3 experiments/experiment_runner.py \
      --method ours --fault $1 --sev $2 --npc none --reps 2 >> $LOG 2>&1
  done
done
echo TTC_SWEEP_DONE
