#!/bin/bash
# v4.9u 8m 경계 x MRM 비교 (고장 교체: cf -> gn-high).
# cf는 순정이 신호등을 못 읽어 교차로 영구대기(0816 실측 303s) — 조우 불가.
# gn-high: 순정 251m 계속주행(프로브 실측), 우리는 갓길 MRM, 지각계 무사
# -> 같은 8m 조우에서 순수 속도 효과만 비교된다.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/mrm_boundary.log
echo "===== GN ARM A: ours slow-cap-3.0 8m x10 ====="
MRM_MOVE_SPEED=3.0 HAZARD="ped=dist:8:2.6:arm" \
  python3 experiments/experiment_runner.py \
  --method ours --fault gn --sev mid --npc none --reps 10 >> $LOG 2>&1
unset MRM_MOVE_SPEED
echo "===== GN ARM B: stock-observe 8m x10 ====="
HAZARD="ped=dist:8:3.8:arm" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault gn --sev mid --npc none --reps 10 >> $LOG 2>&1
echo "===== GN ARM C: ours fixed-cap-4.2 8m x5 ====="
HAZARD="ped=dist:8:3.6:arm" python3 experiments/experiment_runner.py \
  --method ours --fault gn --sev mid --npc none --reps 5 >> $LOG 2>&1
echo GN_BOUNDARY_DONE
# 후속: 실명 사다리 나머지 + gm 검증
unset MRM_FORCE_TARGET MRM_CAP_MODE
NLOG=experiments/results/night_queue.log
for D in 11 8 6 5; do
  echo "===== BLIND-LADDER D=${D}m ====="
  HAZARD="ped=dist:$D" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault lso --sev high --npc none --reps 2 >> $NLOG 2>&1
done
for SEV in mid high; do
  echo "===== GM-VERIFY sev=$SEV ====="
  python3 experiments/experiment_runner.py \
    --method ours --fault gm --sev $SEV --npc none --reps 2 >> $NLOG 2>&1
done
echo NIGHT_ALL_DONE
