#!/usr/bin/env bash
# [2026-11-08] 비전 블록 후처리 (CPU 전용, nice 19; 재튜닝 주행과 병행 가능):
#   map.csv 의 표준 bag 태그 → baseline_fdi 캐시/진단/통계(제안 재생·B0·주입 시각) → 라이다 특징(WON/ZH)
#   → LEE CNN 학습(nf 짝수 rep)·추론 → report.md / cases.csv
cd /home/taewook/autoware_carla_leaderboard/experiments
source /opt/ros/humble/setup.bash; source /home/taewook/autoware_awcl/autoware/install/setup.bash
set -uo pipefail   # ROS setup 뒤에 켠다(nounset 아래서 setup.bash 가 죽음)
X=results/raw_vision; LOG=$X/post.log
tail -n +2 $X/map.csv | awk -F, '$4!="" && $6!~/CARLA_DIED|INTERRUPTED|SETUP_FAIL|NONE/ {print $4}' | sort -u > $X/tags.txt
echo "$(date '+%F %T') post: $(wc -l < $X/tags.txt) tags" | tee -a $LOG
nice -n 19 python3 analysis/baseline_fdi_extract.py --tags-file $X/tags.txt --workers 2 2>&1 | grep -E "FAIL|done|cached|ok" | tail -4 | tee -a $LOG
nice -n 19 python3 analysis/baseline_fdi_diag.py --tags-file $X/tags.txt --workers 2 2>&1 | tail -2 | tee -a $LOG
while read -r t; do nice -n 19 python3 analysis/baseline_fdi_eval.py --stats --only "$t" --workers 1 2>&1 | grep -E "ok|FAIL|cached" | tail -1; done < $X/tags.txt | tee -a $LOG
nice -n 19 python3 analysis/vision_fdi_eval.py --features --workers 4 2>&1 | tee -a $LOG
LEE_THREADS=${LEE_THREADS:-8} nice -n 19 python3 analysis/vision_fdi_eval.py --train-lee --epochs ${LEE_EPOCHS:-6} 2>&1 | tee -a $LOG
LEE_THREADS=${LEE_THREADS:-8} nice -n 19 python3 analysis/vision_fdi_eval.py --infer-lee 2>&1 | tee -a $LOG
nice -n 19 python3 analysis/vision_fdi_eval.py --report 2>&1 | tail -30 | tee -a $LOG
echo "$(date '+%F %T') post: done" | tee -a $LOG
