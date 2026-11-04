#!/usr/bin/env bash
# 순정 Autoware(감시·대응 없음, --mrm-off) 비교군 매트릭스. 설계: fs_failsafe/docs/stock_freeze_plan.md
# 캠페인과 같은 셀·시드·주입시점: 교통 def -> none -> agg, rep 마다 13조건 라운드로빈.
# 완료 셀은 results/stock_done.txt 에 적어 재시작 시 건너뛴다.  사용: experiments/stock_matrix.sh
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "stock matrix rviz recording" sleep 300000 >/dev/null 2>&1 &
INH=$!
LOG=experiments/results/stock_matrix.log
DONE=experiments/results/stock_done.txt
touch $DONE
COND=("cf mid" "cn mid" "cn high" "gn mid" "gn high" "lso mid" "lso high" "lcl mid" "lcl high" "imn mid" "imn high" "lf mid" "nf mid")
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
echo "$(date '+%F %T') stock matrix done" | tee -a $LOG
