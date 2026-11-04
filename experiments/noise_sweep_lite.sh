#!/usr/bin/env bash
# noise-capability 스윕 경량판 (2026-11-04 결정): 순정 매트릭스가 mid/high 두 단계를 45건씩 주므로 그 사이 단계만 3회씩.
#   lso T(폭 90°) 7단 × 3, lcl 5단 × 3, imn 4단 × 3 = 48회 ≈ 4.5 h. gn·imb·폭분리는 뺌(순정/항법확장 블록이 대체).
# 완료 (fault,value,rep) 는 results/rr_done.txt 공용. 라운드로빈: rep 마다 lso→lcl→imn 한 수준씩.
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LOG=experiments/results/noise_sweep_batch.log
DONE=experiments/results/rr_done.txt
touch $DONE
LSO=(0.6:90 0.45:90 0.25:90 0.2:90 0.15:90 0.12:90 0.07:90)
LCL=(10:2100 2:1100 15:2750 40:5900 1:1000)
IMN=(0.25 1.0 0.1 0.05)
one() {  # fault value rep
  local f=$1 v=$2 r=$3
  grep -qx "$f $v $r" $DONE && return
  [ -f experiments/results/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
  echo "$(date '+%F %T') $f $v rep$r  free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG
  $R --fault "$f" --sev-value "$v" --rep "$r" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback" | tee -a $LOG
  echo "$f $v $r" >> $DONE
}
for r in 0 1 2; do
  one nf nf $r
  for ((i=0; i<${#LSO[@]}; i++)); do
    one lso "${LSO[$i]}" $r
    [ $i -lt ${#LCL[@]} ] && one lcl "${LCL[$i]}" $r
    [ $i -lt ${#IMN[@]} ] && one imn "${IMN[$i]}" $r
  done
done
echo "$(date '+%F %T') sweep-lite done" | tee -a $LOG
