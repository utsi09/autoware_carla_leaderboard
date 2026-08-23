#!/bin/bash
# v6 lf 인계 (cron 멱등): cf 러너 종료 후 lf 배치 1회 발사, 완료 시 자기 제거
LOG=/home/taewook/autoware_carla_leaderboard/experiments/results/hardfast_full6_0822.log
if grep -q "hardfast full6 done" "$LOG" 2>/dev/null; then
  crontab -l 2>/dev/null | grep -v lf_handover_cron > /tmp/ct.$$ && crontab /tmp/ct.$$; rm -f /tmp/ct.$$
  exit 0
fi
pgrep -f "experiment_runner.py --fault cf" > /dev/null && exit 0   # cf 진행 중
grep -q "full: lf" "$LOG" 2>/dev/null && exit 0                     # lf 이미 시작
pgrep -f "experiment_runner.py --fault lf" > /dev/null && exit 0
cd /home/taewook/autoware_carla_leaderboard/experiments
# cron 환경엔 ROS가 없음 — 러너(judge rclpy) 구동에 필요한 최소 환경 구성
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
export ROS_DOMAIN_ID=0
echo "--- full: lf $(date +%m%d_%H:%M) (cron 인계) ---" >> "$LOG"
SUP_HARD_FAST=1 PYTHONUNBUFFERED=1 python3 experiment_runner.py --fault lf --method both --reps 15 >> "$LOG" 2>&1
echo "=== hardfast full6 done $(date +%m%d_%H:%M) ===" >> "$LOG"
