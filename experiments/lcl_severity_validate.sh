#!/usr/bin/env bash
# [2026-11-07] lcl 세기 추정 검증: 7개 강우 수준 × 15회(라운드로빈, rep 마다 전 수준 한 바퀴), 케이스별 cdr 원본 로그 보관.
# 2단계 세기 추정(CUSUM 감지 뒤 원거리 잔존율·근거리 클러터)을 8월에 안 본 수준에서 평가한다. 모니터·정책은 안 바꾼다.
# 체인 전체가 끝난 뒤("EVERYTHING DONE") 시작. 완료 셀: results/lcl_raw_done.txt (실패 셀은 안 적어 재시작 시 다시 돔).
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; RES=experiments/results; DONE=$RES/lcl_raw_done.txt; touch $DONE
until grep -q "chain: final top-up done — EVERYTHING DONE" $LOG; do sleep 60; done
echo "$(date '+%F %T') chain: starting lcl severity validation (105)" | tee -a $LOG
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "lcl severity validation" sleep 100000 >/dev/null 2>&1 & INH=$!
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LV=(15:2750 2:1100 40:5900 10:2100 1:1000 5:1500 25:4000)
for rep in $(seq 0 14); do
  for v in "${LV[@]}"; do
    grep -qx "$v $rep" $DONE && continue
    [ -f $RES/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
    echo "$(date '+%F %T') lclraw $v rep=$rep free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG
    OUT=$($R --fault lcl --sev-value "$v" --rep "$rep" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback")
    echo "$OUT" | tee -a $LOG
    D=$RES/case_logs/lclraw_${v/:/_}_r$rep; mkdir -p "$D"; gzip -c $RES/cdr.log > "$D/cdr.log.gz"; echo "$OUT" | grep "^\[live\]" > "$D/live.txt"
    echo "$OUT" | grep -qE "CARLA_DIED|INTERRUPTED|Traceback" || [ -z "$OUT" ] || echo "$v $rep" >> $DONE
  done
done
kill $INH 2>/dev/null
echo "$(date '+%F %T') chain: lcl severity validation done" | tee -a $LOG
