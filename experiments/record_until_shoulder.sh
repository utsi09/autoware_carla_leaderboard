#!/usr/bin/env bash
# lso-high 를 갓길 대피(SHOULDER/PARKED 성공)가 나올 때까지 시드·주입시점을 바꿔 가며 녹화. 성공 회차만 남긴다.
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/record_until_shoulder.log
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "rviz recording" sleep 7200 >/dev/null 2>&1 &
INH=$!
MAX=${MAX:-12}
for i in $(seq 1 $MAX); do
  rep=$(( (i-1) % 15 )); t=$(( 15 + (i-1)*7 % 40 ))
  echo "$(date '+%T') try $i rep=$rep t=$t" | tee -a $LOG
  REP=$rep T=$t experiments/record_rviz_case.sh lso 0.07:150 420 lso_high_try$i >> $LOG 2>&1
  res=$(grep -a -m1 "\[runner\] result" experiments/results/video_lso_high_try$i.log | sed 's/.*result: //')
  fs=$(grep -a -m1 "state .* -> MRM_MOVE\|state .* -> MRM_PARKED" experiments/results/supervisor.log 2>/dev/null | cut -c60-140)
  echo "$(date '+%T') try $i -> $res | $fs" | tee -a $LOG
  if echo "$res" | grep -q "SHOULDER_SUCCESS\|PARKED_SUCCESS"; then
    mv doc/videos/lso_high_try$i.mp4 doc/videos/lso_high_shoulder.mp4; mv doc/videos/lso_high_try${i}_x4.mp4 doc/videos/lso_high_shoulder_x4.mp4
    echo "$(date '+%T') SHOULDER FOUND at try $i" | tee -a $LOG; break
  else
    rm -f doc/videos/lso_high_try$i.mp4 doc/videos/lso_high_try${i}_x4.mp4
  fi
done
kill $INH 2>/dev/null
echo "$(date '+%T') UNTIL-SHOULDER DONE" | tee -a $LOG
