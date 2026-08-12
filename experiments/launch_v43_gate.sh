#!/bin/bash
# v4.3 게이트 블록: gn-mid ours 15 (npc3 x 5reps, --no-shoulder)
# 통과 기준(별도 판정): 주차 전환 후 성공률 >= 90% (d<=1.2m 게이트 기준)
# 게이트는 여기서 멈춘다 — Arm A 는 판정 후 launch_v43_armA.sh 로.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
python3 experiments/experiment_runner.py --method ours --fault gn --sev mid --reps 5 --no-shoulder \
  >> experiments/results/v43_gate.log 2>&1
echo GATE_BLOCK_DONE
