#!/bin/bash
# v4.3 본 배터리: Arm A(990, 갓길+주차 자연선택) -> Arm C(민감도 스윕)
# Arm B 는 폐지 — Arm A 의 주차 선택 분포를 보고 부족 셀만 no-shoulder 보충
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
python3 experiments/experiment_runner.py --method both \
  > experiments/results/v43_armA_main.log 2>&1
bash experiments/launch_v3_armC.sh >> experiments/results/v43_armC.log 2>&1
echo ARMA_ARMC_DONE
