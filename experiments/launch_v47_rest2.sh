#!/bin/bash
# v4.7 잔여 체인 2: DEST_XY 컴파일 사고로 lso 이후가 전소된 뒤 재개.
# 완료: cn(구agg, 재수집 예정) / imn / gn. 여기서: lso -> lcl -> cf -> lf -> nf
# -> Arm C -> cn 재수집(신 agg). ROUTE_COMPLETE_NEAR 판정 포함(v4.7).
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for f in lso lcl cf lf nf; do
  echo "===== BLOCK $f ====="
  python3 experiments/experiment_runner.py --method both --fault $f \
    >> experiments/results/v46_rest.log 2>&1
done
bash experiments/launch_v3_armC.sh >> experiments/results/v46_armC.log 2>&1
echo "===== BLOCK cn-rerun ====="
python3 experiments/experiment_runner.py --method both --fault cn \
  >> experiments/results/v46_rest.log 2>&1
echo V47_REST2_DONE
