#!/usr/bin/env bash
# noise-capability 스윕 배치 (계획: fs_failsafe/docs/followup_noise_capability_plan.md 3절)
# 우선순위 순서. 중간에 끊겨도 앞 블록만으로 성립.  사용: experiments/noise_sweep_batch.sh [시작블록번호]
# 디스크: 케이스마다 러너가 15 GB 미만이면 멈추고 results/DISK_FULL 을 남긴다.
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LOG=experiments/results/noise_sweep_batch.log
START=${1:-1}
run() {  # block fault reps values...
  local blk=$1 fault=$2 reps=$3; shift 3
  [ "$blk" -lt "$START" ] && return
  for v in "$@"; do
    [ -f experiments/results/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
    echo "$(date '+%F %T') block $blk $fault $v x$reps  free=$(df --output=avail -BG /home | tail -1)" | tee -a $LOG
    if [ "$fault" = nf ]; then
      $R --fault nf --sev-value nf --reps "$reps" 2>&1 | tail -3 | tee -a $LOG
    else
      $R --fault "$fault" --sev-value "$v" --reps "$reps" 2>&1 | tail -3 | tee -a $LOG
    fi
  done
}
# 1 기준선
run 1 nf  5 -
# 2 lso 투과율 (폭 90)
run 2 lso 5 0.8:90 0.6:90 0.45:90 0.33:90 0.25:90 0.2:90 0.15:90 0.12:90 0.07:90
# 3 lcl 강우
run 3 lcl 5 1:1000 2:1100 5:1500 10:2100 15:2750 25:4000 40:5900
# 4 imn 자이로 노이즈
run 4 imn 5 0.05 0.1 0.25 0.5 1.0 1.5
# 5 gn (참고)
run 5 gn  3 0.5 1.0 2.5 5.0
# 6 lso 폭 효과
run 6 lso 5 0.33:150 0.07:150
# 7 imb
run 7 imb 3 0.1 0.3 1.0
echo "$(date '+%F %T') batch done" | tee -a $LOG
