#!/usr/bin/env bash
# [2026-11-09 17:00] 데모 영상 v2 (사용자 지시): ① 카메라 잡음 high — 제안은 갓길 대피(SHOULDER_SUCCESS), 순정은 빨간 신호 무한 대기(frozen_light) 가 나오는 rep 로.
#   순정 frozen_light agg rep(영상 있음): 13 3 6 9 12 14 → 제안을 같은 rep 로 녹화해 SHOULDER_SUCCESS 나올 때까지.
# ② IMU 잡음 mid — 제안이 자기 차로에서 비상정지한 런이 나올 때까지(lane_check offset<1.2 m), rep 3 4 5 6 7 10 11 12 14 (순정 영상 있음).
# 성공 rep 은 results/videos/demo_v2_pick.txt 에 기록. 끝나면 fill_then_retune.sh 재개.
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; V=experiments/results/videos; PICK=$V/demo_v2_pick.txt; export DISPLAY=:0
if loginctl show-session 1 -p LockedHint 2>/dev/null | grep -q yes; then
  gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive false >/dev/null 2>&1; sleep 2
fi
echo "$(date '+%F %T') chain: demo v2 recording start" | tee -a $LOG
if ! grep -q "^cn " $PICK 2>/dev/null; then
  for rep in 13 3 6 9 12 14; do
    NAME="ours-cn-high-agg-r$rep"; echo "$(date '+%F %T') demo v2 $NAME" | tee -a $LOG
    OUT=$(bash experiments/case_video.sh "$NAME" --method ours --fault cn --sev high --npc agg --rep $rep 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback"); echo "$OUT" | tee -a $LOG
    if echo "$OUT" | grep -q "result=SHOULDER_SUCCESS"; then echo "cn $rep" >> $PICK; break; fi
  done
fi
if ! grep -q "^imn " $PICK 2>/dev/null; then
  for rep in 2 3 4 5 6 7 10 11 12 14; do   # r2 는 같은 시드에서 자기 차로 정지(15:51·15:58)·반대 차로(16:29) 둘 다 나옴 → 먼저 재시도
    NAME="ours-imn-mid-agg-r$rep"; echo "$(date '+%F %T') demo v2 $NAME" | tee -a $LOG
    OUT=$(bash experiments/case_video.sh "$NAME" --method ours --fault imn --sev mid --npc agg --rep $rep 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback"); echo "$OUT" | tee -a $LOG
    GT=$(ls -t experiments/results/gt/imn-mid-agg-r$rep-*.csv 2>/dev/null | grep -v _tl | head -1)
    LC=$([ -n "$GT" ] && python3 experiments/analysis/lane_check.py "$GT" agg 2>/dev/null); echo "$(date '+%F %T') lane_check $NAME $LC" | tee -a $LOG
    if echo "$OUT" | grep -qE "result=AW_(EMERGENCY|COMFORTABLE)_STOP_DONE" && echo "$LC" | grep -q "in_lane"; then echo "imn $rep" >> $PICK; break; fi
  done
fi
echo "$(date '+%F %T') chain: demo v2 recording done ($(cat $PICK 2>/dev/null | tr '\n' ';'))" | tee -a $LOG
exec bash experiments/fill_then_retune.sh >> experiments/results/raw_vision_pipeline.log 2>&1
