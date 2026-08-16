#!/bin/bash
# v4.7 잔여 체인 3: 디스플레이 분리발 CARLA 부팅 세그폴트로 rest2 중단 후 재개
# (runner CARLA_LAUNCH에 -RenderOffScreen 적용됨).
# 완료: cn(구agg)/imn/gn/lso/lcl(141, 보충은 launch_lcl_completion.sh).
# 여기서: cf -> lf -> nf -> Arm C -> cn 재수집(신 agg).
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for f in cf lf nf; do
  echo "===== BLOCK $f ====="
  python3 experiments/experiment_runner.py --method both --fault $f \
    >> experiments/results/v46_rest.log 2>&1
done
bash experiments/launch_v3_armC.sh >> experiments/results/v46_armC.log 2>&1
echo "===== BLOCK cn-rerun ====="
python3 experiments/experiment_runner.py --method both --fault cn \
  >> experiments/results/v46_rest.log 2>&1
echo V47_REST3_DONE
