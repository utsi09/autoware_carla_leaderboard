#!/bin/bash
# 주차 프리즈 디버그: 게이트 전(trajectory_follower)/후(command) control_cmd 비교.
# 후진 궤적이 나오는데 차가 안 움직일 때 어느 단계에서 명령이 죽는지 확인용.
source /opt/ros/humble/setup.bash
source ~/autoware_awcl/autoware/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
OUT=/home/taewook/autoware_carla_leaderboard/experiments/results/parking_probe.log
: > "$OUT"
grab() {  # grab <topic> [field]
  if [ -n "$2" ]; then
    timeout 3 ros2 topic echo "$1" --field "$2" --once 2>/dev/null \
      | grep -E "velocity|acceleration" | tr -d ' ' | tr '\n' ' '
  else
    timeout 3 ros2 topic echo "$1" --once 2>/dev/null | head -c 120 | tr '\n' ' '
  fi
}
while true; do
  ts=$(date +%H:%M:%S)
  pre=$(grab /control/trajectory_follower/control_cmd longitudinal)
  post=$(grab /control/command/control_cmd longitudinal)
  gear=$(timeout 3 ros2 topic echo /control/command/gear_cmd --once 2>/dev/null | grep command | tr -d ' ')
  scen=$(timeout 3 ros2 topic echo /planning/scenario_planning/scenario --field current_scenario --once 2>/dev/null | head -1)
  echo "$ts scen=$scen gear=$gear PRE[$pre] POST[$post]" >> "$OUT"
  sleep 2
done
