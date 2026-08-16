#!/bin/bash
# [옵션 보강] 3.0 m/s 순항 사다리 — 경계 이동 증명용 (전문가 제안).
# 4.2 사다리의 대응 실험: 저속 MRM 순항(재출발 후) 조우, D={7,6,5}m x2.
# (8m은 재실험 A팔 n=8 회피로 이미 확보. 예측: 7m 회피 / 6m 경계 / 5m 충돌)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE
LOG=experiments/results/lowspeed_ladder.log
for D in 7 6 5; do
  echo "===== LOWSPEED-LADDER D=${D}m ====="
  MRM_MOVE_SPEED=3.0 HAZARD="ped=dist:${D}:2.6:arm" \
    python3 experiments/experiment_runner.py \
    --method ours --fault gn --sev mid --npc none --reps 2 >> $LOG 2>&1
done
echo LOWSPEED_LADDER_DONE
