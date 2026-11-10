#!/usr/bin/env bash
# [2026-11-08] 검증(105) 끝 → 비전 베이스라인 블록(36) → lcl 재튜닝 확장안(295).
# lcl_retune_ext.sh 는 같은 마커("chain: lcl severity validation done")를 다시 확인하므로 그대로 이어 실행된다.
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
until grep -q "chain: lcl severity validation done" $LOG; do sleep 60; done
bash experiments/vision_baseline_block.sh
exec bash experiments/lcl_retune_ext.sh >> experiments/results/retune_ext/pipeline.log 2>&1
