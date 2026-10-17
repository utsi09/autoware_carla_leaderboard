#!/bin/bash
# gb(GNSS 두절) v2 캠페인 (cron 멱등): 90케이스 동등 매트릭스, 완료 시 자기 제거.
# 침묵 감쇠 속도 게이트 제거판 감독자(a02dbe5+) — 최종 설계 구성(SUP_HARD_FAST=1).
LOG=/home/taewook/autoware_carla_leaderboard/experiments/results/gb_v2_0824.log
if grep -q "gb v2 done" "$LOG" 2>/dev/null; then
  crontab -l 2>/dev/null | grep -v gb_v2_cron > /tmp/ct.$$ && crontab /tmp/ct.$$; rm -f /tmp/ct.$$
  exit 0
fi
pgrep -f "experiment_runner.py" > /dev/null && exit 0          # 러너 이미 동작 중
STARTS=$(grep -c -- "--- gb v2 start" "$LOG" 2>/dev/null || echo 0)
[ "$STARTS" -ge 3 ] && exit 0                                   # 재시도 상한 (3회)
cd /home/taewook/autoware_carla_leaderboard/experiments
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
export ROS_DOMAIN_ID=0
echo "--- gb v2 start $(date +%m%d_%H:%M) (attempt $((STARTS+1))) ---" >> "$LOG"
SUP_HARD_FAST=1 PYTHONUNBUFFERED=1 python3 experiment_runner.py --fault gb --method both --reps 15 >> "$LOG" 2>&1
echo "=== gb v2 done $(date +%m%d_%H:%M) ===" >> "$LOG"
