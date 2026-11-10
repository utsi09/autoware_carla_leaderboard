#!/usr/bin/env bash
# [2026-11-10 23:40] 카메라 잡음 사다리 보강: σ=15, 7 을 채우기 B 와 같은 프로토콜(순정 감시기만, def 교통, t=10 주입, 수준당 10런)로 추가.
#   이유: (d) 아래 행(신호등 인식 성공률)이 5:0.9 → 10:0.3 → 20:0 으로 급락해 전이 구간(5–20)에 점이 없고, 캠페인 mid(σ15)는 27 s 주입·교통 3종이라 섞을 수 없음.
#   끝나면 cam_scores(bag 점수)·stock_outcomes(결말) 갱신 → F1 EN/KR 재생성 → final_fig 복사 → 깃 커밋·푸시.
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
R="python3 experiments/experiment_runner.py --mrm-off --record --method ours --npc def --t 10 --no-log-archive"
LOG=experiments/results/noise_sweep_batch.log; LOG2=experiments/results/stock_matrix.log
DONE=experiments/results/cn_fill2_done.txt; touch $DONE
echo "$(date '+%F %T') chain: cn fill σ15/σ7 start (20 cells)" | tee -a $LOG $LOG2
run_cell () {  # value rep
  local v=$1 rep=$2 key="cn $1 $2"
  grep -qx "$key" $DONE && return 0
  [ -f experiments/results/DISK_FULL ] && { echo "$(date '+%F %T') DISK_FULL — stop" | tee -a $LOG $LOG2; exit 1; }
  echo "$(date '+%F %T') fill cn $v rep=$rep free=$(df --output=avail -BG /home | tail -1 | tr -d ' ')" | tee -a $LOG $LOG2
  local OUT; OUT=$($R --fault cn --sev-value "$v" --rep "$rep" 2>&1 | grep -E "^\[runner\] result|^\[live\]|Traceback")
  echo "$OUT" | tee -a $LOG $LOG2
  if echo "$OUT" | grep -qE "CARLA_DIED|INTERRUPTED|SETUP_FAIL|Traceback" || [ -z "$OUT" ]; then return 0; fi
  echo "$key" >> $DONE
}
for pass in 1 2; do
  for rep in 0 1 2 3 4 5 6 7 8 9; do run_cell 15 $rep; done
  for rep in 0 1 2 3 4 5 6 7 8 9; do run_cell 7 $rep; done
done
echo "$(date '+%F %T') chain: cn fill σ15/σ7 runs done ($(wc -l < $DONE)/20) — post-processing" | tee -a $LOG $LOG2
cd experiments
TAGS=$(for t in $(ls results/live | grep -E "^stock-cn-(15|7)-def-" | sed 's/.csv$//' | sort); do grep -q "^$t," results/derived/cam_scores.csv || echo $t; done | tr '\n' ' ')
( set +u; source /opt/ros/humble/setup.bash >/dev/null 2>&1; source /home/taewook/fs_ws/install/setup.bash >/dev/null 2>&1
  [ -n "$TAGS" ] && nice -n 10 python3 analysis/score_medians.py results/derived/cam_scores.csv $TAGS 2>&1 | grep -vE "^\[" | tail -2 )
cp results/stock_outcomes.csv results/derived/stock_outcomes_before_cnfill2.csv
OT=$(for t in $(ls results/gt | grep -E "^stock-cn-(15|7)-def-.*[0-9]\.csv$" | sed 's/.csv$//' | sort); do grep -q "^$t," results/stock_outcomes.csv || echo $t; done | tr '\n' ' ')
if [ -n "$OT" ]; then
  ( set +u; source /opt/ros/humble/setup.bash >/dev/null 2>&1; source /home/taewook/autoware_awcl/autoware/install/setup.bash >/dev/null 2>&1
    nice -n 10 python3 analysis/stock_freeze.py $OT > results/derived/stock_freeze_cnfill2.md 2> results/derived/stock_freeze_cnfill2.err )
  python3 - <<'PY'
import csv
new = list(csv.DictReader(open("results/stock_outcomes.csv"))); old = list(csv.DictReader(open("results/derived/stock_outcomes_before_cnfill2.csv")))
keys = list(old[0].keys()) + [k for k in (new[0].keys() if new else []) if k not in old[0]]; tags = {r["tag"] for r in old}
merged = old + [r for r in new if r["tag"] not in tags]
with open("results/stock_outcomes.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(merged)
print("stock_outcomes merged", len(old), "+", len(merged) - len(old))
PY
fi
python3 analysis/fig_noise_sweep_v5b_en.py 2>&1 | grep -E "^\s+cn " | tee -a $LOG2
python3 analysis/fig_noise_sweep_v5b.py >/dev/null 2>&1
cp results/figs/fig_noise_sweep_v5b_en.png results/figs/fig_noise_sweep_v5b_en.pdf results/figs/fig_noise_sweep_v5b.png results/figs/fig_noise_sweep_v5b.pdf final_fig/
cp results/stock_outcomes.csv results/derived/cam_scores.csv final_fig/data/
cd /home/taewook/autoware_carla_leaderboard
git add -f experiments/final_fig experiments/results/derived experiments/results/stock_outcomes.csv experiments/results/noise_sweep_batch.log experiments/results/figs experiments/results/cn_fill2_done.txt experiments/cn_fill_15_7.sh >/dev/null 2>&1
git -c core.pager=cat commit -q -m "cn ladder: add sigma 15 and 7 (10 runs each, same protocol), regenerate severity sweep figure

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019ZYs74g5t74ShjhcFaG6F6" && timeout 600 git push mine v3-parking-freeze 2>&1 | tail -1 | tee -a experiments/results/stock_matrix.log
echo "$(date '+%F %T') chain: cn fill σ15/σ7 done + pushed" | tee -a experiments/results/noise_sweep_batch.log experiments/results/stock_matrix.log
