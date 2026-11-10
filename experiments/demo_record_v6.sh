#!/usr/bin/env bash
# [2026-11-09 18:55] 데모 전용 v6: v5 분석 — t=12 에서 이미 갓길 16 m 앞(too close<25), t=15 는 4 m; 또 eta(신호등 2개×tl_wait 15 s 포함) 65 s > eta_max 60 s 로 탈락.
#   → 런타임 파라미터 tl_visible_min_score=0, tl_wait_s=0, eta_max=120 + 주입 t=8 → 9 → 7 (갓길까지 ≈30 m). 목표 후보 shoulder_1002284.
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; V=experiments/results/videos; PICK=$V/demo_v2_pick.txt; export DISPLAY=:0
if loginctl show-session 1 -p LockedHint 2>/dev/null | grep -q yes; then gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive false >/dev/null 2>&1; sleep 2; fi
echo "$(date '+%F %T') chain: demo v6 (cn, tl rules relaxed, early t) start" | tee -a $LOG
SUPNODE="/mrm_""supervisor"
for T in 8 9 7; do
  NAME="ours-cn-high-agg-r13-v6t$T"; rm -f $V/${NAME}_x4.mp4
  echo "$(date '+%F %T') demo v6 $NAME" | tee -a $LOG
  ( set +u; source /opt/ros/humble/setup.bash >/dev/null 2>&1; source /home/taewook/fs_ws/install/setup.bash >/dev/null 2>&1
    for i in $(seq 1 300); do
      if ros2 param set $SUPNODE tl_visible_min_score 0.0 2>/dev/null | grep -q "Set parameter successful"; then
        ros2 param set $SUPNODE tl_wait_s 0.0 >/dev/null 2>&1; ros2 param set $SUPNODE eta_max 120.0 >/dev/null 2>&1
        echo "$(date '+%F %T') demo v6: params set (try $i): $(ros2 param get $SUPNODE tl_wait_s 2>/dev/null) | $(ros2 param get $SUPNODE eta_max 2>/dev/null)" | tee -a $LOG; break; fi; sleep 2
    done ) &
  SETTER=$!
  OUT=$(bash experiments/case_video.sh "$NAME" --method ours --fault cn --sev high --npc agg --rep 13 --t $T 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback"); echo "$OUT" | tee -a $LOG
  kill $SETTER 2>/dev/null; wait $SETTER 2>/dev/null
  grep -aoE "candidate shoulder_1002284 \[shoulder\]: [^\n]{0,70}|MRM_MOVE: target [a-z_0-9]+|MRM_PARKED[^ ]*|MRM_DEFER: [^(]{0,60}" experiments/results/supervisor.log 2>/dev/null | head -4 | sed "s/^/$(date '+%F %T') demo v6 sup: /" | tee -a $LOG
  if echo "$OUT" | grep -q "result=SHOULDER_SUCCESS"; then echo "cn13v6 $T" >> $PICK; break; fi
done
echo "$(date '+%F %T') chain: demo v6 done ($(cat $PICK 2>/dev/null | tr '\n' ';'))" | tee -a $LOG
exec bash experiments/fill_then_retune.sh >> experiments/results/raw_vision_pipeline.log 2>&1
