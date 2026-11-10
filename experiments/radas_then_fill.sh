#!/usr/bin/env bash
# RADAS 대조군 5런 → 사다리 채우기 재개
cd /home/taewook/autoware_carla_leaderboard
bash experiments/radas_block.sh
exec bash experiments/fill_then_retune.sh >> experiments/results/raw_vision_pipeline.log 2>&1
