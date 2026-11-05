#!/usr/bin/env python3
"""노이즈 사다리 확장 그림: 위 = 건강도 점수 vs 실제 recall/측위오차 (fig_sweep_score_vs_capability 와 동일),
   아래 = recall 밖의 부작용 — 고장이 만든 허위 검출/초(정적 물체 마스크 제외), 허위 정지 시간, 급제동 횟수, 추적 ID 교체/분.
입력: results/side_effects.csv (side_effects.py), [live] 줄 (점수·recall)   출력: results/figs/fig_sweep_side_effects.png
"""
import csv, math, collections, statistics as st, importlib.util, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results")
spec = importlib.util.spec_from_file_location("fsc", Path(__file__).parent / "fig_sweep_score_vs_capability.py")
LEVEL = {("lso", "mid"): 0.33, ("lso", "high"): 0.07, ("lcl", "mid"): 5.0, ("lcl", "high"): 25.0, ("imn", "mid"): 0.5, ("imn", "high"): 1.5}

def level_of(tag):
    s = tag[6:] if tag.startswith("stock-") else tag
    p = s.split("-"); f, lv = p[0], p[1]
    if f == "nf": return "nf", None
    if (f, lv) in LEVEL: return f, LEVEL[(f, lv)]
    try: return f, float(lv.split("_")[0])
    except ValueError: return f, None

rows = list(csv.DictReader(open(RES / "side_effects.csv")))
def fnum(x):
    try: return float(x)
    except Exception: return None
SE = [("FP_novel_s", "phantom detections / s\n(outside fault-free static mask)"), ("phantom_stop_s", "unexplained stop time (s)\n(no signal, nothing ahead)"),
      ("hard_brakes", "hard-brake commands\n(< -3 m/s²)")]   # track_churn: 추적 스탬프 정렬 수정 후 추가
nf_rows = [r for r in rows if level_of(r["tag"])[0] == "nf" and "nf-mid" in r["tag"]]
def agg(fault, key):
    g = collections.defaultdict(list)
    for r in rows:
        f, lv = level_of(r["tag"])
        if f != fault or lv is None: continue
        v = fnum(r.get(key)); 
        if v is not None: g[lv].append(v)
    xs = sorted(g); return xs, [float(np.median(g[x])) for x in xs], [float(np.percentile(g[x], 25)) for x in xs], [float(np.percentile(g[x], 75)) for x in xs]
def nf_ref(key):
    v = [fnum(r.get(key)) for r in nf_rows]; v = [x for x in v if x is not None]
    return float(np.median(v)) if v else None

plt.rcParams.update({"font.family": "serif", "font.size": 9})
fig, axes = plt.subplots(len(SE), 3, figsize=(13, 2.3 * len(SE)), sharex="col")
cols = [("lso", "LiDAR transmittance T  →  worse", True, False), ("lcl", "rain rate (mm/h)  →  worse", False, False), ("imn", "gyro noise σ (rad/s)  →  worse", False, True)]
for j, (fault, xlabel, invert, logx) in enumerate(cols):
    for i, (key, lab) in enumerate(SE):
        ax = axes[i][j]
        xs, m, lo, hi = agg(fault, key)
        if xs:
            ax.plot(xs, m, "o-", color="black", ms=4); ax.fill_between(xs, lo, hi, color="black", alpha=0.12, lw=0)
        ref = nf_ref(key)
        if ref is not None:
            ax.axhline(ref, color="#2f6bb0", ls=":", lw=1.2); ax.text(0.02, 0.95, f"fault-free median {ref:g}", transform=ax.transAxes, color="#2f6bb0", fontsize=7, va="top")
        if j == 0: ax.set_ylabel(lab, fontsize=8)
        if i == 0: ax.set_title({"lso": "(a) LiDAR sparsification", "lcl": "(b) LiDAR clutter / rain", "imn": "(c) IMU gyro noise"}[fault], loc="left", fontsize=10)
        if invert and not ax.xaxis_inverted(): ax.invert_xaxis()
        if logx: ax.set_xscale("log")
        ax.grid(alpha=0.3)
        if i == len(SE) - 1: ax.set_xlabel(xlabel)
fig.suptitle("Side effects beyond recall along the noise ladder (median, IQR band; blue dotted = fault-free stock runs, n=15)", fontsize=9)
plt.tight_layout()
out = RES / "figs" / "fig_sweep_side_effects.png"; plt.savefig(out, dpi=200, bbox_inches="tight"); print(out)
