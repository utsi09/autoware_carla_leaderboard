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
        ax.scatter([x] * len(g[x]), g[x], s=9, color=color, alpha=0.35, linewidths=0, zorder=2)
    med = [float(stat(g[x])) for x in full]
    ax.plot(full, med, marker=marker, ls=ls, color=color, lw=figstyle.LW_LINE, ms=5.5, mec="white", mew=0.8, label=label, zorder=3)
    if single:
        ax.scatter(single, [g[x][0] for x in single], s=38, marker=marker, facecolors="white", edgecolors=color, linewidths=1.4, zorder=4)
    print(f"  {fault:3s} {key:7s} " + "  ".join(f"{x:g}:{stat(g[x]):.2f}(n={len(g[x])})" for x in xs))
    return xs, [len(g[x]) for x in xs], (full[-1] if full else None), (med[-1] if med else None)

fig, axes = plt.subplots(2, 4, figsize=(16.8, 6.6), sharex="col", gridspec_kw=dict(hspace=0.10, wspace=0.30))
OP["cn"] = {"mid": 15.0, "high": 30.0}; THR["cn"] = 0.7
C_SCORE, C1, C2, C_THR = figstyle.INK, figstyle.C_NF, figstyle.C_MID, figstyle.C_HIGH
COL = [("lso", "(a) LiDAR 성김 (lso)", "S_front", "LiDAR 점수", "LiDAR 투과율 T (1 = 정상) → 나쁨"),
       ("lcl", "(b) LiDAR 강우 열화 (lcl)", "S_front", "LiDAR 점수", "열화 세기 R / 등가 시정 (m) → 나쁨"),
       ("imn", "(c) IMU 자이로 잡음 (imn)", "s_loc", "위치추정 점수", "자이로 잡음 σ (rad/s) → 나쁨"),
       ("cn", "(d) 카메라 잡음 (cn)", "cam", "카메라 점수", "카메라 가우시안 잡음 σ → 나쁨")]

for j, (fault, title, skey, slabel, xlabel) in enumerate(COL):
    top, bot = axes[0, j], axes[1, j]
    xs, ns, xe, ye = draw(top, fault, skey, C_SCORE, "o", "-", slabel)
    top.set_ylim(-0.03, 1.06)
    top.axhline(THR[fault], color=C_THR, ls=":", lw=1.1)
    tx, tha = (0.985, "right") if fault == "lcl" else (0.015, "left")
    thr_txt = f"판단 문턱 {THR[fault]}"
    top.text(tx, THR[fault] + 0.025, thr_txt, color=C_THR, fontsize=7.5, ha=tha, va="bottom", transform=top.get_yaxis_transform())
    m, n = nfmed_cn(skey) if fault == "cn" else nfmed(skey)
    if m is not None:
        top.axhline(m, color=REF, ls="--", lw=0.9)
        if fault == "lcl": top.text(0.985, m - 0.025, f"무고장 중앙값 {m:.2f} (n={n})", color=REF, fontsize=7.5, ha="right", va="top", transform=top.get_yaxis_transform())
        else: top.text(0.985, m + 0.012, f"무고장 중앙값 {m:.2f} (n={n})", color=REF, fontsize=7.5, ha="right", va="bottom", transform=top.get_yaxis_transform())
    top.set_title(title, loc="left", fontsize=10, pad=14)
    top.set_ylabel("감시기 점수 (중앙값)" if j == 0 else slabel)
    if fault in ("lso", "lcl"):
        draw(bot, fault, "R_h", C1, "o", "-", "재현율 0–26 m")
        draw(bot, fault, "R_far", C2, "s", "--", "재현율 26–50 m")
        bot.set_ylim(0, 1.06)
        if j == 0: bot.set_ylabel("Autoware 인식 재현율\n(CARLA 정답 대비, 중앙값)")
        m, n = nfmed("R_far")
        if m is not None:
            bot.axhline(m, color=REF, ls="--", lw=0.9)
            bot.text(0.985, m - 0.025, f"무고장 26–50 m 재현율 {m:.2f}", color=REF, fontsize=7.5, ha="right", va="top", transform=bot.get_yaxis_transform())
        bot.legend(loc="center right" if fault == "lcl" else "lower left", ncol=1, handlelength=2.2, borderaxespad=0.6)
    elif fault == "cn":
        draw(bot, fault, "ok", C1, "o", "-", "녹색 신호 인식 성공률 (런 비율)", stat=np.mean)
        bot.set_ylim(-0.03, 1.06); bot.set_ylabel("신호등 인식 성공률 (런 비율)")
        m, n = nfmed_cn("ok", np.mean)
        if m is not None:
            bot.axhline(m, color=REF, ls="--", lw=0.9)
            bot.text(0.985, m - 0.025, f"무고장 {m:.2f}", color=REF, fontsize=7.5, ha="right", va="top", transform=bot.get_yaxis_transform())
        bot.legend(loc="lower left", handlelength=2.2, borderaxespad=0.6)
    else:
        draw(bot, fault, "ATE", C1, "o", "-", "궤적 오차 ATE")
        draw(bot, fault, "e_lat", C2, "s", "--", "횡오차 P95")
        bot.set_yscale("log"); bot.set_ylim(0.02, 30); bot.set_ylabel("EKF 위치 오차 (m, 로그)")
        m, n = nfmed("ATE")
        if m is not None:
            bot.axhline(m, color=REF, ls="--", lw=0.9)
            bot.text(0.985, m * 1.12, f"무고장 ATE {m:.2f} m", color=REF, fontsize=7.5, ha="right", va="bottom", transform=bot.get_yaxis_transform())
        bot.legend(loc="upper left", handlelength=2.2, borderaxespad=0.6)
    runs = ", ".join(f"{x:g}:{c}" for x, c in zip(xs, ns))
    bot.set_xlabel(xlabel + f"\n수준별 런 수 — {runs}", fontsize=8)
    if fault == "lso": top.invert_xaxis()
    if fault == "lcl":
        top.set_xscale("log"); top.set_xlim(0.8, 50)
        lv = sorted({r["x"] for r in rows if r["fault"] == "lcl"})
        bot.xaxis.set_major_locator(FixedLocator(lv)); bot.xaxis.set_major_formatter(FixedFormatter([f"{v:g}\n{mor(v):.0f}" for v in lv])); bot.xaxis.set_minor_locator(NullLocator())
        bot.tick_params(axis="x", labelsize=7.5)
    if fault == "cn":
        lv = sorted({r["x"] for r in rows if r["fault"] == "cn"})
        top.set_xlim(0, 50); bot.xaxis.set_major_locator(FixedLocator(lv)); bot.xaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in lv])); bot.xaxis.set_minor_locator(NullLocator())
    if fault == "imn":
        top.set_xscale("log"); top.set_xlim(0.04, 1.9)
        lv = sorted({r["x"] for r in rows if r["fault"] == "imn"})
        bot.xaxis.set_major_locator(FixedLocator(lv)); bot.xaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in lv])); bot.xaxis.set_minor_locator(NullLocator())
        bot.yaxis.set_major_locator(FixedLocator([0.1, 1, 10])); bot.yaxis.set_major_formatter(FixedFormatter(["0.1", "1", "10"])); bot.yaxis.set_minor_locator(NullLocator())
    for k, x in OP[fault].items():
        for ax in (top, bot): ax.axvline(x, color=REF, ls=(0, (1, 3)), lw=0.8, zorder=0)
        top.text(x, 1.012, k, transform=top.get_xaxis_transform(), ha="center", va="bottom", fontsize=7.5, color=REF)
    for ax in (top, bot):
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)

axes[0, 0].text(0.98, 0.04, "속 빈 표식: n=1 (본 캠페인 mid/high 운용점)\n작은 점: 개별 런", transform=axes[0, 0].transAxes,
                fontsize=7.2, color=REF, ha="right", va="bottom")

os.makedirs(f"{RES}/figs", exist_ok=True)
for ext in ("png", "pdf"):
    out = f"{RES}/figs/fig_noise_sweep_v5b.{ext}"; plt.savefig(out); print(out)
