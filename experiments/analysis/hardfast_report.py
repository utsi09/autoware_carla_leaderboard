# -*- coding: utf-8 -*-
"""cf/lf 하드페일 고속경로 재수집(180케이스) 판정표.

사용자 지정 지표 (0822):
  fault×method별 — median / P95 / P99 / max 감지·판정 지연, >1.5 s 위반 x/n,
  MRM 도달 성공 x/n, FAST_PATH 발화 커버리지(원장 기준; 원장은 캠페인 도중
  5케이스 이후 도입되어 초기 케이스는 지연값으로만 판정).
사용법: python3 hardfast_report.py <cf_csv> <lf_csv>
"""
import csv, sys
import numpy as np

DEADLINE = 1.5
BAD = {"CARLA_DIED", "SETUP_FAIL", "TIMEOUT"}
MRM_OK = {"SHOULDER_SUCCESS", "PARKED_SUCCESS",
          "AW_COMFORTABLE_STOP_DONE", "AW_EMERGENCY_STOP_DONE",
          "DEFER_STOPPED(log)"}
LEDGER = "/home/taewook/autoware_carla_leaderboard/experiments/results/sup_events.log"


def q(d, p):
    return float(np.percentile(d, p)) if len(d) else float("nan")


def main(files):
    rows = []
    for f in files:
        rows += list(csv.DictReader(open(f)))
    try:
        fp_events = sum(1 for l in open(LEDGER) if " FAST_PATH " in l)
        dead_events = sum(1 for l in open(LEDGER) if " DEAD_SEEN " in l)
    except FileNotFoundError:
        fp_events = dead_events = -1

    print(f"{'구분':14s} {'n':>3s} {'med':>6s} {'P95':>6s} {'P99':>6s} "
          f"{'max':>6s} {'>1.5s':>7s} {'MRM성공':>8s}")
    for fault in ("cf", "lf"):
        for method in ("ours", "baseline"):
            sub = [r for r in rows if r["fault"] == fault
                   and r["method"] == method and r["outcome"] not in BAD]
            d = np.array([float(r["det_latency_s"]) for r in sub
                          if r.get("det_latency_s") not in ("", "nan", None)])
            viol = int((d > DEADLINE).sum())
            ok = sum(1 for r in sub if r["outcome"] in MRM_OK)
            print(f"{fault}-{method:9s} {len(sub):3d} {q(d,50):6.2f} "
                  f"{q(d,95):6.2f} {q(d,99):6.2f} {d.max() if len(d) else 0:6.2f} "
                  f"{viol:>3d}/{len(d):<3d} {ok:>3d}/{len(sub):<3d}")
    print(f"\n원장: FAST_PATH {fp_events}건, DEAD_SEEN {dead_events}건 "
          f"(원장 도입 후 케이스 기준 — 발화≠사망관측이면 원인 조사)")
    # 지연 분해 (원장): DEAD_SEEN -> 직후 TRANSITION 간격
    try:
        ev = [l.split() for l in open(LEDGER)]
        gaps = []
        for i, e in enumerate(ev):
            if e[1] == "DEAD_SEEN":
                for e2 in ev[i+1:i+8]:
                    if e2[1] == "TRANSITION":
                        gaps.append(float(e2[0]) - float(e[0]))
                        break
        if gaps:
            g = np.array(gaps)
            print(f"분해(사망 관측→상태 전이): 중앙 {np.median(g):.2f}s, "
                  f"max {g.max():.2f}s (n={len(g)}) — 앞단(주입→관측)은 "
                  f"신선도 마감+전파, 뒷단이 판정·전이 몫")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
