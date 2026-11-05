#!/usr/bin/env python3
"""노이즈 사다리: 건강도 점수(빨강, 오른쪽 축) 와 함께 보는 실제 성능 + recall 밖 부작용.
행: (1) 실제 recall / EKF 오차  (2) 고장이 만든 유령 검출/초  (3) 설명 안 되는 정지 시간  (4) 급제동 횟수  [(5) 추적 ID 교체/분: 값 있으면]
열: lso / lcl / imn.  입력: results/side_effects.csv + [live] 줄.  출력: results/figs/fig_sweep_side_effects.png
"""
import csv, math, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results")
LEVEL = {("lso", "mid"): 0.33, ("lso", "high"): 0.07, ("lcl", "mid"): 5.0, ("lcl", "high"): 25.0, ("imn", "mid"): 0.5, ("imn", "high"): 1.5}
RED = "#a50f15"; BLUE = "#2f6bb0"

def f(x):
    try: return float(x)
    except Exception: return None

# ---- [live] 줄: 점수·recall·EKF
def load_live(path, stock):
    rows = []
    for ln in open(path, errors="replace"):
        if not ln.startswith("[live]"): continue
        c = [x.strip() for x in ln.split("|")[1:-1]]
        if len(c) < 20 or c[4] in ("CARLA_DIED", "SETUP_FAIL", "INTERRUPTED", "DISK_FULL"): continue
        fault, sev = c[1], c[2]
        if stock:
            if (fault, sev) in LEVEL: x = LEVEL[(fault, sev)]
            elif fault == "nf": x = None
            else: continue
        else:
            if fault == "nf": x = None
            elif fault in ("lso", "lcl"): x = f(sev.split(":")[0])
            elif fault == "imn": x = f(sev)
            else: continue
        rows.append(dict(fault=fault, x=x, R_h=f(c[6]), R_far=f(c[7]), S_front=f(c[10]), e_lat=f(c[12]), ATE=f(c[13]), s_loc=f(c[16])))
    return rows
live = load_live(RES / "noise_sweep_batch.log", False) + load_live(RES / "stock_matrix.log", True)
live = [r for r in live if not (r["fault"] == "nf" and (r["e_lat"] or 0) > 5)]

# ---- side_effects.csv
def level_of(tag):
    s = tag[6:] if tag.startswith("stock-") else tag
    p = s.split("-"); fa, lv = p[0], p[1]
    if fa == "nf": return "nf", None
    if (fa, lv) in LEVEL: return fa, LEVEL[(fa, lv)]
    try: return fa, float(lv.split("_")[0])
    except ValueError: return fa, None
se = list(csv.DictReader(open(RES / "side_effects.csv")))
nf_se = [r for r in se if "nf-mid" in r["tag"]]

def agg(rows, fault, key, getx=lambda r: r["x"]):
    g = collections.defaultdict(list)
    for r in rows:
        fa = r["fault"] if "fault" in r else level_of(r["tag"])[0]
        if fa != fault: continue
        x = getx(r)
        v = f(r.get(key))
        if x is None or v is None: continue
        g[x].append(v)
    xs = sorted(g)
    return xs, [float(np.median(g[x])) for x in xs], [float(np.percentile(g[x], 25)) for x in xs], [float(np.percentile(g[x], 75)) for x in xs]

def nf_median(rows, key):
    v = [f(r.get(key)) for r in rows if (r.get("fault") == "nf" if "fault" in r else True)]
    v = [x for x in v if x is not None]
    return float(np.median(v)) if v else None

ROWS = [("cap", "actual capability"), ("FP_novel_s", "phantom detections / s\n(outside fault-free static mask)"),
        ("phantom_stop_s", "unexplained stop time (s)\n(no signal, nothing ahead)"), ("hard_brakes", "hard-brake commands\n(< -3 m/s²)")]
if any(f(r.get("track_churn")) is not None for r in se): ROWS.append(("track_churn", "track-ID switches / min"))
COLS = [("lso", "(a) LiDAR sparsification", "LiDAR transmittance T  →  worse", True, False, "S_front", "front-LiDAR score", 0.7),
        ("lcl", "(b) LiDAR clutter / rain", "rain rate (mm/h)  →  worse", False, False, "S_front", "front-LiDAR score", 0.7),
        ("imn", "(c) IMU gyro noise", "gyro noise σ (rad/s)  →  worse", False, True, "s_loc", "localization score", 0.5)]

plt.rcParams.update({"font.family": "serif", "font.size": 9})
fig, axes = plt.subplots(len(ROWS), 3, figsize=(13.5, 2.5 * len(ROWS)), sharex="col")
for j, (fault, title, xlabel, invert, logx, skey, slabel, thr) in enumerate(COLS):
    for i, (key, ylabel) in enumerate(ROWS):
        ax = axes[i][j]; ax2 = ax.twinx()
        if key == "cap":
            if fault == "imn":
                for k, lab, stl, col in (("e_lat", "EKF lateral err P95 (m)", "o-", "black"), ("ATE", "EKF ATE (m)", "s--", "dimgray")):
                    xs, m, lo, hi = agg(live, fault, k); ax.plot(xs, m, stl, color=col, ms=4, label=lab); ax.fill_between(xs, lo, hi, color=col, alpha=0.12, lw=0)
                ref = nf_median([r for r in live if r["fault"] == "nf"], "e_lat")
                if ref: ax.axhline(ref, color=BLUE, ls=":", lw=1.2)
                ax.set_yscale("log"); 
                if j == 0 or True: ax.set_ylabel("EKF error vs GT (m)" if j == 2 else "", fontsize=8)
            else:
                for k, lab, stl, col in (("R_h", "recall 0–26 m", "o-", "black"), ("R_far", "recall 26–50 m", "s--", "dimgray")):
                    xs, m, lo, hi = agg(live, fault, k); ax.plot(xs, m, stl, color=col, ms=4, label=lab); ax.fill_between(xs, lo, hi, color=col, alpha=0.12, lw=0)
                ax.set_ylim(0, 1.05)
                if j == 0: ax.set_ylabel("Autoware detection recall\nvs CARLA GT", fontsize=8)
        else:
            xs, m, lo, hi = agg(se, fault, key, getx=lambda r: level_of(r["tag"])[1])
            if xs: ax.plot(xs, m, "o-", color="black", ms=4, label=ylabel.split("\n")[0]); ax.fill_between(xs, lo, hi, color="black", alpha=0.12, lw=0)
            ref = nf_median(nf_se, key)
            if ref is not None: ax.axhline(ref, color=BLUE, ls=":", lw=1.2); ax.text(0.02, 0.93, f"fault-free median {ref:g}", transform=ax.transAxes, color=BLUE, fontsize=7, va="top")
            if j == 0: ax.set_ylabel(ylabel, fontsize=8)
        # 건강도 점수 (오른쪽 축, 모든 행 공통)
        xs, m, lo, hi = agg(live, fault, skey)
        ax2.plot(xs, m, "^-", color=RED, ms=5, label=slabel, alpha=0.9); ax2.fill_between(xs, lo, hi, color=RED, alpha=0.10, lw=0)
        ax2.axhline(thr, color=RED, ls=":", lw=1); ax2.set_ylim(0, 1.05); ax2.tick_params(axis="y", colors=RED, labelsize=7)
        if j == 2: ax2.set_ylabel(slabel, color=RED, fontsize=8)
        if i == 0: ax.set_title(title, loc="left", fontsize=10)
        if invert and not ax.xaxis_inverted(): ax.invert_xaxis()
        if logx: ax.set_xscale("log")
        ax.grid(alpha=0.3)
        if i == len(ROWS) - 1: ax.set_xlabel(xlabel)
        if i == 0:
            h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="lower left" if fault != "imn" else "upper left", frameon=True)
fig.suptitle("Noise ladder: monitor score (red, right axis, dotted = threshold) vs actual capability and side effects beyond recall\n(median, IQR band; blue dotted = fault-free stock runs n=15; mid/high levels include the 15-run stock block)", fontsize=9)
plt.tight_layout()
out = RES / "figs" / "fig_sweep_side_effects.png"; plt.savefig(out, dpi=200, bbox_inches="tight"); print(out)
