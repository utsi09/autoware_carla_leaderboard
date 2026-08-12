#!/bin/bash
# 남쪽·북쪽 재촬영 — 케이스 판정(PARKED_SUCCESS) 검증 후에만 인코딩, 최대 3회 재시도
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R=experiments/results
shoot_verified() {  # <target> <t> <outname>
  for try in 1 2 3; do
    rm -f $R/frames/*.jpg 2>/dev/null
    MRM_FORCE_TARGET=$1 timeout 800 python3 experiments/experiment_runner.py \
      --fault gn --sev mid --method ours --npc none --reps 1 --t $2 --no-shoulder \
      > $R/reshoot_$3_try$try.log 2>&1 &
    RPID=$!
    sleep 45
    timeout 700 docker exec aw_carla_leaderboard_0916 python3 \
      /home/taewook/autoware_carla_leaderboard/experiments/video_once.py >> $R/reshoot_$3_try$try.log 2>&1
    wait $RPID
    V=$(grep -a "result:" $R/reshoot_$3_try$try.log | tail -1)
    echo "$3 try$try: $V"
    if echo "$V" | grep -q "PARKED_SUCCESS"; then
      ffmpeg -y -loglevel error -framerate 8 -pattern_type glob -i "$R/frames/*.jpg" \
        -c:v libx264 -pix_fmt yuv420p -crf 23 doc/videos/$3.mp4
      rm -f $R/frames/*.jpg
      ffmpeg -y -loglevel error -sseof -120 -i doc/videos/$3.mp4 \
        -c:v libx264 -crf 26 -pix_fmt yuv420p doc/videos/$3_clip.mp4
      echo "VERIFIED+ENCODED $3"
      return 0
    fi
    rm -f $R/frames/*.jpg
  done
  echo "RESHOOT FAILED $3 (3 tries)"
}
shoot_verified parking_1002367 27 parking_south_barn_reverse
shoot_verified parking_1003001 45 parking_north_row
echo RESHOOT_DONE
CH=experiments/launch_v36_chain.sh
nohup bash $CH >/dev/null 2>&1 &
echo "battery resumed pid $!"
