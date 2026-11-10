#!/usr/bin/env python3
"""검출기 비교 — 벤치마크식 2패널 (IEEE/MATLAB 스타일). 2026-11-11 리뷰 반영판.
(a) 검출기별 레이더: 고장 계열 6축 검출률(Σk/Σn). **빗금 부채꼴 = 해당 센서를 다루지 않거나 평가하지 않음(N/A)** — 0(평가했으나 미검출)과 구분.
    다각형은 평가한 축만 잇는다. 회색 점선 = 제안 윤곽.
(b) 검출 지연 분포(검출된 케이스, 시뮬 s, 로그). 검출 표본 5개 미만(Won·RADAS)은 상자 대신 개별 점. 오른쪽에 n = 검출/평가 케이스.
lso-mid(능력 손실 없음, 제안은 설계상 미개입)는 모든 검출기에서 제외. 자료: analysis/detector_data.py. 오탐 수치는 각 보고서(results/*/report.md)에서 옮김."""
import os, sys, numpy as np, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detector_data import load_cells, ROWS, FAMILY, FAMILIES, DETS, RES, APPLICABLE, applicable
import matplotlib as mpl; mpl.use("Agg")
mpl.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif", "STIXGeneral"], "mathtext.fontset": "stix",
                     "axes.linewidth": 0.8, "font.size": 9, "xtick.direction": "in", "ytick.direction": "in", "axes.grid": False, "hatch.linewidth": 0.5})
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
cells = load_cells()
COND = [(f, s) for f, s, _ in ROWS if not (f == "lso" and s == "mid")]
COLOR = {"ours": "black", "b0": "#0072BD", "won": "#D95319", "zh": "#EDB120", "lee": "#7E2F8E", "yu": "#77AC30", "gos": "#4DBEEE", "radas": "#A2142F", "mmd": "#A0522D"}
SHORT = {"ours": "Proposed", "b0": "Autoware diag.", "won": "Won 2023", "zh": "Zhang 2024", "lee": "Lee 2022", "yu": "Yu 2021", "gos": "Huang & Su", "radas": "RADAS", "mmd": "Alibi MMD"}
def fam_stats(det):
    """[(rate or None, k, n)] per family; None = not evaluated (sensor not consumed / not run)."""
    out = []
    for fam in FAMILIES:
        k = n = 0
        if fam in APPLICABLE[det]:
            for f, s in COND:
                if FAMILY[f] != fam: continue
                c = cells.get((f, s, det))
                if c: k += c[0]; n += c[1]
        out.append((k / n if n else None, k, n))   # None = 센서를 다루지 않거나 평가 안 함 → 빗금
    return out
def lats(det): return [l for f, s in COND if applicable(det, f) for l in cells.get((f, s, det), (0, 0, []))[2]]
def kn(det):
    k = n = 0
    for f, s in COND:
        if not applicable(det, f): continue
        c = cells.get((f, s, det))
        if c: k += c[0]; n += c[1]
    return k, n
stats = {d: fam_stats(d) for d, _ in DETS}; lat = {d: lats(d) for d, _ in DETS}
for d, name in DETS:
    k, n = kn(d); print(f"{name:34s} det {k}/{n}  med lat {st.median(lat[d]) if lat[d] else float('nan'):5.1f} s  fam " + " ".join("n/a " if r is None else f"{r:.2f}" for r, _, _ in stats[d]))

fig = plt.figure(figsize=(12.6, 8.6))
gs = GridSpec(3, 5, figure=fig, width_ratios=[1, 1, 1, 0.12, 1.45], height_ratios=[1, 1, 1], wspace=0.1, hspace=0.78, left=0.03, right=0.9, top=0.875, bottom=0.075)
N = len(FAMILIES); ang = np.array([2 * np.pi * i / N for i in range(N)]); W = 2 * np.pi / N
ours_r = [r if r is not None else 0 for r, _, _ in stats["ours"]]
for i, (d, name) in enumerate(DETS):
    ax = fig.add_subplot(gs[i // 3, i % 3], polar=True)
    ax.set_theta_offset(np.pi / 2); ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.0); ax.set_yticks([0.5, 1.0]); ax.set_yticklabels(["0.5", "1"], fontsize=6, color="#555"); ax.set_rlabel_position(22)
    ax.set_xticks(ang); ax.set_xticklabels(FAMILIES, fontsize=6.8)
    ax.grid(True, color="#cccccc", lw=0.5); ax.spines["polar"].set_linewidth(0.8)
    ev = [j for j, (r, _, _) in enumerate(stats[d]) if r is not None]; na = [j for j in range(N) if j not in ev]
    for j in na: ax.bar(ang[j], 1.0, width=W, bottom=0, color="#f0f0f0", edgecolor="#b0b0b0", hatch="////", linewidth=0.0, zorder=1)
    if d != "ours": ax.plot(np.r_[ang, ang[:1]], ours_r + ours_r[:1], color="#888888", lw=0.9, ls="--", zorder=2)
    if ev:
        a = ang[ev]; v = np.array([stats[d][j][0] for j in ev])
        if len(ev) == N or True:
            a_c = np.r_[a, a[:1]]; v_c = np.r_[v, v[:1]]
            ax.plot(a_c, v_c, color=COLOR[d], lw=1.6 if d == "ours" else 1.3, zorder=3); ax.fill(a_c, v_c, color=COLOR[d], alpha=0.22, zorder=2)
        ax.scatter(a, v, s=14, color=COLOR[d], edgecolors="black", linewidths=0.4, zorder=4)
    ax.set_title(name.replace(" (", "\n("), fontsize=8.6, pad=6, fontweight="bold" if d == "ours" else "normal")
    for lab in ax.get_xticklabels(): lab.set_y(lab.get_position()[1] - 0.06)
fig.text(0.03, 0.955, "(a) Detection rate by fault family", fontsize=10.5, ha="left")
fig.legend(handles=[Patch(facecolor="#f0f0f0", edgecolor="#b0b0b0", hatch="////", label="not applicable: detector does not consume that sensor, or not evaluated"),
                    Line2D([], [], color="#888888", ls="--", lw=0.9, label="proposed (reference outline)"),
                    Line2D([], [], marker="o", color="#555", lw=0, ms=4, mec="black", label="evaluated family: detection rate (0 = evaluated, missed)"),
                    Patch(facecolor="#bbbbbb", alpha=0.6, edgecolor="black", label="(b) box: median and interquartile range of detected cases"),
                    Line2D([], [], marker="D", color="#bbbbbb", lw=0, ms=5, mec="black", label="(b) fewer than 5 detections: individual cases")],
           loc="upper left", bbox_to_anchor=(0.2, 0.995), ncol=3, fontsize=7.6, frameon=True, edgecolor="black", handlelength=1.8, columnspacing=1.2, labelspacing=0.35)
# (b) latency
axb = fig.add_subplot(gs[:, 4])
order = [d for d, _ in DETS][::-1]; pos = list(range(1, len(order) + 1))
boxed = [d for d in order if len(lat[d]) >= 5]
bp = axb.boxplot([lat[d] for d in boxed], positions=[pos[order.index(d)] for d in boxed], vert=False, widths=0.5, patch_artist=True, showfliers=False,
                 medianprops=dict(color="black", lw=2.0), whiskerprops=dict(lw=0.8), capprops=dict(lw=0.8), boxprops=dict(lw=0.8), zorder=3)
for patch, d in zip(bp["boxes"], boxed): patch.set_facecolor(COLOR[d]); patch.set_alpha(0.35)
rng = np.random.default_rng(0)
for yi, d in zip(pos, order):
    if not lat[d]: continue
    if len(lat[d]) >= 5: axb.scatter(lat[d], yi + rng.uniform(-0.16, 0.16, len(lat[d])), s=3.5, color=COLOR[d], alpha=0.28, linewidths=0, zorder=2)
    else: axb.scatter(lat[d], [yi] * len(lat[d]), s=34, marker="D", color=COLOR[d], edgecolors="black", linewidths=0.6, zorder=4)
for yi, d in zip(pos, order):
    k, n = kn(d); axb.text(1.015, yi, f"{k} / {n}", transform=axb.get_yaxis_transform(), fontsize=7.8, va="center", ha="left", color="#333")
axb.text(1.015, 1.0, "detected /\nevaluated", transform=axb.transAxes, fontsize=7.4, va="bottom", ha="left", color="#333")
axb.set_xscale("log"); axb.set_xlim(0.3, 300); axb.set_ylim(0.4, len(order) + 0.6); axb.set_yticks(pos); axb.set_yticklabels([SHORT[d] for d in order], fontsize=8.5)
axb.get_yticklabels()[order.index("ours")].set_fontweight("bold")
axb.set_xlabel("Latency (s, simulation time, log scale)", fontsize=9); axb.tick_params(axis="both", which="both", length=3)
axb.set_title("(b) Detection latency after injection", loc="left", fontsize=10.5, pad=8)
for ext in ("png", "pdf"): fig.savefig(f"{RES}/figs/fig_detector_compare.{ext}", dpi=200, facecolor="white")
print("saved", f"{RES}/figs/fig_detector_compare.png")
