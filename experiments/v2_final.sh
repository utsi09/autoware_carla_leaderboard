#!/bin/bash
# 이격 목적지 nf 검증 (교차로 40m 이전 직선 구간 목적지)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R="python3 experiments/experiment_runner.py"

echo "=== 이격 목적지 nf 검증 (10) $(date +%T) ==="
$R --fault nf --method ours --npc agg --reps 5 --dg=-147.8:75:90
$R --fault nf --method ours --npc def --reps 5 --dg=-147.8:75:90
echo "=== 최종 보강 완료 $(date +%T) ==="
