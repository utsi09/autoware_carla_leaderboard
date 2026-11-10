#!/usr/bin/env bash
# noise-capability 스윕, 라운드로빈 순서: rep 마다 nf → lso → lcl → imn → gn → imb 를 한 수준씩 번갈아.
# 같은 조건을 연속으로 돌리지 않는다. 완료한 (fault,value,rep) 는 results/rr_done.txt 에 적어 재시작 시 건너뛴다.
# 사용: experiments/noise_sweep_rr.sh
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LOG=experiments/results/noise_sweep_batch.log
DONE=experiments/results/rr_done.txt
touch $DONE
# 수준 순서: 핵심(mid/high) 먼저
LSO=(0.33:90 0.07:90 0.2:90 0.6:90 0.45:90 0.25:90 0.15:90 0.12:90 0.8:90 0.33:150 0.07:150)
LCL=(5:1500 25:4000 10:2100 2:1100 15:2750 40:5900 1:1000)
IMN=(0.5 1.5 0.25 1.0 0.1 0.05)
GN=(1.0 2.5 0.5 5.0)      # rep 0-2 만
IMB=(0.3 1.0 0.1)         # rep 0-2 만
one() {  # fault value rep
  local f=$1 v=$2 r=$3
  grep -qx "$f $v $r" $DONE && return
  [ -f experiments/results/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
  echo "$(date '+%F %T') $f $v rep$r  free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG
  $R --fault "$f" --sev-value "$v" --rep "$r" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback" | tee -a $LOG
  echo "$f $v $r" >> $DONE
}
for r in 0 1 2 3 4; do
  n=$(( ${#LSO[@]} > ${#LCL[@]} ? ${#LSO[@]} : ${#LCL[@]} ))
  one nf nf $r
  for ((i=0; i<n; i++)); do
    [ $i -lt ${#LSO[@]} ] && one lso "${LSO[$i]}" $r
    [ $i -lt ${#LCL[@]} ] && one lcl "${LCL[$i]}" $r
    [ $i -lt ${#IMN[@]} ] && one imn "${IMN[$i]}" $r
    if [ $r -lt 3 ]; then
      [ $i -lt ${#GN[@]} ]  && one gn  "${GN[$i]}"  $r
      [ $i -lt ${#IMB[@]} ] && one imb "${IMB[$i]}" $r
    fi
  done
done
echo "$(date '+%F %T') rr batch done" | tee -a $LOG
