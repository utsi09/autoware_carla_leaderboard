#!/bin/bash
# v4.8 재실험 체인 (0814): 신호등 카운트 결함(병행 차선 태그 누락 → n_tl 과소
# 집계, cn 실측 "tl 0" 경로가 실제 신호교차로 통과) 수정 후, 비용함수에
# 신호등 항이 개입하는 3개 블록만 재수집. 나머지 블록(imn/lso/lcl/lf/nf)은
# 경로 선택 자체가 없어 무관 — 기존 데이터 유지.
# 수정 내용: map_model.py 교차로-근접 기하 카운트 (junction cluster 5개,
# 경로 중심선 25m 이내 통과 시 계상). 폴백/INF 룰은 코드 무변경, 입력만 정정.
# 이후: 순정 프로브 -> 자이로 보강 -> lcl 보충. 크래시 재수집은 별도.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
for f in cf cn gn; do
  echo "===== V48 BLOCK $f ====="
  python3 experiments/experiment_runner.py --method both --fault $f \
    >> experiments/results/v48_rerun.log 2>&1
done
bash experiments/launch_stock_probe.sh
bash experiments/launch_gyro_block.sh
bash experiments/launch_lcl_completion.sh
echo V48_RERUN_DONE
