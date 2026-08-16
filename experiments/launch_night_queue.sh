#!/bin/bash
# 무정지 큐 (0816 사용자 지시): 사다리(순정 nf) 종료 후 — 실명 사다리 -> gm 검증
# [사용자 지시 8/16] 8m 경계 MRM 비교가 최우선 — 실명 사다리보다 먼저 실행
bash /home/taewook/autoware_carla_leaderboard/experiments/launch_mrm_boundary.sh
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE
LOG=experiments/results/night_queue.log
# 1) 실명(오염-심함) 거리 사다리
for D in 14 11 8 6 5; do
  echo "===== BLIND-LADDER D=${D}m ====="
  HAZARD="ped=dist:$D" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault lso --sev high --npc none --reps 2 >> $LOG 2>&1
done
# 2) gm 폴트 첫 검증 (EXTRA — 코드 인 but 미실행)
for SV in mid high; do
  echo "===== GM-VERIFY $SV ====="
  python3 experiments/experiment_runner.py \
    --method ours --fault gm --sev $SV --npc none --reps 2 >> $LOG 2>&1
done
echo NIGHT_QUEUE_DONE
