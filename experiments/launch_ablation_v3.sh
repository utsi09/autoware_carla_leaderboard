#!/bin/bash
# v5 절제 캠페인 (계획서 v3, 전문가 승인): 10시드 x 4팔 = 40케이스
# 시드 고정: fault_t/보행속도/지터/fault_seed, 자리균형 팔 순서, 케이스별 CARLA 재기동
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/ablation_v3.log
R=/home/taewook/autoware_carla_leaderboard/experiments/results
tail -n +2 experiments/seeds_ablation.csv | while IFS=, read SEED FT WS JIT FSEED WSEED ORDER; do
  for ARM in ${ORDER//-/ }; do
    echo "===== $SEED $ARM (ft=$FT ws=$WS jit=$JIT) =====" | tee -a $LOG
    export FAULT_SEED=$FSEED WALKER_SEED=$WSEED
    export FAULT_TRACE=$R/ftrace_${SEED}_${ARM}.csv
    export DETECT_CAP=capability/localization
    export FREEZE_TL=1
    SPEC="ped=dist:8:t3.0:w${WS}:j${JIT}"
    unset MRM_MOVE_SPEED MRM_CAP_MODE MRM_FORCE_TARGET
    case $ARM in
      A1) SUP_SHADOW=1 HAZARD=$SPEC python3 experiments/experiment_runner.py \
            --method ours --mrm-off --fault gn --sev mid --npc none \
            --reps 1 --t $FT >> $LOG 2>&1 ;;
      A2) HAZARD=$SPEC python3 experiments/experiment_runner.py \
            --method baseline --fault gn --sev mid --npc none \
            --reps 1 --t $FT >> $LOG 2>&1 ;;
      A3) HAZARD=$SPEC python3 experiments/experiment_runner.py \
            --method ours --fault gn --sev mid --npc none \
            --reps 1 --t $FT >> $LOG 2>&1 ;;
      A4) MRM_MOVE_SPEED=3.0 HAZARD=$SPEC python3 experiments/experiment_runner.py \
            --method ours --fault gn --sev mid --npc none \
            --reps 1 --t $FT >> $LOG 2>&1 ;;
    esac
  done
done
echo ABLATION_V3_DONE | tee -a $LOG
