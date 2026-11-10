#!/usr/bin/env bash
# [2026-11-09] 사다리(새 모니터 v5b, 28런) → lcl_retune_ext.sh (보정 v5b → 관문 → 빌드 → 폐루프 일치 검사 → 295런)
cd /home/taewook/autoware_carla_leaderboard
bash experiments/lcl_alpha_ladder.sh
exec bash experiments/lcl_retune_ext.sh >> experiments/results/retune_ext/pipeline.log 2>&1
