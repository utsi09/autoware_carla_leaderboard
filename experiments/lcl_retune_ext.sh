#!/usr/bin/env bash
# [2026-11-09 16:00] 사용자 결정으로 재튜닝 C·D 블록 중단. 원본은 results/retune_ext/lcl_retune_ext.sh.disabled_1109_1600
cd /home/taewook/autoware_carla_leaderboard
echo "$(date '+%F %T') chain: lcl retune(ext) skipped — stopped by user (A 90, B 90, C 12 done; C/D not continued)" | tee -a experiments/results/stock_matrix.log
exit 0
