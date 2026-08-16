#!/bin/bash
# lcl(라이다 비) 블록 미완 구간 보충 (0813 밤: 블록이 141/180에서
# "CARLA could not be recovered"로 조기 종료 — 디스플레이 분리 시점과 겹침).
# 미수집: high-def rep10 baseline + rep11~14 both, high-agg rep0~14 both (39케이스).
# 러너에 rep 범위 필터가 없어 def는 15reps 재실행 -> 병합 때 (sev,npc,rep,method)
# 중복 셀은 원본(results_0813_1513.csv) 우선으로 dedupe.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
python3 experiments/experiment_runner.py --method both --fault lcl --sev high --npc agg \
  >> experiments/results/lcl_completion.log 2>&1
python3 experiments/experiment_runner.py --method both --fault lcl --sev high --npc def \
  >> experiments/results/lcl_completion.log 2>&1
echo LCL_COMPLETION_DONE
