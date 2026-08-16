#!/bin/bash
# v4.9e 보행자 최종판: 충돌 코스 보장(에고 속도 연동 스폰) — 이전 보행자
# 데이터 전량 대체. 24케이스 (~2h). 현 배터리(PED_REDO_DONE) 후 실행.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
LOG=experiments/results/ped_final.log
for F in "nf mid" "cn mid" "lso mid" "lso high"; do
  set -- $F
  echo "===== PED-FINAL $1 $2 ====="
  HAZARD="ped=fixed" python3 experiments/experiment_runner.py \
    --method ours --fault $1 --sev $2 --npc none --reps 3 >> $LOG 2>&1
  HAZARD="ped=fixed" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault $1 --sev $2 --npc none --reps 3 >> $LOG 2>&1
done
echo PED_FINAL_DONE
