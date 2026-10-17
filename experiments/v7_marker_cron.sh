#!/bin/bash
# v7 완료 마커 (cron 멱등): lf 러너 종료 감지 시 마커 기록 후 자기 제거
LOG=/home/taewook/autoware_carla_leaderboard/experiments/results/hardfast_v7_lf_0823.log
grep -q "lf v7 done" "$LOG" 2>/dev/null && { crontab -l | grep -v v7_marker_cron | crontab -; exit 0; }
pgrep -f "experiment_runner.py --fault lf" > /dev/null && exit 0
echo "=== lf v7 done $(date +%m%d_%H:%M) (cron marker) ===" >> "$LOG"
