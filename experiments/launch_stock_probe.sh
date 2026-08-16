#!/bin/bash
# 순정 오토웨어 프로브 (사용자 지시 0813): 우리 스택 개입 완전 오프(--mrm-off),
# 순정 진단->순정 MRM만으로 각 폴트에 어떻게 반응하는지 측정.
# 26케이스 (8폴트, sev 자동 x npc def x reps 2). 체인(V47_REST2_DONE) 후 실행.
# 분석 시 method 컬럼을 'stock'으로 재라벨 (러너는 ours로 기록하지만 supervisor 미개입).
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for f in cn imn gn lso lcl cf lf nf; do
  echo "===== STOCK PROBE $f ====="
  python3 experiments/experiment_runner.py --method ours --mrm-off \
    --fault $f --npc def --reps 2 \
    >> experiments/results/stock_probe.log 2>&1
done
echo STOCK_PROBE_DONE
