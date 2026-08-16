#!/bin/bash
# 자이로 보강 블록 (사용자 지시 0813): imb(고정 편향)/imd(드리프트 램프)를
# 본 매트릭스 방법 비교로 측정 — CarFASE "자이로 최고 치명" 커버리지 보강,
# ZUPT의 조용한-고장 감지 스토리. 순정 프로브(STOCK_PROBE_DONE) 후 실행.
# 2폴트 x 2sev(자동) x npc def x 3reps x both = 48케이스 (~3.5h)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for f in imb imd; do
  echo "===== GYRO BLOCK $f ====="
  python3 experiments/experiment_runner.py --method both \
    --fault $f --npc def --reps 3 \
    >> experiments/results/gyro_block.log 2>&1
done
echo GYRO_BLOCK_DONE
