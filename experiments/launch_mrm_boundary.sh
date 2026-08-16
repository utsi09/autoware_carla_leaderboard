#!/bin/bash
# v4.9t 8m 경계 x MRM 대규모 비교 (사용자 설계):
# 카메라 완전고장(cf-high, 라이다 정상 -> 보행자 감지력 동일 조건) 상태에서
# MRM 이동 중 8m 앞 무단횡단. arm 옵션: 고장+8s 후에만 발사.
#  A) ours + 저속 MRM (scaled cap ~3.0 m/s), 게이트 2.0  x10
#  B) 순정 관찰 (mrm-off, 4.2 m/s 유지)              x10
#  C) ours + 고정 cap 4.2 (속도만 다름 -> 인과 분리)   x5
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/mrm_boundary.log
echo "===== ARM A: ours scaled-cap 8m x10 ====="
MRM_CAP_MODE=scaled HAZARD="ped=dist:8:2.0:arm" \
  python3 experiments/experiment_runner.py \
  --method ours --fault cf --sev mid --npc none --reps 10 >> $LOG 2>&1
unset MRM_CAP_MODE
echo "===== ARM B: stock-observe 8m x10 ====="
HAZARD="ped=dist:8:2.0:arm" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault cf --sev mid --npc none --reps 10 >> $LOG 2>&1
echo "===== ARM C: ours fixed-cap-4.2 8m x5 ====="
HAZARD="ped=dist:8:2.0:arm" python3 experiments/experiment_runner.py \
  --method ours --fault cf --sev mid --npc none --reps 5 >> $LOG 2>&1
echo MRM_BOUNDARY_DONE
