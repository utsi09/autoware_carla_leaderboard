#!/usr/bin/env bash
# [2026-11-09] 데모 영상 녹화만(체인 재개 없음). 화면 잠금이면 GNOME ScreenSaver 해제 시도 → 실패 시 건너뛰고 마커만 남김.
#  1) ours lso-high agg r2 (차선 내 정지)  2) ours imn-mid agg r2 (비상정지)  3)4) ours cn-high agg r7·r13 (갓길 대피 기대; 사용자 결정 16:30 — lso 대신 cn-high 를 대피 데모로)
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; V=experiments/results/videos; export DISPLAY=:0
if loginctl show-session 1 -p LockedHint 2>/dev/null | grep -q yes; then
  gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive false >/dev/null 2>&1; sleep 2
fi
if loginctl show-session 1 -p LockedHint 2>/dev/null | grep -q yes; then
  echo "$(date '+%F %T') chain: demo recording SKIPPED — desktop still locked" | tee -a $LOG; exit 0
fi
echo "$(date '+%F %T') chain: demo video recording start (4 cells)" | tee -a $LOG
for pass in 1 2; do
  for spec in "ours lso high agg 2" "ours imn mid agg 2" "ours cn high agg 7" "ours cn high agg 2"; do   # cn-high agg r7·r2 = 8월 본 캠페인(results_0814_1833) 갓길 대피 셀(순정 영상 stock-cn-high-agg-r7/r2 있음)
    set -- $spec; m=$1; f=$2; s=$3; n=$4; r=$5
    if [ "$m" = stock ]; then NAME="stock-$f-$s-$n-r$r"; else NAME="ours-$f-$s-$n-r$r"; fi
    [ -s $V/${NAME}_x4.mp4 ] && continue
    echo "$(date '+%F %T') demo video $NAME" | tee -a $LOG
    if [ "$m" = stock ]; then bash experiments/stock_case_video.sh $f $s $n $r 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback" | tee -a $LOG
    else bash experiments/case_video.sh "$NAME" --method ours --fault $f --sev $s --npc $n --rep $r 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback" | tee -a $LOG; fi
  done
done
echo "$(date '+%F %T') chain: demo video recording done" | tee -a $LOG
