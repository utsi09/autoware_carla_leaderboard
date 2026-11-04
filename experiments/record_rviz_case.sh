#!/usr/bin/env bash
# 디펜스 영상용: 고장 케이스 하나를 RViz 켜고 돌리면서 화면을 녹화한다.
#   사용: experiments/record_rviz_case.sh <fault> <sev-value> [초(기본 300)] [출력이름]
#   예:   experiments/record_rviz_case.sh lso 0.07:150 300 lso_high
# 결과: doc/videos/<이름>.mp4 (원본) 와 <이름>_x4.mp4 (4배속, 디펜스용)
# 러너는 --mrm-off --eagleye 로 돌고(감시기 점수는 뜸, 개입 없음), rviz:=true 로 Autoware 를 띄운다.
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
FAULT=$1; SEV=$2; DUR=${3:-300}; NAME=${4:-${FAULT}_$(echo $SEV | tr ':' '_')}
REP=${REP:-0}; T=${T:-20}; NPC=${NPC:-def}   # env 로 시드(rep)·주입 시점·교통 바꿀 수 있음
OUT=doc/videos; mkdir -p $OUT
export DISPLAY=${DISPLAY:-:0}
# 주 모니터(HDMI-0 3840x2160, 가상화면 오프셋 +2160,+1680)만 잡고 1920x1080 으로 줄여 저장
GRAB_SIZE=3840x2160; GRAB_OFF=2160,1680

# 1) 케이스 시작 (rviz 켜기: 러너의 rviz:=false 를 덮어쓴다)
RVIZ_ON=1 RVIZ_CFG=/home/taewook/autoware_awcl/autoware/src/launcher/autoware_launch/autoware_launch/rviz/autoware_video.rviz python3 -u experiments/experiment_runner.py --record --method ours --npc "$NPC" --t "$T" \
  --no-log-archive --fault "$FAULT" --sev-value "$SEV" --rep "$REP" > experiments/results/video_${NAME}.log 2>&1 &
RPID=$!
# 2) 리더보드가 "이번 케이스"로 새로 뜬 뒤(러너 로그), 차가 출발(timer armed)할 때까지 기다렸다가 녹화 시작
#    (leaderboard.log 는 이전 케이스 파일이 남아 있어 바로 grep 하면 안 된다)
for i in $(seq 1 300); do grep -q "start leaderboard" experiments/results/video_${NAME}.log 2>/dev/null && break; sleep 1; done
sleep 3
for i in $(seq 1 240); do grep -aq "timer armed" experiments/results/leaderboard.log 2>/dev/null && break; sleep 1; done
sleep 1
# RViz 창 ID 를 찾아 그 창만 잡는다 (-window_id: 다른 창이 위에 있어도 RViz 내용만 녹화. 컴포지터 덕).
# 못 찾으면 주 모니터 전체 영역으로 대체.
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
if [ -n "$WID" ]; then
  echo "recording up to ${DUR}s, window id $WID -> $OUT/${NAME}.mp4"
  ffmpeg -hide_banner -loglevel error -y -f x11grab -framerate 15 -window_id "$WID" -i "$DISPLAY" -t "$DUR" \
    -vf "scale=1920:-2" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$OUT/${NAME}.mp4" &
else
  echo "rviz window not found; recording primary monitor region"
  ffmpeg -hide_banner -loglevel error -y -f x11grab -framerate 15 -video_size 3840x2160 -i "${DISPLAY}+2160,1680" -t "$DUR" \
    -vf "scale=1920:-2" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$OUT/${NAME}.mp4" &
fi
FPID=$!
# 케이스(러너)가 먼저 끝나면 녹화도 멈춘다 (정지 후 빈 화면을 5분 내내 찍지 않게); 끝난 뒤 8 s 여유
while kill -0 $FPID 2>/dev/null; do
  if ! kill -0 $RPID 2>/dev/null; then sleep 8; kill -INT $FPID 2>/dev/null; break; fi
  sleep 2
done
wait $FPID 2>/dev/null
# 3) 케이스 종료
kill -INT $RPID 2>/dev/null; for i in $(seq 1 40); do kill -0 $RPID 2>/dev/null || break; sleep 2; done
kill -9 $RPID 2>/dev/null || true
# 4) 4배속 판
ffmpeg -hide_banner -loglevel error -y -i "$OUT/${NAME}.mp4" -filter:v "setpts=0.25*PTS" -an -c:v libx264 -crf 23 "$OUT/${NAME}_x4.mp4"
ls -la "$OUT/${NAME}.mp4" "$OUT/${NAME}_x4.mp4"
