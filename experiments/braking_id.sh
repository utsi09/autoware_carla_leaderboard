#!/bin/bash
# 제동 파라미터 동정(0826, 심사 반영): 무고장 순정 4.2 순항 + 14 m 스폰 5런.
# 회피 케이스의 v(t) 틱 로그에서 tau(반응 지연)·a(감속도)를 사다리와 독립으로 추정.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE MRM_MOVE_SPEED
HAZARD="ped=dist:14" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault nf --npc none --reps 5 \
  >> experiments/results/braking_id.log 2>&1
echo BRAKING_ID_DONE
grep -oE 'result: [A-Z_]+' experiments/results/braking_id.log | tail -5
ls -t experiments/results/tick_*.csv | head -5
