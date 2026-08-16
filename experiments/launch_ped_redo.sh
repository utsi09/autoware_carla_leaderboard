#!/bin/bash
# v4.9b 보행자 파트 재실험 (0815: 1차 스폰이 가드레일 바깥 → 허수아비 실측).
# 수정: 도로 waypoint 차선 우측 끝 스폰 — 횡단 보장. 24케이스 (~2h).
# 엣지 배터리(EDGE_BATTERY_DONE) 종료 후 실행.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
LOG=experiments/results/ped_redo.log
for F in "nf mid" "cn mid" "lso mid" "lso high"; do
  set -- $F
  echo "===== PED-REDO $1 $2 ====="
  HAZARD="ped=5:22:3" python3 experiments/experiment_runner.py \
    --method ours --fault $1 --sev $2 --npc none --reps 3 >> $LOG 2>&1
  HAZARD="ped=5:22:3" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault $1 --sev $2 --npc none --reps 3 >> $LOG 2>&1
done
# [v4.9c 사용자 설계] 갓길 점유 전면 재실험 — 고정 좌표는 조우 미보장
# (0815 실측: gn 케이스가 막힌 갓길 안 거치고 동쪽으로 감). shoulder=auto:
# 슈퍼바이저가 고른 갓길에 즉시 블로커 스폰 -> 전 케이스 조우 보장.
for F in "cn mid" "cf mid" "gn mid" "lso high"; do
  set -- $F
  echo "===== SHOULDER-AUTO $1 $2 ====="
  HAZARD="shoulder=auto" python3 experiments/experiment_runner.py \
    --method ours --fault $1 --sev $2 --npc none --reps 3 >> $LOG 2>&1
done
echo PED_REDO_DONE
