#!/bin/bash
# speed-dose 인과 실험 배치 (사전등록: doc/speed_dose_plan_0827.md)
# 사용: speed_dose_batch.sh dev   -> D00 스모크 3런만
#       speed_dose_batch.sh       -> 본 캠페인 120런 (P1~P5, 이어달리기 가능)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
R=/home/taewook/autoware_carla_leaderboard/experiments/results
LOG=$R/speed_dose.log
PROG=$R/speed_dose_progress.csv
FT=25                       # 개발 단계 확정 후 동결 (plan 참조)
mkdir -p $R/videos_sd
[ -f $PROG ] || echo "tag,seed,cap,dist,attempt,adopted,first_v,outcome,tick" > $PROG

if pgrep -f "experiment_runner[.]py" > /dev/null; then
  echo "runner already active — abort" | tee -a $LOG; exit 1
fi

# 밴드 하한 = 캡-0.35: 속도 스무서가 외부 제한보다 ~0.2 낮게 추종하는 실측
# (D00 스모크: 캡 3.0 지속 구간 2.77) 반영. 세 밴드는 서로소 유지.
band() { case $1 in 4.2) echo "3.85x4.45";; 3.6) echo "3.25x3.75";; 3.0) echo "2.65x3.15";; esac; }

run_one() {  # SEED WS JIT FSEED WSEED CAP DIST
  local SEED=$1 WS=$2 JIT=$3 FSEED=$4 WSEED=$5 CAP=$6 D=$7
  local TAG=sd-${SEED}-c${CAP/./}-d${D}
  # 이미 채택(6열 adopted==1 — 정규식 ",1,"은 attempt 열과 오매칭했음)
  awk -F, -v t="$TAG" '$1==t && $6==1 {found=1} END{exit !found}' $PROG && return 0
  local A; A=$(grep -c "^${TAG}," $PROG)
  [ "$A" -ge 3 ] && { echo "$TAG retries exhausted" | tee -a $LOG; return 0; }
  local FREE; FREE=$(df --output=avail -BG / | tail -1 | tr -dc 0-9)
  [ "$FREE" -lt 20 ] && { echo "DISK_STOP free=${FREE}G" | tee -a $LOG; exit 2; }
  echo "===== $TAG attempt $((A+1)) $(date +%m%d_%H:%M) =====" | tee -a $LOG
  export FAULT_SEED=$FSEED WALKER_SEED=$WSEED CASE_TAG=$TAG
  export FAULT_TRACE=$R/ftrace_${TAG}.csv
  export DETECT_CAP=capability/localization FREEZE_TL=1
  MRM_MOVE_SPEED=$CAP HAZARD="ped=dist:${D}:s$(band $CAP):w${WS}:j${JIT}" \
    python3 experiments/experiment_runner.py --method ours --fault gn --sev mid \
    --npc none --reps 1 --t $FT >> $LOG 2>&1
  unset CASE_TAG
  local TICK V1 OK OUT
  TICK=$(ls -t $R/tick_${TAG}_*.csv 2>/dev/null | head -1)
  V1=""; OK=0
  if [ -n "$TICK" ]; then
    V1=$(awk -F, 'NR==2{print $8}' "$TICK")
    OK=$(python3 - "$CAP" "$TICK" <<'PY'
import sys, csv, math
cap, tick = sys.argv[1], sys.argv[2]
b = {'4.2': (3.85, 4.45), '3.6': (3.25, 3.75), '3.0': (2.65, 3.15)}[cap]
try:
    rows = list(csv.DictReader(open(tick)))
except Exception:
    print(0); raise SystemExit
ok = 0
if len(rows) >= 3:
    v = float(rows[0]['ego_v'])
    ex, ey = float(rows[0]['ego_x']), float(rows[0]['ego_y'])
    px, py = float(rows[0]['ped_x']), float(rows[0]['ped_y'])
    j = min(len(rows) - 1, 10)               # 첫 ~0.5 s 이동 벡터 = 진행방향
    hx, hy = float(rows[j]['ego_x']) - ex, float(rows[j]['ego_y']) - ey
    dx, dy = px - ex, py - ey
    hn = math.hypot(hx, hy) or 1.0
    dn = math.hypot(dx, dy) or 1.0
    cos = (dx * hx + dy * hy) / (hn * dn)    # 보행자가 전방인가 (D01 역스폰 방지)
    ok = 1 if (b[0] - 0.15 <= v <= b[1] + 0.15 and cos > 0.6) else 0
print(ok)
PY
)
  fi
  OUT=$(tail -400 $LOG | grep -oE 'result: [A-Z_]+' | tail -1)
  echo "${TAG},${SEED},${CAP},${D},$((A+1)),${OK},${V1},${OUT#result: },${TICK##*/}" >> $PROG
  local PV
  for PV in $R/pvid_${TAG}_*/; do          # 프레임→mp4, PNG 즉시 삭제 (디스크 규율)
    [ -d "$PV" ] || continue
    ffmpeg -y -loglevel error -framerate 10 -pattern_type glob -i "${PV}f*.png" \
      -c:v libx264 -pix_fmt yuv420p $R/videos_sd/${TAG}_a$((A+1)).mp4 \
      && rm -rf "$PV"
  done
  [ "$OK" -eq 1 ] || run_one "$SEED" "$WS" "$JIT" "$FSEED" "$WSEED" "$CAP" "$D"
}

if [ "$1" = "dev" ]; then                   # D00 스모크: 본 분석 제외
  run_one D00 3.0 0.0 999 1999 4.2 8
  run_one D00 3.0 0.0 999 1999 3.0 8
  run_one D00 3.0 0.0 999 1999 3.6 7
  echo "SPEED_DOSE_DEV_DONE" | tee -a $LOG; exit 0
fi
if [ "$1" = "dev2" ]; then                  # D01: 캡 재발행 패치 검증 (본 분석 제외)
  run_one D01 3.0 0.0 998 1998 3.0 8
  run_one D01 3.0 0.0 998 1998 3.6 7
  run_one D01 3.0 0.0 998 1998 4.2 8
  echo "SPEED_DOSE_DEV2_DONE" | tee -a $LOG; exit 0
fi
if [ "$1" = "dev3" ]; then                  # D02: 안정판정+방향검사 검증 (본 분석 제외)
  run_one D02 3.0 0.0 997 1997 3.0 8
  run_one D02 3.0 0.0 997 1997 3.6 7
  run_one D02 3.0 0.0 997 1997 4.2 8
  echo "SPEED_DOSE_DEV3_DONE" | tee -a $LOG; exit 0
fi

mapfile -t ROWS < <(tail -n +2 experiments/seeds_speed_dose.csv)
# P1: 8m 1차 종결점 (4.2 vs 3.0, 시드 교차 순서)
i=0
for ROW in "${ROWS[@]}"; do
  IFS=, read -r SEED WS JIT FSEED WSEED <<< "$ROW"
  if [ $((i % 2)) -eq 0 ]; then ORD="4.2 3.0"; else ORD="3.0 4.2"; fi
  for CAP in $ORD; do run_one "$SEED" "$WS" "$JIT" "$FSEED" "$WSEED" "$CAP" 8; done
  i=$((i+1))
done
# P2: 8m x 3.6
for ROW in "${ROWS[@]}"; do
  IFS=, read -r SEED WS JIT FSEED WSEED <<< "$ROW"
  run_one "$SEED" "$WS" "$JIT" "$FSEED" "$WSEED" 3.6 8
done
# P3~P5: 7m -> 9m -> 6m, 시드별 속도 회전
for D in 7 9 6; do
  i=0
  for ROW in "${ROWS[@]}"; do
    IFS=, read -r SEED WS JIT FSEED WSEED <<< "$ROW"
    case $((i % 3)) in
      0) ORD="4.2 3.6 3.0";; 1) ORD="3.6 3.0 4.2";; 2) ORD="3.0 4.2 3.6";;
    esac
    for CAP in $ORD; do run_one "$SEED" "$WS" "$JIT" "$FSEED" "$WSEED" "$CAP" "$D"; done
    i=$((i+1))
  done
done
echo "SPEED_DOSE_BATCH_DONE $(date +%m%d_%H:%M)" | tee -a $LOG
