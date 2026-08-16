#!/bin/bash
# S05 A2/A4 CARLA_DIED 동일시드 재실행 (프로토콜 §2)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/ablation_v3.log
R=/home/taewook/autoware_carla_leaderboard/experiments/results
SEED=S05; FT=12; WS=2.5; JIT=-0.09; FSEED=1004; WSEED=2004
for ARM in A2 A4; do
  echo "===== ${SEED}R $ARM (ft=$FT ws=$WS jit=$JIT rerun) =====" | tee -a $LOG
  export FAULT_SEED=$FSEED WALKER_SEED=$WSEED
  export FAULT_TRACE=$R/ftrace_${SEED}R_${ARM}.csv
  export DETECT_CAP=capability/localization
  export FREEZE_TL=1
  SPEC="ped=dist:8:t3.0:w${WS}:j${JIT}"
  unset MRM_MOVE_SPEED MRM_CAP_MODE MRM_FORCE_TARGET
  case $ARM in
    A2) HAZARD=$SPEC python3 experiments/experiment_runner.py \
          --method baseline --fault gn --sev mid --npc none --reps 1 --t $FT >> $LOG 2>&1 ;;
    A4) MRM_MOVE_SPEED=3.0 HAZARD=$SPEC python3 experiments/experiment_runner.py \
          --method ours --fault gn --sev mid --npc none --reps 1 --t $FT >> $LOG 2>&1 ;;
  esac
done
echo S05_RERUN_DONE | tee -a $LOG
