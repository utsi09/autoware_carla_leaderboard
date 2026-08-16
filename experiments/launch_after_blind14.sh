#!/bin/bash
# 재체인: (1) 8m 경계 MRM 비교 25케이스 -> (2) 실명 사다리 나머지 {11,8,6,5}
# -> (3) gm 검증. 실명 14m은 지금 도는 러너가 마무리.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
bash experiments/launch_mrm_boundary.sh
unset MRM_FORCE_TARGET MRM_CAP_MODE
LOG=experiments/results/night_queue.log
for D in 11 8 6 5; do
  echo "===== BLIND-LADDER D=${D}m ====="
  HAZARD="ped=dist:$D" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault lso --sev high --npc none --reps 2 >> $LOG 2>&1
done
for SEV in mid high; do
  echo "===== GM-VERIFY sev=$SEV ====="
  python3 experiments/experiment_runner.py \
    --method ours --fault gm --sev $SEV --npc none --reps 2 >> $LOG 2>&1
done
echo NIGHT_RECHAIN_DONE
