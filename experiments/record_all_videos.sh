#!/usr/bin/env bash
# 디펜스 영상 3편: lso-high, lcl-high, cn-high (각 300 s, 4배속 판 포함). 순서대로.
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/record_videos.log
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "rviz recording" sleep 5400 &   # 녹화 중 화면 잠금 방지
INH=$!
for spec in "lso 0.07:150 lso_high" "lcl 25:4000 lcl_high" "cn 30 cn_high"; do   # supervisor ON (ours)
  set -- $spec
  echo "$(date '+%T') start $3" | tee -a $LOG
  experiments/record_rviz_case.sh $1 $2 300 $3 2>&1 | tee -a $LOG
  echo "$(date '+%T') done $3" | tee -a $LOG
done
kill $INH 2>/dev/null
echo "$(date '+%T') ALL VIDEOS DONE" | tee -a $LOG
