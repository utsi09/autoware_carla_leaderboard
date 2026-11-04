#!/usr/bin/env bash
# 순정 매트릭스의 항법 확장 블록: 캠페인 그림의 "Navigation ext.†" 행(gm, gb, imb, imd)과 짝을 맞추는 315셀.
# 7조건(gb, gm-mid/high, imb-mid/high, imd-mid/high) × 교통 3종 × 15회. stock_matrix.sh 와 같은 로그·완료 목록을 쓴다.
# 완료 셀은 results/stock_done.txt 에 적어 재시작 시 건너뛴다.  사용: experiments/stock_navext.sh (stock_matrix.sh 가 끝난 뒤)
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "stock matrix rviz recording" sleep 300000 >/dev/null 2>&1 &
INH=$!
LOG=experiments/results/stock_matrix.log
DONE=experiments/results/stock_done.txt
touch $DONE
COND=("gb mid" "gm mid" "gm high" "imb mid" "imb high" "imd mid" "imd high")
for npc in def none agg; do
  for rep in $(seq 0 14); do
    for c in "${COND[@]}"; do
      set -- $c; f=$1; s=$2
      grep -qx "$f $s $npc $rep" $DONE && continue
      [ -f experiments/results/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
      echo "$(date '+%F %T') stock $f-$s npc=$npc rep=$rep free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG
      experiments/stock_case_video.sh "$f" "$s" "$npc" "$rep" 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback" | tee -a $LOG
      echo "$f $s $npc $rep" >> $DONE
    done
  done
done
kill $INH 2>/dev/null
echo "$(date '+%F %T') stock nav-ext block done" | tee -a $LOG
