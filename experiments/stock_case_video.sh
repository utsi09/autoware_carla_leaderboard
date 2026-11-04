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
  ffmpeg -hide_banner -loglevel error -y -f x11grab -framerate 10 -window_id "$WID" -i "$DISPLAY" -t 900 \
    -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p "$V/$NAME.mp4" &
  FPID=$!
fi
wait $RPID
RES=$(grep -a -m1 "\[runner\] result" $R/run_$NAME.log | sed 's/.*result: //')
if [ -n "$FPID" ]; then sleep 2; kill -INT $FPID 2>/dev/null; wait $FPID 2>/dev/null; fi
if [ -s "$V/$NAME.mp4" ]; then
  ffmpeg -hide_banner -loglevel error -y -i "$V/$NAME.mp4" -filter:v "setpts=0.25*PTS" -r 15 -an -c:v libx264 -crf 28 "$V/${NAME}_x4.mp4" && rm -f "$V/$NAME.mp4"
  echo "VIDEO $V/${NAME}_x4.mp4 $(du -m "$V/${NAME}_x4.mp4" | cut -f1)MB result=$RES"
else
  echo "VIDEO none result=$RES"
fi
grep -a "^\[live\]" $R/run_$NAME.log
