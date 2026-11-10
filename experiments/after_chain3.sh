#!/usr/bin/env bash
# [2026-11-07] 최종 보충 패스: after_chain.sh(스윕 재실행)까지 끝나면 실패 셀을 done 에서 지우고
#   순정 매트릭스 → 항법확장 → 조우 블록을 한 번 더 돌려 빠진 셀만 채운다 (after_chain2.sh 대체).
#   사용: experiments/after_chain3.sh  (run_in_background, 단일 인스턴스)
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
until grep -q "chain: sweep reruns done" $LOG; do sleep 60; done
echo "$(date '+%F %T') chain: final top-up pass — pruning failed cells" | tee -a $LOG
python3 experiments/prune_failed_done.py | tee -a $LOG
bash experiments/stock_matrix.sh
bash experiments/stock_navext.sh
bash experiments/encounter_block.sh
echo "$(date '+%F %T') chain: final top-up done — EVERYTHING DONE" | tee -a $LOG
