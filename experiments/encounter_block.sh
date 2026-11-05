#!/usr/bin/env bash
# 조우 블록 A: 고장 3종 + nf × 2팔(순정 stock mrm-off / 제안 ours) × 10시드, 보행자 돌발(고장 5 s 뒤 전방 8 m, 2.5 m/s).
# 같은 시드는 세 팔이 같은 교통·같은 보행자·같은 주입시점을 만난다. 완료 셀은 results/encounter_done.txt.
#   사용: experiments/encounter_block.sh        (약 80회, 7시간)
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/encounter_block.log; DONE=experiments/results/encounter_done.txt; touch $DONE
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "encounter block" sleep 60000 >/dev/null 2>&1 & INH=$!
COND=("nf nf" "lso 0.07:150" "lcl 25:4000" "cn 30")
for rep in $(seq 0 9); do
  for c in "${COND[@]}"; do
    set -- $c; f=$1; v=$2
    for arm in stock ours; do
      grep -qx "$f $v $arm $rep" $DONE && continue
      [ -f experiments/results/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
      case $arm in
        stock)    ARGS="--mrm-off --method ours";;
        ours)     ARGS="--method ours";;
        baseline) ARGS="--method baseline";;
      esac
      NAME="enc-$arm-$f-$(echo $v | tr ':' '_')-r$rep"
      echo "$(date '+%F %T') $NAME free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG
      CASE_TAG="$NAME" HAZARD="ped=5:8:2.5" HAZARD_NOREC=1 WALKER_SEED=$((12+rep)) FAULT_SEED=$((12+rep)) \
        experiments/case_video.sh "$NAME" $ARGS --npc def --t 25 --fault "$f" --sev-value "$v" --rep "$rep" 2>&1 | grep -E "^VIDEO|^\[live\]|Traceback" | tee -a $LOG
      echo "$f $v $arm $rep" >> $DONE
      docker exec aw_carla_leaderboard_0916 bash -lc "rm -rf /home/taewook/autoware_carla_leaderboard/experiments/results/pvid_*" 2>/dev/null   # 혹시 남은 자체 녹화 정리
    done
  done
done
kill $INH 2>/dev/null
echo "$(date '+%F %T') encounter block done" | tee -a $LOG
