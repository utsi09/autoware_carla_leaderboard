#!/bin/bash
# v7 체인 (cron 멱등): lf 완료 → cf 재수집(원장 측정) → 전체 완료 마커 → 자기 제거
LOG=/home/taewook/autoware_carla_leaderboard/experiments/results/hardfast_v7_lf_0823.log
CFLOG=/home/taewook/autoware_carla_leaderboard/experiments/results/hardfast_v7_cf_0823.log
if grep -q "cf v7 done" "$CFLOG" 2>/dev/null; then
  crontab -l | grep -v v7_chain_cron | crontab -; exit 0
fi
pgrep -f "experiment_runner.py --fault" > /dev/null && exit 0   # 뭔가 진행 중
if ! grep -q "lf v7 done" "$LOG" 2>/dev/null; then
  echo "=== lf v7 done $(date +%m%d_%H:%M) (cron) ===" >> "$LOG"; exit 0
fi
grep -q "cf v7 start" "$CFLOG" 2>/dev/null && exit 0
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
export ROS_DOMAIN_ID=0
cd /home/taewook/autoware_carla_leaderboard/experiments
echo "=== cf v7 start $(date +%m%d_%H:%M) ===" > "$CFLOG"
SUP_HARD_FAST=1 PYTHONUNBUFFERED=1 python3 experiment_runner.py --fault cf --method both --reps 15 >> "$CFLOG" 2>&1
echo "=== cf v7 done $(date +%m%d_%H:%M) ===" >> "$CFLOG"
