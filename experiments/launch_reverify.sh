#!/bin/bash
# [0816 사용자 적발] '회피' 오판 3케이스 재검증 — 물리 오라클+워치독 탑재판.
# gn 사다리식 8m x2, gn 6m x2 — 접촉이면 CONTACT-PHYSICS가 찍힌다.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE MRM_MOVE_SPEED
LOG=experiments/results/reverify.log
echo "===== REVERIFY gn 8m x2 ====="
HAZARD="ped=dist:8" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault gn --sev mid --npc none --reps 2 >> $LOG 2>&1
echo "===== REVERIFY gn 6m x2 ====="
HAZARD="ped=dist:6" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault gn --sev mid --npc none --reps 2 >> $LOG 2>&1
echo REVERIFY_DONE
# [추가] A팔(저속 MRM) 재검증 x4 — 물리 오라클+에고 실시간 원장 기준
echo "===== REVERIFY ours slow-MRM 8m x4 ====="
MRM_MOVE_SPEED=3.0 HAZARD="ped=dist:8:2.6:arm" \
  python3 experiments/experiment_runner.py \
  --method ours --fault gn --sev mid --npc none --reps 4 >> $LOG 2>&1
echo REVERIFY_ALL_DONE
