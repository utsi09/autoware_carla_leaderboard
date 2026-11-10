#!/usr/bin/env bash
# [2026-11-09] RADAS ROS2 이식 대조군 — 센서별 1건씩 5런(lf, cf, lso-high, gn-high, imn-mid; def 교통, rep 50, MRM off).
# 러너 런마다 호스트에서 radas_diag_port.py 를 띄워 /diagnostics 상당 판정을 CSV 로 남김. 완료 목록 results/radas/done.txt
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LOG=experiments/results/stock_matrix.log; OUT=experiments/results/radas; DONE=$OUT/done.txt; mkdir -p $OUT; touch $DONE
echo "$(date '+%F %T') chain: RADAS block start (5 cells)" | tee -a $LOG
for pass in 1 2; do
  for spec in "lf mid" "cf mid" "lso high" "gn high" "imn mid"; do
    set -- $spec; f=$1; s=$2; key="$f $s"
    grep -qx "$key" $DONE && continue
    [ -f experiments/results/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
    echo "$(date '+%F %T') radas $f $s rep=50 free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG
    ( set +u; source /opt/ros/humble/setup.bash >/dev/null 2>&1; exec python3 experiments/radas_diag_port.py $OUT/radas_${f}_${s}_r50.csv ) > $OUT/radas_${f}_${s}_r50.log 2>&1 &
    DPID=$!
    OUT_R=$($R --fault $f --sev $s --rep 50 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback")
    kill -INT $DPID 2>/dev/null; sleep 1; kill $DPID 2>/dev/null; wait $DPID 2>/dev/null
    echo "$OUT_R" | tee -a $LOG
    if echo "$OUT_R" | grep -qE "CARLA_DIED|INTERRUPTED|SETUP_FAIL|Traceback" || [ -z "$OUT_R" ]; then mv $OUT/radas_${f}_${s}_r50.csv $OUT/radas_${f}_${s}_r50.failed_$(date +%H%M).csv 2>/dev/null; continue; fi
    echo "$key" >> $DONE
  done
done
echo "$(date '+%F %T') chain: RADAS block done ($(wc -l < $DONE)/5)" | tee -a $LOG
