#!/bin/bash
# v6 인계: cf 러너(PID $1) 종료 대기 → lf 배치 → 완료 마커
while kill -0 "$1" 2>/dev/null; do sleep 60; done
cd /home/taewook/autoware_carla_leaderboard/experiments
LOG=results/hardfast_full6_0822.log
echo "--- full: lf $(date +%m%d_%H:%M) (detached 인계) ---" >> $LOG
SUP_HARD_FAST=1 PYTHONUNBUFFERED=1 python3 experiment_runner.py --fault lf --method both --reps 15 >> $LOG 2>&1
echo "=== hardfast full6 done $(date +%m%d_%H:%M) ===" >> $LOG
