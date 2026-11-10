#!/usr/bin/env bash
# [2026-11-07] after_chain.sh(스윕 재실행)까지 끝난 뒤, 조우 블록에서 CARLA 사망으로 빠진 셀(encounter_done.txt 에 없는 것)을 다시 돈다.
#   사용: experiments/after_chain2.sh  (run_in_background, 단일 인스턴스)
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
until grep -q "chain: sweep reruns done" $LOG; do sleep 60; done
echo "$(date '+%F %T') chain: rerunning missing encounter cells" | tee -a $LOG
bash experiments/encounter_block.sh
echo "$(date '+%F %T') chain: encounter reruns done — EVERYTHING DONE" | tee -a $LOG
