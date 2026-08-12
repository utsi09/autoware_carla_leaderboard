#!/bin/bash
# 체인(pid $1) 종료를 기다렸다가 Arm C 실행
while kill -0 "$1" 2>/dev/null; do sleep 300; done
bash /home/taewook/autoware_carla_leaderboard/experiments/launch_v3_armC.sh
