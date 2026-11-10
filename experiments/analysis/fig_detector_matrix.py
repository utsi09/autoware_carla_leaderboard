#!/usr/bin/env python3
"""검출기 비교 통합 — 고장 조건 × 검출기 '검출률 행렬' (IEEE 스타일) + 마크다운 표.
자료: results/baseline_fdi/cases.csv(항법, 셀당 45), results/raw_vision/cases.csv(비전, 셀당 5), results/alibi/cases_v2_maxthr.csv(Online MMD, nf 최대값 문턱),
      results/radas/report.md 수치(RADAS 이식, 셀당 1). 셀 = 검출 k/n (중앙 지연 s); 회색 빗금 = 해당 센서를 다루지 않음/미실행.
출력: results/figs/fig_detector_matrix.{png,pdf}, results/figs/detector_matrix.md"""
import os, sys, csv, collections, statistics as st, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib as mpl; mpl.use("Agg")
mpl.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif", "STIXGeneral"], "mathtext.fontset": "stix",
                     "axes.linewidth": 0.8, "font.size": 9})
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
ROWS = [("lso", "mid", "LiDAR sparsification (mid)"), ("lso", "high", "LiDAR sparsification (high)"), ("lcl", "mid", "LiDAR clutter (mid)"), ("lcl", "high", "LiDAR clutter (high)"), ("lf", "mid", "LiDAR death"),
        ("cn", "mid", "Camera noise (mid)"), ("cn", "high", "Camera noise (high)"), ("cf", "mid", "Camera death"),
        ("gn", "mid", "GNSS position noise (mid)"), ("gn", "high", "GNSS position noise (high)"), ("gm", "mid", "GNSS correlated bias (mid)"), ("gm", "high", "GNSS correlated bias (high)"), ("gb", "mid", "GNSS outage"),
        ("imn", "mid", "IMU gyro noise (mid)"), ("imn", "high", "IMU gyro noise (high)"), ("imb", "mid", "IMU gyro bias (mid)"), ("imb", "high", "IMU gyro bias (high)"), ("imd", "mid", "IMU bias ramp (mid)"), ("imd", "high", "IMU bias ramp (high)")]
COLS = [("b0", "Autoware\nbuilt-in\ndiagnostics"), ("won", "Won 2023\nLiDAR\nbitmap"), ("zh", "Zhang 2024\nLiDAR\ndistribution"), ("lee", "Lee 2022\ncamera\nCNN"),
        ("yu", "Yu 2021\nstate\nχ² test"), ("gos", "Huang & Su\nEKF\nresidual"), ("radas", "RADAS\nstream\nrate"), ("mmd", "Alibi Detect\nonline MMD\n(nf-calibrated)"), ("ours", "Proposed")]
cell = {}   # (fault, sev, col) -> (k, n, median latency or None)
def put(key, dets):
    d = [float(x) for x in dets if x not in ("", None, "nan")]
    cell[key] = (len(d), len(dets), st.median(d) if d else None)
# navigation + cf/lf (baseline_fdi)
nav = collections.defaultdict(lambda: collections.defaultdict(list))
for r in csv.DictReader(open(f"{RES}/baseline_fdi/cases.csv")):
    if not r["tag"].startswith("stock-") or r["sev"] not in ("mid", "high"): continue
    k = (r["fault"], r["sev"])
    nav[k]["yu"].append(r["det_yu"]); nav[k]["gos"].append(r["det_gos_all"]); nav[k]["ours"].append(r["det_ours"])
    if r.get("b0loc_avail") == "1": nav[k]["b0"].append(r["det_b0_loc"])
for k, d in nav.items():
    for c, v in d.items(): put((k[0], k[1], c), v)
# vision (raw_vision)
vis = collections.defaultdict(lambda: collections.defaultdict(list))
for r in csv.DictReader(open(f"{RES}/raw_vision/cases.csv")):
    if r["fault"] == "nf": continue
    k = (r["fault"], r["sev"])
    vis[k]["won"].append(r["det_won"]); vis[k]["zh"].append(r["det_zh"]); vis[k]["lee"].append(r["det_lee"]); vis[k]["b0"].append(r["det_b0_perc"])
    if (k[0], k[1], "ours") not in cell: vis[k]["ours"].append(r["det_ours"])
for k, d in vis.items():
    for c, v in d.items(): put((k[0], k[1], c), v)
# Alibi MMD (variant a)
mmd = collections.defaultdict(list)
for r in csv.DictReader(open(f"{RES}/alibi/cases_v2_maxthr.csv")):
    if r["fault"] == "nf": continue
    mmd[(r["fault"], r["sev"])].append(r["det"])
for k, v in mmd.items(): put((k[0], k[1], "mmd"), v)
# RADAS (5 runs)
for (f, s, det) in (("lf", "mid", 3.8), ("cf", "mid", 2.4), ("lso", "high", None), ("gn", "high", None), ("imn", "mid", None)):
    cell[(f, s, "radas")] = (1 if det else 0, 1, det)
# table
lines = ["# 검출기 비교 행렬 — 검출 k/n (중앙 지연 s)", "", "| 조건 | " + " | ".join(c[1].replace("\n", " ") for c in COLS) + " |", "|---|" + "---|" * len(COLS)]
for f, s, lab in ROWS:
    cells = []
    for c, _ in COLS:
        v = cell.get((f, s, c))
        cells.append("–" if v is None else (f"{v[0]}/{v[1]}" + (f" ({v[2]:.1f})" if v[2] is not None else "")))
    lines.append(f"| {lab} | " + " | ".join(cells) + " |")
lines += ["", "항법·cf·lf 열(Autoware 진단·Yu·Huang&Su·제안)은 순정 bag 재생 셀당 45런; 비전 열(Won·Zhang·Lee)은 원시 기록 셀당 5런; Alibi Online MMD 는 센서별 특징에 무고장 보정 문턱(변형 a), 셀당 5–6런; RADAS 이식은 조건당 1런. '–' = 해당 센서를 다루지 않거나 미실행. 제안의 lso-mid 0/5 는 설계(능력 손실 없음). 오탐: 항법 평가(무고장 홀수 rep 26런 + 주입 전 창 597) 제안 1·Autoware 진단 1(같은 런)·Yu 0·Huang&Su 0; 비전 평가(무고장 3런 + 창 30) 전부 0; Alibi(nf 보정) 무고장 런×센서 8회 중 3회 경보; RADAS 주입 전 구간 5회 중 0. (Alibi 기본 문턱 변형은 전 런 경보라 제외.)"]
open(f"{RES}/figs/detector_matrix.md", "w").write("\n".join(lines) + "\n")
# figure
fig, ax = plt.subplots(figsize=(12.5, 8.2))
nR, nC = len(ROWS), len(COLS)
for i, (f, s, lab) in enumerate(ROWS):
    for j, (c, _) in enumerate(COLS):
        v = cell.get((f, s, c)); y = nR - 1 - i
        if v is None:
            ax.add_patch(Rectangle((j, y), 1, 1, facecolor="#f2f2f2", edgecolor="white", hatch="///", linewidth=0.8)); continue
        k, n, lat = v; rate = k / n if n else 0
        col = plt.cm.Blues(0.15 + 0.75 * rate) if n else "#f2f2f2"
        ax.add_patch(Rectangle((j, y), 1, 1, facecolor=col, edgecolor="white", linewidth=0.8))
        txt = f"{k}/{n}" + (f"\n{lat:.1f} s" if lat is not None else ""); 
        ax.text(j + 0.5, y + 0.5, txt, ha="center", va="center", fontsize=8.2, color="white" if rate > 0.55 else "black")
ax.set_xlim(0, nC); ax.set_ylim(0, nR); ax.set_xticks(np.arange(nC) + 0.5); ax.set_xticklabels([c[1] for c in COLS], fontsize=8.5)
ax.set_yticks(np.arange(nR) + 0.5); ax.set_yticklabels([r[2] for r in ROWS][::-1], fontsize=9)
ax.tick_params(length=0); ax.xaxis.tick_top()
for yb in (14, 11, 6):   # group separators: lidar | camera | gnss | imu  (row index from bottom)
    ax.axhline(yb, color="black", lw=0.8)
for xb in (1, 4, 6, 8): ax.axvline(xb, color="black", lw=0.8)
for sp in ax.spines.values(): sp.set_linewidth(0.8)
foot = ("Cell: detections / runs (median latency, simulation s).  Hatched: detector does not consume that sensor or was not run.\n"
        "Navigation rows and camera/LiDAR death: 45 runs per cell (bag replay); LiDAR/camera degradation rows: 5 runs (raw 2 Hz recordings); Alibi MMD: 5–6; RADAS: 1.\n"
        "Proposed lso-mid 0/5 is by design (no capability loss, no intervention).\n"
        "False alarms — navigation evaluation (26 no-fault runs + 597 pre-injection windows): Proposed 1, Autoware diag. 1 (same run), Yu 0, Huang & Su 0;\n"
        "LiDAR/camera evaluation (3 no-fault runs + 30 windows): 0 for all;  Alibi (nf-calibrated): 3 of 8 no-fault run×sensor evaluations;  RADAS: 0 of 5 pre-injection windows.")
ax.text(0, -0.35, foot, fontsize=7.8, color="black", va="top", linespacing=1.45)
plt.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(f"{RES}/figs/fig_detector_matrix.{ext}", dpi=200, bbox_inches="tight", facecolor="white")
print("\n".join(lines[:6])); print("...", f"{RES}/figs/fig_detector_matrix.png")
