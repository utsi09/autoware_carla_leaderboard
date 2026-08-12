#!/bin/bash
# v4.5 검증: 게이트 실패 재현 3케이스 (셀렉터 8m 거리판정 + 1003003 폴리곤 확장 픽스 검증)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for args in "--t 40 --npc def" "--t 23 --npc def" "--t 40 --npc agg"; do
  python3 experiments/experiment_runner.py --method ours --fault gn --sev mid $args --reps 1 --no-shoulder \
    >> experiments/results/v45_verify.log 2>&1
done
echo V45_VERIFY_DONE
