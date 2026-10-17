#!/bin/bash
# 건강도 궤적 보강 수집 (0826): cn-mid/high, imn-mid/high — /monitor/scores 녹음.
# launch_score_traces2.sh와 동일 레시피 (단일 런, npc none, t=25).
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R=experiments/results
for SPEC in "lso mid" "lso high"; do
  set -- $SPEC; F=$1; S=$2
  echo "===== SCORE-TRACE $F-$S $(date +%H:%M:%S) ====="
  ( source /opt/ros/humble/setup.bash; export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml; \
    timeout 400 ros2 topic echo /monitor/scores diagnostic_msgs/msg/DiagnosticArray --csv > $R/scoretrace_${F}_${S}.csv 2>/dev/null ) &
  RECPID=$!
  python3 experiments/experiment_runner.py --method ours --fault $F --sev $S \
    --npc none --reps 1 --t 25 >> $R/score_traces_cnimn.log 2>&1
  kill $RECPID 2>/dev/null
done
echo SCORE_TRACES_CNIMN_DONE
