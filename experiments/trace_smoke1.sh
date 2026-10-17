#!/bin/bash
# psim 정리 후 스모크: cn-mid 1런 + /monitor/scores 녹음
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R=experiments/results
( source /opt/ros/humble/setup.bash; export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml; \
  timeout 400 ros2 topic echo /monitor/scores diagnostic_msgs/msg/DiagnosticArray --csv > $R/scoretrace_cn_mid.csv 2> $R/rec_err.log ) &
RECPID=$!
python3 experiments/experiment_runner.py --method ours --fault cn --sev mid \
  --npc none --reps 1 --t 25 >> $R/score_traces_cnimn.log 2>&1
kill $RECPID 2>/dev/null
echo SMOKE1_DONE; tail -3 $R/score_traces_cnimn.log; wc -c $R/scoretrace_cn_mid.csv
