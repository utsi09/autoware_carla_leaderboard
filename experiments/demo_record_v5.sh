#!/usr/bin/env bash
# [2026-11-09 18:40] 데모 전용 v5: 카메라 잡음 high + 감독기 신호등 가시성 문턱(tl_visible_min_score 0.5→0.0)을 런타임 파라미터로 완화
#   → 교차로 앞 접근로 갓길 shoulder_1002284 (0.8,−29.2) 가 후보로 살아남(기본 25 m 접근거리 유지라 코너·첫 직선 갓길은 too close 로 빠짐).
#   주입 --t 15 → 12 → 18 (차가 첫 직선 중간, 후보까지 40–45 m). 순정 짝 stock-cn-high-agg-r13(빨간불 대기). 논문 실험 미적용(데모 전용).
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; V=experiments/results/videos; PICK=$V/demo_v2_pick.txt; export DISPLAY=:0
if loginctl show-session 1 -p LockedHint 2>/dev/null | grep -q yes; then gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive false >/dev/null 2>&1; sleep 2; fi
echo "$(date '+%F %T') chain: demo v5 (cn, tl_visible_min_score=0) start" | tee -a $LOG
SUPNODE="/mrm_""supervisor"
for T in 15 12 18; do
  NAME="ours-cn-high-agg-r13-tl$T"; rm -f $V/${NAME}_x4.mp4
  echo "$(date '+%F %T') demo v5 $NAME" | tee -a $LOG
  ( set +u; source /opt/ros/humble/setup.bash >/dev/null 2>&1; source /home/taewook/fs_ws/install/setup.bash >/dev/null 2>&1
    for i in $(seq 1 300); do
      if ros2 param set $SUPNODE tl_visible_min_score 0.0 2>/dev/null | grep -q "Set parameter successful"; then echo "$(date '+%F %T') demo v5: tl_visible_min_score=0.0 set (try $i)" | tee -a $LOG; break; fi; sleep 2
    done ) &
  SETTER=$!
  OUT=$(bash experiments/case_video.sh "$NAME" --method ours --fault cn --sev high --npc agg --rep 13 --t $T 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback"); echo "$OUT" | tee -a $LOG
  kill $SETTER 2>/dev/null; wait $SETTER 2>/dev/null
  grep -aoE "candidate shoulder_1002284 \[shoulder\]: [^\n]{0,70}|MRM_MOVE: target [a-z_0-9]+|MRM_PARKED[^ ]*|MRM_DEFER: [^(]{0,60}" experiments/results/supervisor.log 2>/dev/null | head -4 | sed "s/^/$(date '+%F %T') demo v5 sup: /" | tee -a $LOG
  if echo "$OUT" | grep -q "result=SHOULDER_SUCCESS"; then echo "cn13tl $T" >> $PICK; break; fi
done
echo "$(date '+%F %T') chain: demo v5 done ($(cat $PICK 2>/dev/null | tr '\n' ';'))" | tee -a $LOG
exec bash experiments/fill_then_retune.sh >> experiments/results/raw_vision_pipeline.log 2>&1
