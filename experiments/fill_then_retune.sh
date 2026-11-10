#!/usr/bin/env bash
# 데모 영상 녹화(잠금 해제 상태에서만) → 사다리 채우기(B) → lcl 재튜닝 스텁
cd /home/taewook/autoware_carla_leaderboard
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "thesis demo video recording" bash experiments/demo_record_only.sh
bash experiments/ladder_fill_b.sh
exec bash experiments/lcl_retune_ext.sh >> experiments/results/retune_ext/pipeline.log 2>&1
