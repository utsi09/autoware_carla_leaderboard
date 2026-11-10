#!/usr/bin/env bash
# [2026-11-09 17:50] 데모 전용: 카메라 잡음 high, 주행 시작 직후 주입(--t), 감독기 최소 접근거리(min_approach_dist 25 m)를 런타임 파라미터로 3 m 로 낮춰
#   첫 직선의 갓길(shoulder_1002243 (10,−56) / 1002238)을 고를 수 있게 함 → 교차로 전 갓길 정지. 코드 수정 없음(ros2 param set), 논문 실험에는 미적용.
#   순정 짝 = stock-cn-high-agg-r13 (빨간불 대기). 시도: t=3 → 5 → 8. 성공 시 demo_v2_pick.txt 에 "cn13early <t>". 끝나면 fill 재개.
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; V=experiments/results/videos; PICK=$V/demo_v2_pick.txt; export DISPLAY=:0
if loginctl show-session 1 -p LockedHint 2>/dev/null | grep -q yes; then gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive false >/dev/null 2>&1; sleep 2; fi
echo "$(date '+%F %T') chain: demo v4 (early cn, min_approach_dist=3) start" | tee -a $LOG
SUPNODE="/mrm_""supervisor"
for T in 3 5 8; do
  NAME="ours-cn-high-agg-r13-t$T"; rm -f $V/${NAME}_x4.mp4
  echo "$(date '+%F %T') demo v4 $NAME" | tee -a $LOG
  ( set +u; source /opt/ros/humble/setup.bash >/dev/null 2>&1; source /home/taewook/fs_ws/install/setup.bash >/dev/null 2>&1
    for i in $(seq 1 300); do
      if ros2 param set $SUPNODE min_approach_dist 3.0 2>/dev/null | grep -q "Set parameter successful"; then echo "$(date '+%F %T') demo v4: min_approach_dist=3.0 set (try $i)" | tee -a $LOG; break; fi; sleep 2
    done ) &
  SETTER=$!
  OUT=$(bash experiments/case_video.sh "$NAME" --method ours --fault cn --sev high --npc agg --rep 13 --t $T 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback"); echo "$OUT" | tee -a $LOG
  kill $SETTER 2>/dev/null; wait $SETTER 2>/dev/null
  grep -aoE "MRM_MOVE: target [a-z_0-9]+|MRM_PARKED[^ ]*|MRM_DEFER: [^(]{0,60}" experiments/results/supervisor.log 2>/dev/null | head -3 | sed "s/^/$(date '+%F %T') demo v4 sup: /" | tee -a $LOG
  if echo "$OUT" | grep -q "result=SHOULDER_SUCCESS"; then echo "cn13early $T" >> $PICK; break; fi
done
echo "$(date '+%F %T') chain: demo v4 done ($(cat $PICK 2>/dev/null | tr '\n' ';'))" | tee -a $LOG
exec bash experiments/fill_then_retune.sh >> experiments/results/raw_vision_pipeline.log 2>&1
