#!/usr/bin/env bash
# [2026-11-08] 비전 베이스라인 블록 (사용자 승인 "비전 베이스라인들 비교 먼저 뽑자").
# 순정(--mrm-off) 런을 표준 bag(--record)으로 남기면서, 옆에서 vision_raw_recorder.py 가 전방 점군·
# 카메라 이미지를 2 Hz(시뮬)로 저장 → Won 2023(구면 비트맵 소실) / Zhang 2024(거리·반사강도 분포) /
# Lee 2022(CNN 분류) 구조 재구현 베이스라인을 오프라인에서 제안 방식과 같은 런으로 비교한다.
#   nf × 6 (rep 30-35; 짝수 rep = 문턱 보정, 홀수 rep = 오탐 평가) + lso/lcl/cn × mid/high × 5 (rep 30-34) = 36런
#   rep 30+ 는 순정 매트릭스(0-14)·재튜닝(15-29)과 겹치지 않는다. 고장 시각은 셀 키에서 결정적으로 뽑힘(10-45 s).
# 완료 목록 results/raw_vision/vb_done.txt, 런↔bag 매핑 results/raw_vision/map.csv (실패 셀은 안 적고 2차 패스).
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; RES=experiments/results; X=$RES/raw_vision; DONE=$X/vb_done.txt
mkdir -p $X; touch $DONE
[ -f $X/map.csv ] || echo "fault,sev,rep,bag_tag,raw_dir,result" > $X/map.csv
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "vision baseline block" sleep 100000 >/dev/null 2>&1 & INH=$!
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --no-log-archive"
echo "$(date '+%F %T') chain: vision baseline block start (36 cells)" | tee -a $LOG

run_cell () {  # fault sev rep
  local f=$1 s=$2 rep=$3 key="$1 $2 $3"
  grep -qx "$key" $DONE && return 0
  [ -f $RES/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
  local free; free=$(df -BG --output=avail /home | tail -1 | tr -dc 0-9)
  if [ "$free" -lt 18 ]; then echo "$(date '+%F %T') vb: free=${free}G < 18G — stop block" | tee -a $LOG; exit 1; fi
  local OUTD=$X/vb-$f-$s-r$rep; rm -rf "$OUTD"; mkdir -p "$OUTD"
  echo "$(date '+%F %T') vb $f-$s rep=$rep free=${free}G" | tee -a $LOG
  ( set +u   # ROS setup.bash 는 nounset 아래서 죽는다(AMENT_TRACE_SETUP_FILES) — 11/08 20:05 첫 셀에서 레코더 미기동 원인
    export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
    source /opt/ros/humble/setup.bash
    exec python3 experiments/vision_raw_recorder.py --out "$OUTD" --hz 2.0 ) > "$OUTD/recorder.log" 2>&1 &
  local RP=$!
  local OUT; OUT=$($R --fault "$f" --sev "$s" --rep "$rep" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback")
  kill -TERM $RP 2>/dev/null; wait $RP 2>/dev/null
  echo "$OUT" | tee -a $LOG
  local TAG; TAG=$(ls -td $RES/bags/stock-$f-$s-def-r$rep-* 2>/dev/null | head -1 | xargs -rn1 basename)
  local RESULT; RESULT=$(echo "$OUT" | grep -oE "result: [A-Z_]+" | head -1 | cut -d' ' -f2)
  echo "$f,$s,$rep,$TAG,$OUTD,${RESULT:-NONE}" >> $X/map.csv
  if echo "$OUT" | grep -qE "CARLA_DIED|INTERRUPTED|SETUP_FAIL|Traceback" || [ -z "$OUT" ]; then return 0; fi
  echo "$key" >> $DONE
}

for pass in 1 2; do
  for rep in 30 31 32 33 34; do
    run_cell nf mid $rep
    for c in "lso mid" "lso high" "lcl mid" "lcl high" "cn mid" "cn high"; do run_cell $c $rep; done
  done
  run_cell nf mid 35
done
kill $INH 2>/dev/null
echo "$(date '+%F %T') chain: vision baseline block done ($(wc -l < $DONE)/36)" | tee -a $LOG
