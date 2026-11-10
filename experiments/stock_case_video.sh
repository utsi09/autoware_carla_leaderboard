#!/usr/bin/env bash
# 순정 매트릭스 케이스 하나를 RViz 켜고 돌리면서 RViz 창을 녹화 → 4배속 작은 mp4 만 남김(원본 삭제).
#   사용: experiments/stock_case_video.sh <fault> <sev> <npc> <rep>
# 출력: results/videos/stock-<fault>-<sev>-<npc>-r<rep>_x4.mp4 와 "VIDEO <path> <MB>" 줄.
cd /home/taewook/autoware_carla_leaderboard
F=$1; S=$2; N=$3; REP=$4
NAME="stock-$F-$S-$N-r$REP"
R=experiments/results; V=$R/videos; mkdir -p $V
export DISPLAY=:0
RVIZ_ON=1 RVIZ_CFG=/home/taewook/autoware_awcl/autoware/src/launcher/autoware_launch/autoware_launch/rviz/autoware_video.rviz \
python3 -u experiments/experiment_runner.py --mrm-off --record --method ours --reps 15 --no-log-archive \
  --fault "$F" --sev "$S" --npc "$N" --rep "$REP" > $R/run_$NAME.log 2>&1 &
RPID=$!
# 리더보드가 이번 케이스로 뜨고 차가 출발하면 녹화 시작
for i in $(seq 1 400); do grep -q "start leaderboard" $R/run_$NAME.log 2>/dev/null && break; kill -0 $RPID 2>/dev/null || break; sleep 1; done
sleep 3
for i in $(seq 1 300); do grep -aq "timer armed" $R/leaderboard.log 2>/dev/null && break; kill -0 $RPID 2>/dev/null || break; sleep 1; done
WID=$(python3 - <<'PY'
import os; os.environ.setdefault("DISPLAY", ":0")
from Xlib import display
d=display.Display(":0"); root=d.screen().root
def find(w):
    try:
        for c in w.query_tree().children:
            try: n=c.get_wm_name()
            except Exception: n=None
            if n and "RViz" in n: return c
            r=find(c)
            if r: return r
    except Exception: pass
w=find(root); print(w.id if w else "")
PY
)
FPID=""
if [ -n "$WID" ] && kill -0 $RPID 2>/dev/null; then
  # [2026-11-06] 창 id 캡처는 RViz 가 창을 다시 만들면 옛 id 가 검은 화면만 내보냄(검은 녹화 11건).
  #   창의 화면 영역(좌표·크기)을 잡아 영역 캡처로 바꿈; 영역을 못 읽으면 예전 방식.
  # [2026-11-09] RViz 창을 오른쪽 모니터(3840x2160 @ +2160+1680) 우측으로 옮기고 항상-위로: 터미널이 덮어 터미널이 녹화되던 사고 방지
  python3 experiments/rviz_place.py "$WID" 3840 1680 2>/dev/null; sleep 1.5
  GEO=$(xwininfo -id "$WID" 2>/dev/null | awk '/Absolute upper-left X/{x=$NF} /Absolute upper-left Y/{y=$NF} /^ *Width/{w=$NF} /^ *Height/{h=$NF} END{if(w>0&&h>0) printf "%dx%d %d,%d", w-(w%2), h-(h%2), x, y}')
  if [ -n "$GEO" ]; then read GSZ GOFF <<<"$GEO"; GRAB=(-video_size "$GSZ" -i "$DISPLAY+$GOFF"); else GRAB=(-window_id "$WID" -i "$DISPLAY"); fi
  ffmpeg -hide_banner -loglevel error -y -f x11grab -framerate 10 "${GRAB[@]}" -t 900 \
    -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p "$V/$NAME.mp4" &
  FPID=$!
fi
wait $RPID
RES=$(grep -a -m1 "\[runner\] result" $R/run_$NAME.log | sed 's/.*result: //')
if [ -n "$FPID" ]; then sleep 2; kill -INT $FPID 2>/dev/null || true; wait $FPID 2>/dev/null || true; fi   # [2026-11-06] 캡처 ffmpeg 가 먼저 죽었어도(RViz 종료) set -e 로 스크립트가 끊기지 않게
if [ -s "$V/$NAME.mp4" ]; then
  ffmpeg -hide_banner -loglevel error -y -i "$V/$NAME.mp4" -filter:v "setpts=0.25*PTS" -r 15 -an -c:v libx264 -crf 28 "$V/${NAME}_x4.mp4" && rm -f "$V/$NAME.mp4"
  echo "VIDEO $V/${NAME}_x4.mp4 $(du -m "$V/${NAME}_x4.mp4" | cut -f1)MB result=$RES"
else
  echo "VIDEO none result=$RES"
fi
grep -a "^\[live\]" $R/run_$NAME.log
