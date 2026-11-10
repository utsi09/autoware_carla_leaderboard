#!/usr/bin/env python3
"""[2026-11-09] 비전(LiDAR·카메라) 베이스라인 비교 그림 — fig_baseline_fdi 와 같은 양식.
(a) 고장별 검출률(Wilson 95% CI, 셀당 n=5) (b) 검출 지연(시뮬 시간, 로그). 검출기: B0 인지 진단, Won 비트맵, Zhang 분포, Lee CNN, 제안.
입력: results/raw_vision/cases.csv  출력: results/figs/fig_vision_fdi.png/.pdf"""
import os, sys, csv, math, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle; figstyle.apply({"font.size": 9})
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
rows = [r for r in csv.DictReader(open(os.path.join(RES, "raw_vision", "cases.csv"))) if r["fault"] != "nf"]
ORDER = [("lso", "mid"), ("lso", "high"), ("lcl", "mid"), ("lcl", "high"), ("cn", "mid"), ("cn", "high")]
LABEL = {"lso": "LiDAR\n성김", "lcl": "LiDAR\n강우 열화", "cn": "카메라\n잡음"}
DET = [("b0_perc", "Autoware 인지 진단 (B0)", "#8a8f99", "//"), ("won", "구면 비트맵 소실 (Won 2023 구조)", figstyle.C_NF, ""),
       ("zh", "거리·강도 분포 거리 (Zhang 2024 구조)", figstyle.C_MID, ""), ("lee", "영상 CNN 분류 (Lee 2022 구조)", "#1b9e77", ""), ("ours", "제안 (감독기 재생)", figstyle.C_HIGH, "")]
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan, np.nan)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0, c - h), min(1, c + h)
groups = collections.OrderedDict((k, [r for r in rows if (r["fault"], r["sev"]) == k]) for k in ORDER)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 7.6), gridspec_kw=dict(height_ratios=[1, 1], hspace=0.62))
X = np.arange(len(groups)); w = 0.16
for j, (key, lab, col, hatch) in enumerate(DET):
    ps, lo, hi = [], [], []
    for k, cs in groups.items():
        d = sum(1 for c in cs if c[f"det_{key}"] != ""); p, l, h = wilson(d, len(cs)); ps.append(p); lo.append(l); hi.append(h)
    ps, lo, hi = map(np.array, (ps, lo, hi)); xs = X + (j - 2) * w
    ax1.bar(xs, ps, w * 0.92, color=col, hatch=hatch, edgecolor="white", linewidth=0.8, label=lab, zorder=3)
    ax1.errorbar(xs, ps, yerr=[np.nan_to_num(ps - lo), np.nan_to_num(hi - ps)], fmt="none", ecolor=figstyle.INK, elinewidth=0.8, capsize=2, zorder=4)
    for i, (k, cs) in enumerate(groups.items()):
        d = [float(c[f"det_{key}"]) for c in cs if c[f"det_{key}"] != ""]
        if d:
            ax2.scatter(np.full(len(d), xs[i]) + np.random.default_rng(i).uniform(-w * 0.3, w * 0.3, len(d)), d, s=14, color=col, alpha=0.55, linewidths=0, zorder=3)
            ax2.plot([xs[i] - w * 0.4, xs[i] + w * 0.4], [np.median(d)] * 2, color=figstyle.INK, lw=1.4, zorder=4)
ax1.set_ylim(0, 1.08); ax1.set_ylabel("검출률 (Wilson 95% CI)"); ax1.set_xticks(X); ax1.set_xticklabels([f"{LABEL[f]}\n{s}" for f, s in groups], fontsize=8)
ax1.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.24), fontsize=7.8, frameon=False)
ax1.set_title("(a) 동일 순정 주행의 원시 점군·영상(2 Hz)에서의 고장 검출률 (셀당 n = 5)", loc="left", fontsize=10)
ax2.set_yscale("log"); ax2.set_ylim(0.3, 300); ax2.set_ylabel("검출 지연 (s, 시뮬 시간, 로그)"); ax2.set_xticks(X); ax2.set_xticklabels([f"{LABEL[f]}\n{s}" for f, s in groups], fontsize=8)
ax2.set_title("(b) 검출된 케이스의 지연 (점: 개별 런, 가로선: 중앙값; 1 s 지속 확정 포함)", loc="left", fontsize=10)
ax2.yaxis.set_major_locator(FixedLocator([1, 10, 100])); ax2.yaxis.set_major_formatter(FixedFormatter(["1", "10", "100"])); ax2.yaxis.set_minor_locator(NullLocator())
ax1.text(0.0, -0.44, "오탐: 무고장 6런·고장 런 주입 전 30구간에서 전 검출기 0. LiDAR 성김 mid 는 제안이 설계상 미경보(능력 손실 없음). 문턱: 무고장 짝수 rep 최대값.",
         transform=ax1.transAxes, fontsize=7.5, color="#8a8f99", va="top")
for ax in (ax1, ax2):
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
os.makedirs(os.path.join(RES, "figs"), exist_ok=True)
for ext in ("png", "pdf"): plt.savefig(os.path.join(RES, "figs", f"fig_vision_fdi.{ext}"))
print(os.path.join(RES, "figs", "fig_vision_fdi.png"))
