#!/usr/bin/env python3
"""lcl 세기 등급 모니터의 폐루프 효과 (2026-11-09 재튜닝 블록 A·B·C, MRM on, 제안 arm).
(a) 강우 파라미터 R 별 감독기 결정(주행 유지 / 갓길 대피 / 정지) — 사다리 C(1,2,10,15,40) + A(5) + B(25)
(b) 운용점(mid R=5, high R=25)에서 구 모니터(8월 캠페인) vs 세기 등급 모니터(11월) 결말과 열화 상태 주행거리
입력: results/results_1109_*.csv, results/results_0813_1513.csv  출력: results/figs/fig_lcl_graded.png/.pdf
"""
import csv, glob, collections, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"
plt.rcParams.update({"font.family": "STIXGeneral", "font.size": 11, "mathtext.fontset": "stix"})
SKIP = {"CARLA_DIED", "SETUP_FAIL", "INTERRUPTED", "DISK_FULL", "SCENARIO_ENDED"}   # SCENARIO_ENDED = 고장 미주입 하네스 실패
def cls(r):
    fs = (r.get("final_state") or "").split(":")[0]; oc = r["outcome"]
    if oc.startswith("ROUTE_COMPLETE") or fs == "NORMAL": return "cont"
    if oc in ("SHOULDER_SUCCESS", "PARKED_SUCCESS") or fs in ("MRM_PARKED", "MRM_MOVE"): return "move"
    return "stop"
def R_of(sev): return {"mid": 5.0, "high": 25.0}.get(sev) or float(sev.split(":")[0])
def mor(R): return 3.0 / (0.01 * R ** 0.6)
new = [r for p in sorted(glob.glob(f"{RES}/results_1109_*.csv")) for r in csv.DictReader(open(p))
       if r.get("fault") == "lcl" and r.get("method") == "ours" and r["outcome"] not in SKIP and r.get("final_state")]
old = [r for r in csv.DictReader(open(f"{RES}/results_0813_1513.csv")) if r["fault"] == "lcl" and r["method"] == "ours" and r["outcome"] not in SKIP]
byR = collections.defaultdict(collections.Counter)
for r in new: byR[R_of(r["severity"])][cls(r)] += 1
C = {"cont": ("white", "Continue driving"), "move": ("#c8c8c8", "Evacuation to shoulder (MRM_MOVE)"), "stop": ("#4d4d4d", "Stop deferral (MRM_DEFER)")}

fig, (a, b) = plt.subplots(1, 2, figsize=(13.5, 5.2), gridspec_kw=dict(width_ratios=[1.45, 1.0], wspace=0.35))
# (a) staircase by R
Rs = sorted(byR); xs = range(len(Rs))
for i, R in zip(xs, Rs):
    n = sum(byR[R].values()); bottom = 0.0
    for k in ("cont", "move", "stop"):
        v = byR[R][k]
        if v <= 0: continue
        h = v / n * 100; a.bar(i, h, bottom=bottom, width=0.62, color=C[k][0], edgecolor="black", linewidth=0.8)
        if h >= 8: a.text(i, bottom + h / 2, str(v), ha="center", va="center", fontsize=10, color="white" if k == "stop" else "black")
        bottom += h
    a.text(i, 102, f"$n$ = {n}", ha="center", va="bottom", fontsize=9)
a.set_xticks(list(xs)); a.set_xticklabels([f"{R:g}\n{mor(R):.0f} m" for R in Rs], fontsize=10)
a.set_xlabel("Rain parameter R  /  equivalent visibility (m)", fontsize=11); a.set_ylabel("Share of valid cases (%)", fontsize=11)
a.set_ylim(0, 112); a.set_yticks([0, 20, 40, 60, 80, 100])
for x_, lab in ((2, "mid"), (5, "high")): a.text(x_, 109, lab, ha="center", va="bottom", fontsize=9, color="gray")
a.set_title("(a) Supervisor decision vs. rain parameter (graded monitor, closed loop)", loc="left", fontsize=11)
# (b) old vs graded at operating points
cats = ["cont", "move", "stop"]
def dist(rows):
    c = collections.Counter(cls(r) for r in rows); n = sum(c.values()); return c, n
groups = [("mid (R = 5)", [r for r in old if r["severity"] == "mid"], [r for r in new if r["severity"] == "mid"]),
          ("high (R = 25)", [r for r in old if r["severity"] == "high"], [r for r in new if r["severity"] == "high"])]
pos = 0; ticks, labels = [], []
for gi, (name, o, nw) in enumerate(groups):
    for j, (lab, rows) in enumerate((("Fixed-score monitor\n(Aug. campaign)", o), ("Graded monitor\n(Nov. re-run)", nw))):
        c, n = dist(rows); bottom = 0.0; x = pos
        for k in cats:
            v = c[k]
            if v <= 0: continue
            h = v / n * 100; b.bar(x, h, bottom=bottom, width=0.7, color=C[k][0], edgecolor="black", linewidth=0.8)
            if h >= 8: b.text(x, bottom + h / 2, str(v), ha="center", va="center", fontsize=10, color="white" if k == "stop" else "black")
            bottom += h
        dd = [float(r["deg_dist_m"]) for r in rows if r.get("deg_dist_m") not in ("", None)]
        b.text(x, 102, f"$n$ = {n}\n{st.median(dd):.0f} m", ha="center", va="bottom", fontsize=8.5)
        ticks.append(x); labels.append(lab); pos += 1
    pos += 0.6
b.set_xticks(ticks); b.set_xticklabels(labels, fontsize=8.5)
b.set_ylim(0, 128); b.set_yticks([0, 20, 40, 60, 80, 100]); b.set_ylabel("Share of valid cases (%)", fontsize=11)
b.text(0.5, 119, "LiDAR clutter mid (R = 5)", ha="center", fontsize=9.5, color="gray"); b.text(3.1, 119, "LiDAR clutter high (R = 25)", ha="center", fontsize=9.5, color="gray")
b.set_title("(b) Operating points: fixed-score vs. graded monitor", loc="left", fontsize=11)
b.text(0.0, -0.3, "Numbers above bars: valid cases and median degraded-state driving distance (m).", transform=b.transAxes, fontsize=8.5, color="gray")
for ax in (a, b):
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
fig.legend(handles=[Patch(facecolor=C[k][0], edgecolor="black", label=C[k][1]) for k in cats], loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=3, frameon=True, fontsize=10)
fig.subplots_adjust(top=0.82, bottom=0.2, left=0.07, right=0.98)
for ext in ("png", "pdf"):
    out = f"{RES}/figs/fig_lcl_graded.{ext}"; fig.savefig(out, dpi=200, facecolor="white"); print(out)
print({R: dict(c) for R, c in sorted(byR.items())})
