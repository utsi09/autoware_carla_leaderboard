#!/bin/bash
# v3 2-arm 체인: B(주차 arm, 갓길 없는 구간) -> A(본 배터리, 갓길 구간)
# B: 주행가능 고장(gn/ln/cn/imn x2sev + nf) x npc{none,def,agg} x 5reps x both = 270케이스
# A: 전체 매트릭스 990케이스 (15 reps)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for f in gn ln cn imn nf; do
  python3 experiments/experiment_runner.py --method both --fault $f --reps 5 --no-shoulder \
    >> experiments/results/v3_armB_parking.log 2>&1
done
python3 experiments/experiment_runner.py --method both \
  > experiments/results/v3_armA_main.log 2>&1
