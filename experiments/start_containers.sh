#!/usr/bin/env bash
# 실험용 컨테이너 두 개를 띄운다 (rocker 가 만든 파생 이미지를 그대로 사용, --rm 없이 detach).
# rocker 는 --rm 으로 띄우므로 터미널/재부팅 때 컨테이너가 사라진다. 러너는 docker exec 만 하므로
# 이 스크립트로 한 번 띄워 두면 된다.  사용: experiments/start_containers.sh
set -euo pipefail
AW_IMG=awcl_exp/autoware:rocker      # rocker --image-name ... autoware_awcl_with_models:v1
LB_IMG=awcl_exp/leaderboard:rocker   # rocker --image-name ... tumgeka/autoware_carla_leaderboard:0.9.16
XAUTH=/tmp/.docker_exp.xauth
export DISPLAY="${DISPLAY:-:0}"
touch "$XAUTH"
if command -v xauth >/dev/null; then
  xauth nlist "$DISPLAY" 2>/dev/null | sed -e 's/^..../ffff/' | xauth -f "$XAUTH" nmerge - 2>/dev/null || true
fi
common=(-e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp -e ROS_DOMAIN_ID=11
        -e CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
        --network host --gpus all --privileged
        -v /home/taewook/cyclone_localhost.xml:/home/taewook/cyclone_localhost.xml
        -e DISPLAY -e TERM -e QT_X11_NO_MITSHM=1
        -e XAUTHORITY="$XAUTH" -v "$XAUTH:$XAUTH"
        -v /tmp/.X11-unix:/tmp/.X11-unix -v /etc/localtime:/etc/localtime:ro)
start() {  # name image volumes...
  local name=$1 img=$2; shift 2
  if docker ps --format '{{.Names}}' | grep -qx "$name"; then echo "$name: 이미 실행 중"; return; fi
  if docker ps -a --format '{{.Names}}' | grep -qx "$name"; then docker start "$name" >/dev/null; echo "$name: 재시작"; return; fi
  docker run -dit --name "$name" "${common[@]}" "$@" "$img" bash >/dev/null
  echo "$name: 생성"
}
start autoware_awcl_01 "$AW_IMG" \
  -v /home/taewook/autoware_awcl/autoware:/home/taewook/autoware_awcl/autoware \
  -v /home/taewook/autoware_data:/home/aw/autoware_data \
  -v /home/taewook/awcl_maps:/home/taewook/awcl_maps
start aw_carla_leaderboard_0916 "$LB_IMG" \
  -v /home/taewook/autoware_carla_leaderboard:/home/taewook/autoware_carla_leaderboard
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E "autoware_awcl_01|aw_carla_leaderboard_0916"
