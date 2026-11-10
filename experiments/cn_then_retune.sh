#!/usr/bin/env bash
# cn 사다리(12) 먼저, 끝나면 lcl 재튜닝 파이프라인 재개(완료 목록 기준 이어서).
cd /home/taewook/autoware_carla_leaderboard
bash experiments/cn_sweep.sh
exec bash experiments/lcl_retune_ext.sh >> experiments/results/retune_ext/pipeline.log 2>&1
