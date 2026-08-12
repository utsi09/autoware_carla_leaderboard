#!/bin/bash
# T_hazard 표본 보강: 경계 고장 3종 (imb-high, lf-mid, ln-high) 무개입 각 +5
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R="python3 experiments/experiment_runner.py"
echo "=== T_hazard 보강 시작 $(date +%T) ==="
$R --mrm-off --fault imb --sev high --npc agg --reps 5
$R --mrm-off --fault lf  --sev mid  --npc agg --reps 5
$R --mrm-off --fault ln  --sev high --npc agg --reps 5
echo "=== T_hazard 보강 완료 $(date +%T) ==="
