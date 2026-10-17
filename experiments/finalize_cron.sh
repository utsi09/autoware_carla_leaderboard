#!/bin/bash
# cf v7 완료 시 v19 마무리 1회 실행 (멱등)
D=/home/taewook/autoware_carla_leaderboard/doc/thesis_build_v19
[ -f "$D/FINALIZE_OK.marker" ] && { crontab -l | grep -v finalize_cron | crontab -; exit 0; }
grep -q "cf v7 done" /home/taewook/autoware_carla_leaderboard/experiments/results/hardfast_v7_cf_0823.log 2>/dev/null || exit 0
[ -f "$D/FINALIZE_RUNNING" ] && exit 0
touch "$D/FINALIZE_RUNNING"
export HOME=/home/taewook
cd "$D"
python3 finalize_v19.py > "$D/finalize.log" 2>&1
rm -f "$D/FINALIZE_RUNNING"
