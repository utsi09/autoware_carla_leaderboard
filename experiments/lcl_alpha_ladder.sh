#!/usr/bin/env bash
# [2026-11-09] lcl 세기 재보정 사다리(v5b). 11/08 23:32 1차 보정 관문 실패(원거리·근거리 점수 비 f,n 이 장면 의존 → G2b·G3)
# 후, 모니터의 강수 세기 특징을 강도-거리 감쇠 계수 α̂(Beer-Lambert, 시작 시 맑은 기준선 대비)로 바꾸고(lidar_quality_check.hpp v5b)
# 새 모니터로 7수준 × 4회(rep 40-43)를 돌려 cdr 로그에 α̂ 를 남긴다. 임시 계수(Goodin 이론값) 는 로그용일 뿐, 보정이 확정한다.
# 사전 지정: 학습 rep 40-41, 시험 rep 42-43, 적합·관문 규칙은 1차와 동일(analysis/lcl_severity_calib.py).
# 옆에서 2 Hz 전방 원시 점군(라이다만)도 저장해 오프라인 α̂ 와 온라인 로그를 교차검증한다(xcheck).
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log; RES=experiments/results; X=$RES/retune_ext; DONE=$RES/lcl_raw_done.txt; touch $DONE
export CDR_LCL_SEV_CFG=$(realpath $X/lcl_sev_cfg_prov.txt)
export DISPLAY=:0
gnome-session-inhibit --inhibit idle:suspend --reason "lcl alpha ladder" sleep 100000 >/dev/null 2>&1 & INH=$!
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LV=(15:2750 2:1100 40:5900 10:2100 1:1000 5:1500 25:4000)
echo "$(date '+%F %T') chain: lcl alpha ladder start (28 cells, cfg $CDR_LCL_SEV_CFG)" | tee -a $LOG
for pass in 1 2; do
for rep in 40 41 42 43; do
  for v in "${LV[@]}"; do
    grep -qx "$v $rep" $DONE && continue
    [ -f $RES/DISK_FULL ] && { echo "DISK_FULL — stop" | tee -a $LOG; exit 1; }
    free=$(df -BG --output=avail /home | tail -1 | tr -dc 0-9)
    if [ "$free" -lt 18 ]; then echo "$(date '+%F %T') ladder: free=${free}G < 18G — stop" | tee -a $LOG; exit 1; fi
    OUTD=$RES/raw_vision/lad-lcl-${v/:/_}-r$rep; rm -rf "$OUTD"; mkdir -p "$OUTD"
    echo "$(date '+%F %T') lclraw $v rep=$rep free=${free}G" | tee -a $LOG
    ( set +u   # ROS setup.bash 는 nounset 아래서 죽는다
      export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
      source /opt/ros/humble/setup.bash
      exec python3 experiments/vision_raw_recorder.py --out "$OUTD" --hz 2.0 --no-cam ) > "$OUTD/recorder.log" 2>&1 &
    RP=$!
    OUT=$($R --fault lcl --sev-value "$v" --rep "$rep" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback")
    kill -TERM $RP 2>/dev/null; wait $RP 2>/dev/null
    echo "$OUT" | tee -a $LOG
    D=$RES/case_logs/lclraw_${v/:/_}_r$rep; mkdir -p "$D"; gzip -c $RES/cdr.log > "$D/cdr.log.gz"; echo "$OUT" | grep "^\[live\]" > "$D/live.txt"
    echo "$OUT" | grep -qE "CARLA_DIED|INTERRUPTED|SETUP_FAIL|Traceback" || [ -z "$OUT" ] || echo "$v $rep" >> $DONE
  done
done
done
kill $INH 2>/dev/null
echo "$(date '+%F %T') chain: lcl alpha ladder done ($(grep -cE ' 4[0-3]$' $DONE)/28)" | tee -a $LOG
