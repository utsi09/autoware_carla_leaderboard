#!/usr/bin/env python3
"""noise-capability 그림/표 (계획 8절).  입력: results/noise_capability_runs.csv (noise_capability.py 출력)

  python3 experiments/analysis/fig_noise_capability.py [--runs CSV] [--out DIR]

Fig (2x2): (a) lso: R_h, D_det vs T   (b) lcl: R_h, FP/s vs 강우
           (c) S_perc vs R_h 산점(실행=점, 0.7/0.3 선)   (d) imn: e_lat P95, S_loc vs σ
Table: 수준별 중앙값 + rep 수 (markdown)
"""
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results")

# 주입 모델이 예측하는 최대 검출 거리 (계획 3절 표)
MODEL_RANGE_LSO = {1.0: 100, 0.8: 100, 0.6: 93, 0.45: 72.5, 0.33: 55, 0.25: 42.5, 0.2: 34.5,
                   0.15: 26.5, 0.12: 21, 0.07: 12.5}
MODEL_RANGE_LCL = {0: 100, 1: 75.5, 2: 63, 5: 48, 10: 38, 15: 32.5, 25: 27, 40: 22.5}


def fnum(x):
    try:
        v = float(x)
        return v if not math.isnan(v) else None
    except (TypeError, ValueError):
        return None


def level_of(row):
    f, s = row["fault"], row["sev"]
    if f == "nf":
        return 0.0 if False else None
    try:
        return float(s.split("_")[0])
    except ValueError:
        return None


def load(path):
    rows = list(csv.DictReader(open(path, newline="")))
    by = defaultdict(list)       # (fault, level_str) -> rows
    for r in rows:
        by[(r["fault"], r["sev"])].append(r)
    return rows, by


def med(rows, key):
    v = [fnum(r.get(key)) for r in rows]
    v = [x for x in v if x is not None]
    return (float(np.median(v)), len(v)) if v else (None, 0)


def pick_score_key(rows):
    # perception 점수 열 이름은 cdr 상태명에 따라 S[...] 로 들어온다; 'percep' 포함 열 우선
    for k in rows[0].keys():
        if k.startswith("S[") and "percep" in k.lower():
            return k
    for k in rows[0].keys():
        if k.startswith("S["):
            return k
    return "S_lidar_front"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(RES / "noise_capability_runs.csv"))
    ap.add_argument("--out", default=str(RES / "figs"))
    a = ap.parse_args()
    rows, by = load(a.runs)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sk = pick_score_key(rows)
    nf = by.get(("nf", "nf"), [])
    base_Rh, _ = med(nf, "R_h") if nf else (None, 0)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 2, figsize=(11, 8.5))

    def series(fault, keys, lvl_filter=None):
        pts = defaultdict(lambda: defaultdict(list))
        for (f, s), rs in by.items():
            if f != fault:
                continue
            lv = level_of(rs[0])
            if lv is None or (lvl_filter and not lvl_filter(s)):
                continue
            for r in rs:
                for k in keys:
                    v = fnum(r.get(k))
                    if v is not None:
                        pts[k][lv].append(v)
        return pts

    # (a) lso: width 90 only
    p = series("lso", ["R_h", "D_det", sk], lambda s: s.endswith("_90"))
    a0 = ax[0, 0]
    for lv, vs in sorted(p["R_h"].items()):
        a0.scatter([lv] * len(vs), vs, color="C0", s=14, alpha=.6)
    xs = sorted(p["R_h"]); a0.plot(xs, [np.median(p["R_h"][x]) for x in xs], "C0-o", label="R_h (0-26 m recall)")
    if base_Rh is not None:
        a0.axhline(base_Rh, color="gray", ls=":", lw=1, label="fault-free R_h")
    a0.set_xlabel("cover transmittance T (lso, 90°)"); a0.set_ylabel("recall"); a0.set_ylim(0, 1.05)
    a0.invert_xaxis()
    a1 = a0.twinx()
    xs = sorted(p["D_det"]); a1.plot(xs, [np.median(p["D_det"][x]) for x in xs], "C3-s", label="D_det (m)")
    mx = sorted(MODEL_RANGE_LSO); a1.plot(mx, [MODEL_RANGE_LSO[x] for x in mx], color="C3", ls="--", lw=1, alpha=.5, label="model max range")
    a1.axhline(26, color="k", ls=":", lw=.8); a1.set_ylabel("first-detection distance [m]")
    a0.set_title("(a) LiDAR soiling sweep"); a0.legend(loc="lower left", fontsize=8); a1.legend(loc="lower right", fontsize=8)

    # (b) lcl
    p = series("lcl", ["R_h", "FP_s", sk])
    b0 = ax[0, 1]
    xs = sorted(p["R_h"])
    for lv, vs in sorted(p["R_h"].items()):
        b0.scatter([lv] * len(vs), vs, color="C0", s=14, alpha=.6)
    b0.plot(xs, [np.median(p["R_h"][x]) for x in xs], "C0-o", label="R_h")
    if base_Rh is not None:
        b0.axhline(base_Rh, color="gray", ls=":", lw=1)
    b0.set_xlabel("rain rate [mm/h] (lcl)"); b0.set_ylabel("recall"); b0.set_ylim(0, 1.05)
    b1 = b0.twinx(); xs = sorted(p["FP_s"]); b1.plot(xs, [np.median(p["FP_s"][x]) for x in xs], "C1-^", label="FP/s")
    b1.set_ylabel("false positives / s"); b0.set_title("(b) LiDAR rain-clutter sweep")
    b0.legend(loc="lower left", fontsize=8); b1.legend(loc="upper right", fontsize=8)

    # (c) score vs R_h scatter
    c = ax[1, 0]
    cols = {"nf": "gray", "lso": "C3", "lcl": "C1", "imn": "C2", "gn": "C4", "imb": "C5"}
    for r in rows:
        x, y = fnum(r.get(sk)), fnum(r.get("R_h"))
        if x is None or y is None:
            continue
        c.scatter(x, y, color=cols.get(r["fault"], "k"), s=18, alpha=.7)
    for f, col in cols.items():
        c.scatter([], [], color=col, label=f)
    c.axvline(0.7, color="k", ls="--", lw=.8); c.axvline(0.3, color="k", ls=":", lw=.8)
    c.set_xlabel(f"monitor perception score ({sk})"); c.set_ylabel("R_h"); c.set_xlim(0, 1.02); c.set_ylim(0, 1.05)
    c.set_title("(c) score vs measured recall (one point = one run)"); c.legend(fontsize=8)

    # (d) imn: e_lat P95 and S_loc
    p = series("imn", ["e_lat_p95", "s_loc_med"])
    d0 = ax[1, 1]
    xs = sorted(p["e_lat_p95"])
    for lv, vs in sorted(p["e_lat_p95"].items()):
        d0.scatter([lv] * len(vs), vs, color="C2", s=14, alpha=.6)
    d0.plot(xs, [np.median(p["e_lat_p95"][x]) for x in xs], "C2-o", label="EKF lateral error P95 [m]")
    d0.axhline(0.5, color="k", ls="--", lw=.8, label="0.5 m move minimum")
    d0.axhline(0.29, color="gray", ls=":", lw=.8, label="Reid'19 local 0.29 m")
    d0.set_xlabel("gyro noise σ [rad/s] (imn)"); d0.set_ylabel("lateral error [m]")
    d1 = d0.twinx(); xs = sorted(p["s_loc_med"]); d1.plot(xs, [np.median(p["s_loc_med"][x]) for x in xs], "C4-s", label="S_loc (recomputed)")
    d1.axhline(0.5, color="C4", ls=":", lw=.8); d1.set_ylim(0, 1.05); d1.set_ylabel("localization score")
    d0.set_title("(d) IMU noise sweep: EKF error vs monitor"); d0.legend(loc="upper left", fontsize=8); d1.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "fig_noise_capability.png", dpi=160)
    fig.savefig(out / "fig_noise_capability.pdf")

    # tables
    lines = ["| fault | level | n | R_h | R_far | D_det | FP/s | S_lidar | " + sk + " | e_lat P95 | NVTL | NDT Hz | S_loc |", "|" + "---|" * 13]
    def keyf(k):
        f, s = k
        return (f, level_of({"fault": f, "sev": s}) or 0)
    for (f, s) in sorted(by, key=keyf):
        rs = by[(f, s)]
        cells = [f, s, str(len(rs))]
        for k in ["R_h", "R_far", "D_det", "FP_s", "S_lidar_front", sk, "e_lat_p95", "nvtl_med", "ndt_hz", "s_loc_med"]:
            m, n = med(rs, k)
            cells.append("–" if m is None else f"{m:.2f}")
        lines.append("| " + " | ".join(cells) + " |")
    (out / "table_noise_capability.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"-> {out}/fig_noise_capability.png, table_noise_capability.md")


if __name__ == "__main__":
    main()
