#!/usr/bin/env bash
# [2026-11-09] 본심 데모 영상: 제안(ours, MRM on) lso-high / imn-mid, agg 교통 rep 2 (순정 영상 stock-*-agg-r2_x4 와 같은 시드) → RViz 녹화 4배속.
# 끝나면 사다리 채우기(fill_then_retune.sh) 재개. 사용자 지시 16:30.
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
echo "$(date '+%F %T') chain: demo video recording start (ours lso-high agg r2, ours imn-mid agg r2)" | tee -a $LOG
for pass in 1 2; do
  for spec in "lso high" "imn mid"; do
    set -- $spec; f=$1; s=$2; NAME="ours-$f-$s-agg-r2"
    [ -s experiments/results/videos/${NAME}_x4.mp4 ] && continue
    echo "$(date '+%F %T') demo video $NAME" | tee -a $LOG
    bash experiments/case_video.sh "$NAME" --method ours --fault $f --sev $s --npc agg --rep 2 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback" | tee -a $LOG
  done
done
echo "$(date '+%F %T') chain: demo video recording done" | tee -a $LOG
exec bash experiments/fill_then_retune.sh >> experiments/results/raw_vision_pipeline.log 2>&1
