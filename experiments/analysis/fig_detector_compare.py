#!/usr/bin/env python3
"""검출기 비교 — 벤치마크 논문식 3패널 (IEEE/MATLAB 스타일).
(a) 검출기별 레이더: 고장 계열 6축(LiDAR 열화·LiDAR 사망·카메라 열화·카메라 사망·GNSS·IMU) 검출률(Σk/Σn), 회색 점선 = 제안 윤곽.
(b) 검출 지연 분포(검출된 케이스, 시뮬 s, 로그), (c) 포괄 범위(18 조건 평균 검출률; 미평가 = 0) 대 중앙 지연.
lso-mid(능력 손실 없음, 제안은 설계상 미개입)는 모든 검출기에서 제외. 자료: analysis/detector_data.py"""
import os, sys, numpy as np, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detector_data import load_cells, ROWS, FAMILY, FAMILIES, DETS, RES
import matplotlib as mpl; mpl.use("Agg")
mpl.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif", "STIXGeneral"], "mathtext.fontset": "stix",
                     "axes.linewidth": 0.8, "font.size": 9, "xtick.direction": "in", "ytick.direction": "in", "axes.grid": False})
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
cells = load_cells()
COND = [(f, s) for f, s, _ in ROWS if not (f == "lso" and s == "mid")]
COLOR = {"ours": "black", "b0": "#0072BD", "won": "#D95319", "zh": "#EDB120", "lee": "#7E2F8E", "yu": "#77AC30", "gos": "#4DBEEE", "radas": "#A2142F", "mmd": "#A0522D"}
SHORT = {"ours": "Proposed", "b0": "Autoware diag.", "won": "Won 2023", "zh": "Zhang 2024", "lee": "Lee 2022", "yu": "Yu 2021", "gos": "Huang & Su", "radas": "RADAS", "mmd": "Alibi MMD"}
def fam_rate(det):
    out = []
    for fam in FAMILIES:
        k = n = 0
        for f, s in COND:
            if FAMILY[f] != fam: continue
            c = cells.get((f, s, det))
            if c: k += c[0]; n += c[1]
        out.append(k / n if n else 0.0)
    return out
def coverage(det):   # mean per-condition detection rate; unevaluated condition counts as 0
    return float(np.mean([(cells[(f, s, det)][0] / cells[(f, s, det)][1]) if (f, s, det) in cells and cells[(f, s, det)][1] else 0.0 for f, s in COND]))
def lats(det):
    return [l for f, s in COND for l in cells.get((f, s, det), (0, 0, []))[2]]
rates = {d: fam_rate(d) for d, _ in DETS}; cov = {d: coverage(d) for d, _ in DETS}; lat = {d: lats(d) for d, _ in DETS}
for d, name in DETS: print(f"{name:34s} cov {cov[d]:.2f}  med lat {st.median(lat[d]) if lat[d] else float('nan'):5.1f} s  fam " + " ".join(f"{r:.2f}" for r in rates[d]))

fig = plt.figure(figsize=(13.2, 8.6))
gs = GridSpec(3, 5, figure=fig, width_ratios=[1, 1, 1, 0.18, 1.55], height_ratios=[1, 1, 1], wspace=0.12, hspace=0.8, left=0.03, right=0.985, top=0.885, bottom=0.075)
# (a) radars
N = len(FAMILIES); ang = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist(); ang_c = ang + ang[:1]
ours = rates["ours"] + rates["ours"][:1]
for i, (d, name) in enumerate(DETS):
    ax = fig.add_subplot(gs[i // 3, i % 3], polar=True)
    v = rates[d] + rates[d][:1]
    ax.set_theta_offset(np.pi / 2); ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.0); ax.set_yticks([0.5, 1.0]); ax.set_yticklabels(["0.5", "1"], fontsize=6, color="#555"); ax.set_rlabel_position(22)
    ax.set_xticks(ang); ax.set_xticklabels(FAMILIES, fontsize=6.8)
    ax.grid(True, color="#cccccc", lw=0.5); ax.spines["polar"].set_linewidth(0.8)
    if d != "ours": ax.plot(ang_c, ours, color="#888888", lw=0.9, ls="--", zorder=2)
    ax.plot(ang_c, v, color=COLOR[d], lw=1.6 if d == "ours" else 1.3, zorder=3); ax.fill(ang_c, v, color=COLOR[d], alpha=0.22, zorder=2)
    ax.scatter(ang, rates[d], s=12, color=COLOR[d], edgecolors="black", linewidths=0.4, zorder=4)
    ax.set_title(name.replace(" (", "\n("), fontsize=8.6, pad=6, fontweight="bold" if d == "ours" else "normal")
    for lab in ax.get_xticklabels(): lab.set_y(lab.get_position()[1] - 0.06)
fig.text(0.03, 0.965, "(a) Detection rate by fault family (grey dashed outline: proposed)", fontsize=10.5, ha="left")
# (b) latency
axb = fig.add_subplot(gs[0:2, 4])
order = [d for d, _ in DETS][::-1]
data = [lat[d] if lat[d] else [np.nan] for d in order]
bp = axb.boxplot(data, vert=False, widths=0.55, patch_artist=True, showfliers=False, medianprops=dict(color="black", lw=1.2), whiskerprops=dict(lw=0.8), capprops=dict(lw=0.8), boxprops=dict(lw=0.8))
for patch, d in zip(bp["boxes"], order): patch.set_facecolor(COLOR[d]); patch.set_alpha(0.45)
rng = np.random.default_rng(0)
for yi, d in enumerate(order, start=1):
    if lat[d]: axb.scatter(lat[d], yi + rng.uniform(-0.18, 0.18, len(lat[d])), s=5, color=COLOR[d], alpha=0.5, linewidths=0, zorder=3)
axb.set_xscale("log"); axb.set_xlim(0.3, 300); axb.set_yticks(range(1, len(order) + 1)); axb.set_yticklabels([SHORT[d] for d in order], fontsize=8.5)
axb.get_yticklabels()[order.index("ours")].set_fontweight("bold")
axb.set_xlabel("Detection latency after injection (s, simulation time, log)", fontsize=9); axb.tick_params(axis="both", which="both", length=3)
axb.set_title("(b) Detection latency (detected cases only)", loc="left", fontsize=10.5, pad=8)
for sp in axb.spines.values(): sp.set_visible(True)
# (c) coverage vs latency
axc = fig.add_subplot(gs[2, 4])
for d, name in DETS:
    x = st.median(lat[d]) if lat[d] else None
    if x is None: continue
    if d == "ours": axc.scatter(x, cov[d], marker="*", s=190, color="black", edgecolors="black", zorder=5)
    else: axc.scatter(x, cov[d], s=48, color=COLOR[d], edgecolors="black", linewidths=0.6, zorder=4)
off = {"ours": (9, -1), "b0": (8, -2), "won": (-8, 7), "zh": (0, 9), "lee": (8, -4), "yu": (8, 4), "gos": (8, -9), "radas": (8, -3), "mmd": (8, -3)}
for d, name in DETS:
    x = st.median(lat[d]) if lat[d] else None
    if x is None: continue
    dx, dy = off[d]; axc.annotate(SHORT[d], (x, cov[d]), xytext=(dx, dy), textcoords="offset points", fontsize=8, ha=("center" if dx == 0 else ("left" if dx > 0 else "right")), va="center", fontweight="bold" if d == "ours" else "normal")
axc.set_xscale("log"); axc.set_xlim(0.3, 300); axc.set_ylim(-0.03, 1.08)
axc.set_xlabel("Median detection latency (s, log)", fontsize=9); axc.set_ylabel("Coverage\n(mean detection rate, 18 conditions)", fontsize=8.5)
axc.set_title("(c) Coverage vs. latency", loc="left", fontsize=10.5, pad=8); axc.tick_params(axis="both", which="both", length=3)
fig.text(0.03, 0.012, "Conditions: 18 capability-reducing faults (LiDAR sparsification mid excluded for all detectors — no capability loss, no intervention by design). "
         "A family the detector does not consume counts as 0. False alarms on no-fault runs: 0 for every detector shown. RADAS: 1 run per condition.", fontsize=7.6, color="#333")
for ext in ("png", "pdf"): fig.savefig(f"{RES}/figs/fig_detector_compare.{ext}", dpi=200, facecolor="white")
print("saved", f"{RES}/figs/fig_detector_compare.png")
