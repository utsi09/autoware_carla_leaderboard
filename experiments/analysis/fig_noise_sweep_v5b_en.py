#!/usr/bin/env python3
"""fig_noise_sweep 의 (b) lcl 열을 v5b 세기 경로(α̂ 기반) 사다리(rep 40–43, 2026-11-09)로 교체한 판.
(a) lso·(c) imn 은 원본(lite 스윕 로그) 그대로. (b) 위: LiDAR 점수 q(세기 경로)·인지 건강도(융합), 아래: Autoware 재현율.
입력: results/noise_sweep_batch.log, results/noise_sweep_live.md(nf 기준), results/live/stock-lcl-*-def-r4[0-9]-*.csv
출력: results/figs/fig_noise_sweep_v5b.png / .pdf
"""
import os, sys, re, csv, glob, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle; figstyle.apply({"font.size": 9, "legend.fontsize": 8})
import matplotlib as mpl
mpl.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif", "STIXGeneral"], "mathtext.fontset": "stix",
                     "axes.grid": False, "axes.linewidth": 0.8, "axes.edgecolor": "black", "axes.labelcolor": "black", "text.color": "black",
                     "xtick.color": "black", "ytick.color": "black", "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
                     "xtick.minor.visible": False, "ytick.minor.visible": True, "xtick.major.size": 3.5, "ytick.major.size": 3.5, "ytick.minor.size": 2,
                     "lines.linewidth": 1.2, "legend.framealpha": 1.0, "legend.edgecolor": "black", "legend.fancybox": False,
                     "font.size": 9, "axes.labelsize": 9.5, "axes.titlesize": 10, "legend.fontsize": 8, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5})
figstyle.LW_LINE = 1.2
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
SKIP = {"CARLA_DIED", "SETUP_FAIL", "INTERRUPTED", "DISK_FULL"}
OP = {"lso": {"mid": 0.33, "high": 0.07}, "lcl": {"mid": 5.0, "high": 25.0}, "imn": {"mid": 0.5, "high": 1.5}}
THR = {"lso": 0.7, "lcl": 0.7, "imn": 0.5}
REF = "#8a8f99"; C_HEALTH = "#6b7280"
def mor(R): return 3.0 / (0.01 * R ** 0.6)

def f(x):
    try: return float(x)
    except Exception: return None

def parse(line):
    c = [x.strip() for x in line.split("|")[1:-1]]
    if len(c) < 19: return None
    return dict(fault=c[1], sev=c[2], rep=c[3], outcome=c[4], R_h=f(c[6]), R_far=f(c[7]),
                S_front=f(c[10]), S_perc=f(c[11]), e_lat=f(c[12]), ATE=f(c[13]), s_loc=f(c[16]))

rows = {}
for ln in open(f"{RES}/noise_sweep_batch.log", errors="replace"):
    if not ln.startswith("[live]"): continue
    r = parse(ln)
    if r is None or r["outcome"] in SKIP or r["fault"] not in OP or r["fault"] == "lcl": continue   # lcl 은 v5b 사다리로 교체
    r["x"] = f(r["sev"].split(":")[0]); rows[(r["fault"], r["sev"], r["rep"])] = r
rows = list(rows.values())
# v5b lcl 사다리 (rep 40–43; CARLA_DIED 로 고장 미주입된 런은 S_lidar>0.95 로 제외)
for p in sorted(glob.glob(f"{RES}/live/stock-lcl-*-def-r4[0-9]-*.csv")):
    m = re.match(r"stock-lcl-(\d+)_(\d+)-def-r(\d+)-(1108|1109|1110)_(\d{4})$", os.path.basename(p)[:-4])
    if not m or (m.group(4), m.group(5)) < ("1108", "2353"): continue
    r = next(csv.DictReader(open(p))); q = f(r["S_lidar_front"])
    if q is None or q > 0.95: continue
    rows.append(dict(fault="lcl", sev=f"{m.group(1)}:{m.group(2)}", rep=m.group(3), outcome="ok", x=float(m.group(1)),
                     R_h=f(r["R_h"]), R_far=f(r["R_far"]), S_front=q, S_perc=f(r["S_perc"]), e_lat=None, ATE=None, s_loc=None))

# (d) cn: 순정 매트릭스 mid/high + 2026-11-09 σ 스윕(stock-cn-<σ>-def-r0..2); 카메라 점수는 bag 추출(cam_scores.csv), 신호등 지표는 stock_outcomes.csv
SC = f"{RES}/derived"   # cam_scores.csv, gb_loc.csv (bag 추출 파생표)
def _load(pth):
    return {r["tag"]: r for r in csv.DictReader(open(pth))} if os.path.exists(pth) else {}
cam_tbl = _load(f"{SC}/cam_scores.csv"); out_tbl = _load(f"{RES}/stock_outcomes.csv")
tla_tbl = _load(f"{SC}/tl_approach_acc.csv")   # 접근 구간(60 m, 주행 중) 신호등 인식 정확도 — analysis/tl_approach_acc.py
nf_cn = []
for pth in sorted(glob.glob(f"{RES}/live/stock-cn-*.csv") + glob.glob(f"{RES}/live/stock-nf-*.csv")):
    tag = os.path.basename(pth)[:-4]
    m = re.match(r"stock-(cn|nf)-([^-]+)-(def|none|agg)-r(\d+)-(\d{4}_\d{4})$", tag)
    if not m: continue
    sev = m.group(2); x = {"mid": 15.0, "high": 30.0}.get(sev)
    if x is None:
        try: x = float(sev)
        except ValueError: x = 0.0
    c = cam_tbl.get(tag, {}); o = out_tbl.get(tag, {})
    if m.group(1) == "cn" and f(c.get("cam")) is not None and f(c.get("cam")) > 0.9: continue   # CARLA_DIED 등 고장 미주입 런 제외
    row = dict(fault=m.group(1), sev=sev, rep=m.group(4), npc=m.group(3), ladder=(sev not in ("mid", "high")), outcome="ok", x=(0.0 if m.group(1) == "nf" else x),
               cam=f(c.get("cam")), mg=f(o.get("missed_green")), tlacc=f(tla_tbl.get(tag, {}).get("acc")), ok=(None if f(o.get("missed_green")) is None else (1.0 if f(o.get("missed_green")) == 0 else 0.0)), S_front=None, R_h=None, R_far=None, e_lat=None, ATE=None, s_loc=None, S_perc=None)
    (nf_cn if m.group(1) == "nf" else rows).append(row)
def nfmed_cn(k, stat=np.median):
    v = [r[k] for r in nf_cn if r.get(k) is not None]; return (float(stat(v)), len(v)) if v else (None, 0)

nf = []
for ln in open(f"{RES}/noise_sweep_live.md", errors="replace"):
    if not ln.startswith("|"): continue
    r = parse(ln)
    if r and r["fault"] == "nf" and r["outcome"] not in SKIP and (r["e_lat"] or 0) <= 5: nf.append(r)

def nfmed(k):
    v = [r[k] for r in nf if r[k] is not None]
    return (float(np.median(v)), len(v)) if v else (None, 0)

def series(fault, key):
    g = collections.defaultdict(list)
    for r in rows:
        if fault == "cn" and key == "ok" and not (r.get("npc") == "def" and r.get("ladder")): continue   # (d) 아래 행: def 교통·t=10 주입 사다리 런만(프로토콜 통일; 캠페인 mid/high 는 27 s 주입·교통 3종)
        if r["fault"] == fault and r.get(key) is not None and r["x"] is not None: g[r["x"]].append(r[key])
    return g

def draw(ax, fault, key, color, marker, ls, label, stat=np.median):
    g = series(fault, key); xs = sorted(g)
    full = [x for x in xs if len(g[x]) >= 2]; single = [x for x in xs if len(g[x]) < 2]
    for x in xs:
        ax.scatter([x] * len(g[x]), g[x], s=6, color=color, alpha=0.3, linewidths=0, zorder=2)
    med = [float(stat(g[x])) for x in full]
    ax.plot(full, med, marker=marker, ls=ls, color=color, lw=1.2, ms=4.5, mec="black", mew=0.6, label=label, zorder=3)
    if single:
        ax.scatter(single, [g[x][0] for x in single], s=30, marker=marker, facecolors="white", edgecolors=color, linewidths=1.2, zorder=4)
    print(f"  {fault:3s} {key:7s} " + "  ".join(f"{x:g}:{stat(g[x]):.2f}(n={len(g[x])})" for x in xs))
    return xs, [len(g[x]) for x in xs], (full[-1] if full else None), (med[-1] if med else None)

fig, axes = plt.subplots(2, 4, figsize=(15.0, 7.0), sharex="col", gridspec_kw=dict(hspace=0.12, wspace=0.32))
OP["cn"] = {"mid": 15.0, "high": 30.0}; THR["cn"] = 0.7
# 색: 센서 계열당 한 색상, 지표 둘이면 진한/옅은 톤 (검증 팔레트: 파랑 #2a78d6 / 주황 #eb6834 / 청록 #1baf7a)
# IEEE/MATLAB 고전 팔레트
C_SCORE, C_THR = "black", "#A2142F"
C1, C2 = "#0072BD", "#D95319"        # LiDAR: recall 0–26 m (blue), 26–50 m (red-orange)
C_ATE, C_LAT = "#77AC30", "#7E2F8E"  # IMU: ATE (green), lateral P95 (purple)
C_CAM = "#4DBEEE"                    # Camera: success rate (light blue)
REF = "black"
COL = [("lso", "(a) LiDAR sparsification", "S_front", "LiDAR score", "LiDAR transmittance T"),
       ("lcl", "(b) LiDAR rain degradation", "S_front", "LiDAR score", "Rain parameter R  /  equivalent visibility (m)"),
       ("imn", "(c) IMU gyro noise", "s_loc", "Localization score", "Gyro noise σ (rad/s)"),
       ("cn", "(d) Camera noise", "cam", "Camera score", "Camera Gaussian noise σ")]

for j, (fault, title, skey, slabel, xlabel) in enumerate(COL):
    top, bot = axes[0, j], axes[1, j]
    xs, ns, xe, ye = draw(top, fault, skey, C_SCORE, "o", "-", slabel)
    top.set_ylim(-0.03, 1.06)
    top.axhline(THR[fault], color=C_THR, ls="-.", lw=1.0)
    m, n = nfmed_cn(skey) if fault == "cn" else nfmed(skey)
    if m is not None:
        top.axhline(m, color=REF, ls="--", lw=0.8)
    top.set_title(title, loc="left", fontsize=10, pad=16)
    top.set_ylabel("Monitor score (median)" if j == 0 else slabel)
    if fault in ("lso", "lcl"):
        draw(bot, fault, "R_h", C1, "o", "-", "Recall 0–26 m")
        draw(bot, fault, "R_far", C2, "s", "--", "Recall 26–50 m")
        bot.set_ylim(0, 1.06)
        if j == 0: bot.set_ylabel("Autoware perception recall\n(vs. CARLA ground truth, median)")
        m, n = nfmed("R_far")
        if m is not None: bot.axhline(m, color=REF, ls="--", lw=0.8)
    elif fault == "cn":
        draw(bot, fault, "ok", C_CAM, "D", "-", "Traffic-light recognition success", stat=np.mean)
        bot.set_ylim(-0.03, 1.06); bot.set_ylabel("Traffic-light recognition\nsuccess rate (share of runs)")
        m, n = nfmed_cn("ok", np.mean)
        if m is not None: bot.axhline(m, color=REF, ls="--", lw=0.8)
    else:
        draw(bot, fault, "ATE", C_ATE, "o", "-", "Trajectory error ATE")
        draw(bot, fault, "e_lat", C_LAT, "s", "--", "Lateral error P95")
        bot.set_yscale("log"); bot.set_ylim(0.02, 30); bot.set_ylabel("EKF position error (m, log)")
        m, n = nfmed("ATE")
        if m is not None: bot.axhline(m, color=REF, ls="--", lw=0.8)
    bot.set_xlabel(xlabel, fontsize=9.5)
    if fault == "lso": top.invert_xaxis()
    if fault == "lcl":
        top.set_xscale("log"); top.set_xlim(0.8, 50)
        lv = sorted({r["x"] for r in rows if r["fault"] == "lcl"})
        bot.xaxis.set_major_locator(FixedLocator(lv)); bot.xaxis.set_major_formatter(FixedFormatter([f"{v:g}\n{mor(v):.0f}" for v in lv])); bot.xaxis.set_minor_locator(NullLocator())
        bot.tick_params(axis="x", labelsize=7.5)
    if fault == "cn":
        lv = sorted({r["x"] for r in rows if r["fault"] == "cn"})
        top.set_xlim(0, 50); bot.xaxis.set_major_locator(FixedLocator(lv)); bot.xaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in lv])); bot.xaxis.set_minor_locator(NullLocator()); bot.tick_params(axis="x", labelsize=7.5)
    if fault == "imn":
        top.set_xscale("log"); top.set_xlim(0.04, 1.9)
        lv = sorted({r["x"] for r in rows if r["fault"] == "imn"})
        bot.xaxis.set_major_locator(FixedLocator(lv)); bot.xaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in lv])); bot.xaxis.set_minor_locator(NullLocator())
        bot.yaxis.set_major_locator(FixedLocator([0.1, 1, 10])); bot.yaxis.set_major_formatter(FixedFormatter(["0.1", "1", "10"])); bot.yaxis.set_minor_locator(NullLocator())
    for k, x in OP[fault].items():
        for ax in (top, bot): ax.axvline(x, color="gray", ls=(0, (1, 3)), lw=0.8, zorder=0)
        top.text(x, 1.02, k, transform=top.get_xaxis_transform(), ha="center", va="bottom", fontsize=8, color="black", style="italic")
    pass


from matplotlib.lines import Line2D
H = [Line2D([], [], color=C_SCORE, marker="o", ms=4.5, lw=1.2, mec="black", label="Monitor score (median of runs)"),
     Line2D([], [], color=C_SCORE, marker="o", ms=5.5, lw=0, mfc="white", mew=1.2, label="Open marker: single run (campaign operating point)"),
     Line2D([], [], color=REF, ls="--", lw=0.8, label="No-fault reference (median)"),
     Line2D([], [], color=C_THR, ls="-.", lw=1.0, label="Decision threshold"),
     Line2D([], [], color="gray", ls=(0, (1, 3)), lw=0.8, label="mid / high operating point"),
     Line2D([], [], color=C1, marker="o", ms=4.5, lw=1.2, mec="black", mew=0.6, label="LiDAR: Autoware recall 0–26 m"),
     Line2D([], [], color=C2, marker="s", ms=4.5, lw=1.2, ls="--", mec="black", mew=0.6, label="LiDAR: Autoware recall 26–50 m"),
     Line2D([], [], color=C_ATE, marker="o", ms=4.5, lw=1.2, mec="black", mew=0.6, label="IMU: EKF trajectory error (ATE)"),
     Line2D([], [], color=C_LAT, marker="s", ms=4.5, lw=1.2, ls="--", mec="black", mew=0.6, label="IMU: EKF lateral error (P95)"),
     Line2D([], [], color=C_CAM, marker="D", ms=4.5, lw=1.2, mec="black", mew=0.6, label="Camera: traffic-light recognition success rate")]
fig.legend(handles=H, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=5, fontsize=8, frameon=True, edgecolor="black", fancybox=False, handlelength=2.6, columnspacing=1.6)
fig.subplots_adjust(top=0.875)
os.makedirs(f"{RES}/figs", exist_ok=True)
for ext in ("png", "pdf"):
    out = f"{RES}/figs/fig_noise_sweep_v5b_en.{ext}"; plt.savefig(out); print(out)
