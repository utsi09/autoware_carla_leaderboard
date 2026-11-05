#!/usr/bin/env bash
# 체인(run_chain.sh)이 모두 끝난 뒤, 스윕 경량판에서 CARLA 사망 등으로 빠진 셀(rr_done.txt 에 없는 것)을 다시 돈다.
#   사용: nohup experiments/after_chain.sh > experiments/results/after_chain.log 2>&1 &
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
until grep -q "ALL BLOCKS DONE" $LOG; do sleep 60; done
echo "$(date '+%F %T') chain: rerunning missing sweep cells" | tee -a $LOG
bash experiments/noise_sweep_lite.sh
echo "$(date '+%F %T') chain: sweep reruns done" | tee -a $LOG
