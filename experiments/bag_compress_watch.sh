#!/bin/bash
# [2026-11-08] 디스크 여유가 THRESH_GB 이하로 내려오면 bag 을 무손실 zstd 로 재압축(compress_bags.py --apply, 전수 검증 후 교체).
# 사용자 승인: "압축 자동으로 해 25기가 남으면". 5분 주기. 최근 60분 안에 바뀐 bag(기록·분석 중)은 건너뜀. 러너 DISK_FULL 관문(15 GB)보다 위에서 작동.
B=/home/taewook/autoware_carla_leaderboard/experiments/results/bags
SCRIPT=/home/taewook/autoware_carla_leaderboard/experiments/compress_bags.py
THRESH_GB=${THRESH_GB:-25}
while true; do
  free=$(df -BG --output=avail /home | tail -1 | tr -dc 0-9)
  if [ -n "$free" ] && [ "$free" -le "$THRESH_GB" ]; then
    echo "$(date '+%F %T') free=${free}G <= ${THRESH_GB}G -> compress batch (30 bags)"
    nice -n 19 ionice -c3 bash -c "source /opt/ros/humble/setup.bash && source /home/taewook/autoware_awcl/autoware/install/setup.bash && python3 $SCRIPT $B --apply --min-age-min 60 --limit 30" 2>&1 | tail -3
    continue   # 바로 다시 확인 (여유가 생길 때까지 배치 반복)
  fi
  sleep 300
done
