#!/usr/bin/env python3
"""[2026-11-08] 베이스라인 FDI 비교 그림: (a) 고장별 검출률(Wilson 95% CI) (b) 검출 지연 분포(시뮬 시간), 검출기 5종.
입력: results/baseline_fdi/cases.csv (baseline_fdi_eval.py --report)  출력: results/figs/fig_baseline_fdi.png/.pdf"""
import os, sys, csv, math, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle; figstyle.apply({"font.size": 9})
import matplotlib.pyplot as plt
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
rows = [r for r in csv.DictReader(open(os.path.join(RES, "baseline_fdi", "cases.csv"))) if r["tag"].startswith("stock-") and r["fault"] != "nf"]
ORDER = [("gn", "mid"), ("gn", "high"), ("gm", "mid"), ("gm", "high"), ("gb", "mid"), ("imn", "mid"), ("imn", "high"), ("imb", "mid"), ("imb", "high"), ("imd", "mid"), ("imd", "high")]
LABEL = {"gn": "GNSS\n백색잡음", "gm": "GNSS\n상관편향", "gb": "GNSS\n두절", "imn": "IMU\n잡음", "imb": "IMU\n바이어스", "imd": "IMU\n드리프트"}
DET = [("b0_loc", "Autoware 측위 진단 (B0)", "#8a8f99", "//"), ("yu", "상태영역 χ² (Yu 2021 구조)", figstyle.C_NF, ""), ("gos_all", "EKF 뱅크 잔차 (Huang&Su 구조)", figstyle.C_MID, ""), ("ours", "제안 (감독기 재생)", figstyle.C_HIGH, "")]
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan, np.nan)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0, c - h), min(1, c + h)
groups = collections.OrderedDict((k, [r for r in rows if (r["fault"], r["sev"]) == k]) for k in ORDER)
groups = collections.OrderedDict((k, v) for k, v in groups.items() if v)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12.5, 7.6), gridspec_kw=dict(height_ratios=[1, 1], hspace=0.62))
X = np.arange(len(groups)); w = 0.19
for j, (key, lab, col, hatch) in enumerate(DET):
    ps, lo, hi = [], [], []
    for k, cs in groups.items():
        pool = [c for c in cs if c["b0loc_avail"] == "1"] if key == "b0_loc" else cs
        d = sum(1 for c in pool if c[f"det_{key}"] != ""); p, l, h = wilson(d, len(pool)); ps.append(p); lo.append(l); hi.append(h)
    ps, lo, hi = map(np.array, (ps, lo, hi)); xs = X + (j - 1.5) * w
    ax1.bar(xs, ps, w * 0.92, color=col, hatch=hatch, edgecolor="white", linewidth=0.8, label=lab, zorder=3)
    ax1.errorbar(xs, ps, yerr=[np.nan_to_num(ps - lo), np.nan_to_num(hi - ps)], fmt="none", ecolor=figstyle.INK, elinewidth=0.8, capsize=2, zorder=4)
    # 지연 분포 (검출된 케이스만)
    for i, (k, cs) in enumerate(groups.items()):
        d = [float(c[f"det_{key}"]) for c in cs if c[f"det_{key}"] != ""]
        if d:
            ax2.scatter(np.full(len(d), xs[i]) + np.random.default_rng(i).uniform(-w * 0.3, w * 0.3, len(d)), d, s=8, color=col, alpha=0.45, linewidths=0, zorder=3)
            ax2.plot([xs[i] - w * 0.4, xs[i] + w * 0.4], [np.median(d)] * 2, color=figstyle.INK, lw=1.4, zorder=4)
ax1.set_ylim(0, 1.08); ax1.set_ylabel("검출률 (Wilson 95% CI)"); ax1.set_xticks(X); ax1.set_xticklabels([f"{LABEL[f]}\n{s}" for f, s in groups], fontsize=7.5)
ax1.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=8, frameon=False); ax1.set_title("(a) 동일 순정 주행 bag 에서의 고장 검출률 (셀당 n = " + ", ".join(sorted({str(len(v)) for v in groups.values()})) + ")", loc="left", fontsize=10)
ax2.set_yscale("log"); ax2.set_ylabel("검출 지연 (s, 시뮬 시간, 로그)"); ax2.set_xticks(X); ax2.set_xticklabels([f"{LABEL[f]}\n{s}" for f, s in groups], fontsize=7.5)
ax2.set_title("(b) 검출된 케이스의 지연 (점: 개별 런, 가로선: 중앙값)", loc="left", fontsize=10)
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
ax2.yaxis.set_major_locator(FixedLocator([0.1, 1, 10, 100])); ax2.yaxis.set_major_formatter(FixedFormatter(["0.1", "1", "10", "100"])); ax2.yaxis.set_minor_locator(NullLocator())
for ax in (ax1, ax2):
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
os.makedirs(os.path.join(RES, "figs"), exist_ok=True)
for ext in ("png", "pdf"): plt.savefig(os.path.join(RES, "figs", f"fig_baseline_fdi.{ext}"))
print(os.path.join(RES, "figs", "fig_baseline_fdi.png"))
