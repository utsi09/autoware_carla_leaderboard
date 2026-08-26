#!/bin/bash
# 단일 케이스 궤적 수집 (그룹킬 레코더): trace_one_clean.sh <fault> <sev>
F=$1; S=$2
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R=experiments/results
setsid bash -c "source /opt/ros/humble/setup.bash; export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml; \
  timeout 400 ros2 topic echo /monitor/scores diagnostic_msgs/msg/DiagnosticArray --csv > $R/scoretrace_${F}_${S}.csv 2>/dev/null" &
RECPID=$!
python3 experiments/experiment_runner.py --method ours --fault $F --sev $S \
  --npc none --reps 1 --t 25 >> $R/score_traces_cnimn.log 2>&1
kill -TERM -$RECPID 2>/dev/null; sleep 1; kill -9 -$RECPID 2>/dev/null
pkill -9 -f 'topic[ ]echo /monitor/scores' 2>/dev/null
echo "TRACE_${F}_${S}_DONE $(wc -c < $R/scoretrace_${F}_${S}.csv)"
