#!/usr/bin/env bash
# [2026-11-09 17:05] 카메라 잡음 high: 순정 빨간불 대기(frozen_light) rep 에서 제안 갓길 대피(SHOULDER_SUCCESS) 재시도 2패스(비결정적이라 재시도 의미 있음). 성공 시 demo_v2_pick.txt 에 "cn <rep>". 끝나면 fill 재개.
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; V=experiments/results/videos; PICK=$V/demo_v2_pick.txt; export DISPLAY=:0
if loginctl show-session 1 -p LockedHint 2>/dev/null | grep -q yes; then gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive false >/dev/null 2>&1; sleep 2; fi
echo "$(date '+%F %T') chain: demo v3 (cn shoulder retry) start" | tee -a $LOG
for pass in 1 2; do
  grep -q "^cn " $PICK 2>/dev/null && break
  for rep in 13 3 6 9 12 14; do
    NAME="ours-cn-high-agg-r$rep"; rm -f $V/${NAME}_x4.mp4
    echo "$(date '+%F %T') demo v3 $NAME pass$pass" | tee -a $LOG
    OUT=$(bash experiments/case_video.sh "$NAME" --method ours --fault cn --sev high --npc agg --rep $rep 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback"); echo "$OUT" | tee -a $LOG
    if echo "$OUT" | grep -q "result=SHOULDER_SUCCESS"; then echo "cn $rep" >> $PICK; break; fi
  done
done
echo "$(date '+%F %T') chain: demo v3 done ($(cat $PICK 2>/dev/null | tr '\n' ';'))" | tee -a $LOG
exec bash experiments/fill_then_retune.sh >> experiments/results/raw_vision_pipeline.log 2>&1
