#!/usr/bin/env bash
# metadata.yaml 이 없는 bag(기록기가 강제 종료된 것)을 reindex 한다.  사용: experiments/reindex_bags.sh
source /opt/ros/humble/setup.bash
for d in /home/taewook/autoware_carla_leaderboard/experiments/results/bags/*/; do
  [ -f "$d/metadata.yaml" ] && continue
  ls "$d"/*.mcap >/dev/null 2>&1 || continue
  echo "reindex $(basename $d)"; ros2 bag reindex -s mcap "$d" 2>&1 | grep -i "complete\|error" | tail -1
done
