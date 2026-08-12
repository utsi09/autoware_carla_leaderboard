#!/bin/bash
# 4개 lot 성공 장면 촬영: 케이스당 video_once 프레임 -> mp4 인코딩 -> 프레임 삭제
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R=experiments/results
mkdir -p doc/videos
shoot() {  # shoot <target> <t> <outname>
  rm -f $R/frames/*.jpg 2>/dev/null
  MRM_FORCE_TARGET=$1 timeout 800 python3 experiments/experiment_runner.py \
    --fault gn --sev mid --method ours --npc none --reps 1 --t $2 --no-shoulder \
    > $R/shoot_$3.log 2>&1 &
  RPID=$!
  sleep 45
  timeout 700 docker exec aw_carla_leaderboard_0916 python3 \
    /home/taewook/autoware_carla_leaderboard/experiments/video_once.py >> $R/shoot_$3.log 2>&1
  wait $RPID
  if ls $R/frames/*.jpg >/dev/null 2>&1; then
    ffmpeg -y -loglevel error -framerate 8 -pattern_type glob -i "$R/frames/*.jpg" \
      -c:v libx264 -pix_fmt yuv420p -crf 23 doc/videos/$3.mp4
    rm -f $R/frames/*.jpg
    echo "encoded $3 -> $(du -h doc/videos/$3.mp4 | cut -f1)"
  else
    echo "NO FRAMES for $3"
  fi
}
shoot parking_1002367 27 parking_south_barn_reverse
shoot parking_1003001 45 parking_north_row
shoot parking_1003002 45 parking_roundabout_island
shoot parking_1003003 45 parking_nw_pad
df -h / | tail -1
echo SHOOT_DONE
# 촬영 끝 -> 배터리 재개 (v36 체인)
CH=experiments/launch_v36_chain.sh
nohup bash $CH >/dev/null 2>&1 &
echo "battery resumed pid $!"
