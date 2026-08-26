#!/bin/bash
# cn-mid 궤적 재수집 (레코더 프로세스 그룹 동반 종료판 — 케이스 간 오염 방지)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R=experiments/results
setsid bash -c "source /opt/ros/humble/setup.bash; export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml; \
  timeout 400 ros2 topic echo /monitor/scores diagnostic_msgs/msg/DiagnosticArray --csv > $R/scoretrace_cn_mid.csv 2>/dev/null" &
RECPID=$!
python3 experiments/experiment_runner.py --method ours --fault cn --sev mid \
  --npc none --reps 1 --t 25 >> $R/score_traces_cnimn.log 2>&1
kill -TERM -$RECPID 2>/dev/null; sleep 1; kill -9 -$RECPID 2>/dev/null
pkill -9 -f 'topic echo /monitor/scores' 2>/dev/null
echo CNMID_CLEAN_DONE; tail -2 $R/score_traces_cnimn.log; wc -c $R/scoretrace_cn_mid.csv
