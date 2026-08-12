#!/bin/bash
# v3 본 배터리: 11 고장셀 x 트래픽{none,def,agg} x 15 reps x ours/baseline = 990케이스
# 셸더+주차장 후보 모두 활성(--no-shoulder 없음), MRM_FORCE_TARGET 미설정.
# 예상 ~4일. 확장 블록(imb/imd)은 완료 후 별도 실행.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
nohup python3 experiments/experiment_runner.py --method both \
  > experiments/results/v3_battery.log 2>&1 &
echo "v3 battery pid $!"
