#!/usr/bin/env python3
"""노이즈 세기 사다리 → (실제 인식률 / 실제 측위오차) vs 감시기 점수, 고장 유형별 패널.
입력: results/noise_sweep_batch.log 의 [live] 줄 (스윕) + results/stock_matrix.log 의 [live] 줄 (순정 def, mid/high 15회)
출력: results/figs/fig_sweep_score_vs_capability.png
[live] 열: idx fault sev rep outcome wall R_h R_far D_det FP S_front S_perc e_lat ATE NVTL ndt_hz s_loc n_pairs n_frames npc ...
"""
import re, collections, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"
LEVEL = {("lso", "mid"): 0.33, ("lso", "high"): 0.07, ("lcl", "mid"): 5.0, ("lcl", "high"): 25.0,
         ("imn", "mid"): 0.5, ("imn", "high"): 1.5}
NF_X = {"lso": 1.0, "lcl": 0.0, "imn": 0.0}

def f(x):
    try: return float(x)
    except Exception: return None

def load(path, stock):
    rows = []
    for ln in open(path, errors="replace"):
        if not ln.startswith("[live]"): continue
        c = [x.strip() for x in ln.split("|")[1:-1]]
        if len(c) < 20: continue
        fault, sev, outcome = c[1], c[2], c[4]
        if outcome in ("CARLA_DIED", "SETUP_FAIL", "INTERRUPTED", "DISK_FULL"): continue
        if stock:
            if (fault, sev) in LEVEL: x = LEVEL[(fault, sev)]
            elif fault == "nf": x = None
            else: continue
        else:
            if fault == "nf": x = None
            elif fault in ("lso", "lcl"): x = f(sev.split(":")[0])
            elif fault == "imn": x = f(sev)
            else: continue
        rows.append(dict(fault=fault, x=x, R_h=f(c[6]), R_far=f(c[7]), D_det=f(c[8]), S_front=f(c[10]), S_perc=f(c[11]),
                         e_lat=f(c[12]), ATE=f(c[13]), ndt_hz=f(c[15]), s_loc=f(c[16]), stock=stock))
    return rows

rows = load(f"{RES}/noise_sweep_batch.log", False) + load(f"{RES}/stock_matrix.log", True)
rows = [r for r in rows if not (r["fault"] == "nf" and (r["e_lat"] or 0) > 5)]   # nf 인데 측위 발산한 무효 런 제외
nf = [r for r in rows if r["fault"] == "nf"]
import numpy as np

def nf_ref(key):
    v = [r[key] for r in nf if r[key] is not None]
    return float(np.median(v)) if v else None

def agg(fault, key, use_nf=True):
    g = collections.defaultdict(list)
    for r in rows:
        if r["fault"] == fault and r[key] is not None and r["x"] is not None: g[r["x"]].append(r[key])
    if use_nf:
        v = [r[key] for r in nf if r[key] is not None]
        if v: g[NF_X[fault]] = v
    xs = sorted(g)
    return xs, [float(np.median(g[x])) for x in xs], [float(np.percentile(g[x], 25)) for x in xs], [float(np.percentile(g[x], 75)) for x in xs], [len(g[x]) for x in xs]

plt.rcParams.update({"font.family": "serif", "font.size": 10})
fig, axes = plt.subplots(1, 3, figsize=(13, 5.0))

def panel(ax, fault, cap_keys, cap_labels, score_key, score_label, xlabel, thr, invert=False, logx=False, logy_cap=False, nf_as_point=True):
    ax2 = ax.twinx()
    styles = [("o-", "black"), ("s--", "dimgray")]
    for (k, lab), (stl, col) in zip(zip(cap_keys, cap_labels), styles):
        xs, m, lo, hi, n = agg(fault, k, use_nf=nf_as_point)
        ax.plot(xs, m, stl, color=col, label=lab, ms=5)
        ax.fill_between(xs, lo, hi, color=col, alpha=0.12, lw=0)
        if not nf_as_point and nf_ref(k) is not None:
            ax.axhline(nf_ref(k), color=col, ls=":", lw=1); ax.text(xs[0], nf_ref(k), f" fault-free {nf_ref(k):.2f} m", color=col, fontsize=7, va="bottom")
    xs, m, lo, hi, n = agg(fault, score_key, use_nf=nf_as_point)
    ax2.plot(xs, m, "^-", color="#a50f15", label=score_label, ms=6)
    ax2.fill_between(xs, lo, hi, color="#a50f15", alpha=0.12, lw=0)
    ax2.axhline(thr, color="#a50f15", ls=":", lw=1)
    ax2.text(0.02, thr + 0.02, f"score threshold {thr}", color="#a50f15", fontsize=8, transform=ax2.get_yaxis_transform(), ha="left")
    ax2.set_ylim(0, 1.05); ax2.set_ylabel(score_label, color="#a50f15"); ax2.tick_params(axis="y", colors="#a50f15")
    ax.set_xlabel(xlabel + "\n" + "runs per level: " + ", ".join(f"{x:g}:{c}" for x, c in zip(xs, n)), fontsize=8)
    if invert: ax.invert_xaxis()
    if logx: ax.set_xscale("log")
    if logy_cap: ax.set_yscale("log")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2, fontsize=8, frameon=False)
    ax.grid(alpha=0.3)

panel(axes[0], "lso", ["R_h", "R_far"], ["recall 0–26 m (actual)", "recall 26–50 m (actual)"], "S_front", "front-LiDAR score",
      "LiDAR transmittance T (1 = clean)  →  worse", 0.7, invert=True)
axes[0].set_ylim(0, 1.05); axes[0].set_ylabel("Autoware detection recall vs CARLA GT"); axes[0].set_title("(a) LiDAR sparsification (lso)", loc="left", fontsize=10)
panel(axes[1], "lcl", ["R_h", "R_far"], ["recall 0–26 m (actual)", "recall 26–50 m (actual)"], "S_front", "front-LiDAR score",
      "rain rate (mm/h)  →  worse", 0.7)
axes[1].set_ylim(0, 1.05); axes[1].set_title("(b) LiDAR clutter / rain (lcl)", loc="left", fontsize=10)
panel(axes[2], "imn", ["e_lat", "ATE"], ["EKF lateral err P95 (m, actual)", "EKF ATE (m, actual)"], "s_loc", "localization score",
      "gyro noise σ (rad/s)  →  worse", 0.5, logx=True, logy_cap=True, nf_as_point=False)
axes[2].set_ylabel("EKF error vs CARLA GT (m)"); axes[2].set_title("(c) IMU gyro noise (imn)", loc="left", fontsize=10)
fig.suptitle("Monitor score vs actual Autoware capability along the noise ladder (median, IQR band; mid/high levels include the 15-run stock block; lso high = T 0.07 at 150° width)", fontsize=9)
plt.tight_layout()
out = f"{RES}/figs/fig_sweep_score_vs_capability.png"; plt.savefig(out, dpi=200, bbox_inches="tight"); print(out)
