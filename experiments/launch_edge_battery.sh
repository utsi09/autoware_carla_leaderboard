#!/bin/bash
# v4.9 엣지 케이스 배터리 (0815 사용자 승인: 1 보행자 / 2 정지 장애물 / 3 갓길 점유)
#
# ⚠ 실행 전제 (일요일, 본 체인 완료 후):
#   1) experiment_runner.py에 HAZARD env 통과 패치 적용 필요 — tl_relay 기동부 옆에:
#        hz = os.environ.get("HAZARD", "")
#        if hz:
#            mode, spec = hz.split("=", 1)
#            procs.docker_bg(LB_CONTAINER,
#                "cd /workspace/team_code && python3 experiments/hazard_injector.py "
#                f"--mode {mode} --spec {spec} --fault-t {case['t']}", "hazard")
#      + cleanup pats에 "hazard_injector" 추가. 적용 후 py_compile 검증 필수.
#   2) 스모크: HAZARD=ped=5:22:3 으로 nf 1케이스 — 보행자 스폰·회피 확인.
#
# 매트릭스: ped/obstacle × {stock(--mrm-off), ours} × {nf, cn mid, lso mid, lso high}
#           × 3 reps + shoulder × ours × 4폴트 × 3 reps  ≈ 60케이스 (~4.5 h)
# 갓길 점유 좌표(CARLA 프레임, AW의 y 부호 반전): 남측(-75,-5.3) 서측(-96.5,-30)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
LOG=experiments/results/edge_battery.log

run() {  # run <hazard> <method-flag...> <fault> <sev>
  local hz="$1"; shift
  HAZARD="$hz" python3 experiments/experiment_runner.py "$@" \
    --npc none --reps 3 >> $LOG 2>&1
}

for F in "nf mid" "cn mid" "lso mid" "lso high"; do
  set -- $F
  echo "===== EDGE ped $1 $2 ====="
  run "ped=5:22:3"      --method ours --fault $1 --sev $2
  run "ped=5:22:3"      --method ours --mrm-off --fault $1 --sev $2
  echo "===== EDGE obstacle $1 $2 ====="
  run "obstacle=5:40"   --method ours --fault $1 --sev $2
  run "obstacle=5:40"   --method ours --mrm-off --fault $1 --sev $2
done
for F in "cn mid" "cf mid" "gn mid" "lso high"; do
  set -- $F
  echo "===== EDGE shoulder $1 $2 ====="
  run "shoulder=-75:-5.3,-96.5:-30" --method ours --fault $1 --sev $2
done
echo EDGE_BATTERY_DONE
