#!/usr/bin/env python3
"""노이즈 사다리 lite 스윕 그림 (2행 × 3열): 고장 세기 → 위 행 감시기 점수, 아래 행 실제 성능.
입력: results/noise_sweep_batch.log 의 [live] 줄 (lite 스윕, 제안 방식, 수준당 n=3; mid/high 운용점은 n=1)
      results/noise_sweep_live.md 의 nf 줄 (무고장 기준 중앙값)
출력: results/figs/fig_noise_sweep.png / .pdf
[live] 열: idx fault sev rep outcome wall R_h R_far D_det FP S_front S_perc e_lat ATE NVTL ndt_hz s_loc n_pairs n_frames
"""
import os, sys, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle; figstyle.apply({"font.size": 9, "legend.fontsize": 8})
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
SKIP = {"CARLA_DIED", "SETUP_FAIL", "INTERRUPTED", "DISK_FULL"}
OP = {"lso": {"mid": 0.33, "high": 0.07}, "lcl": {"mid": 5.0, "high": 25.0}, "imn": {"mid": 0.5, "high": 1.5}}
THR = {"lso": 0.7, "lcl": 0.7, "imn": 0.5}
REF = "#8a8f99"


def f(x):
    try: return float(x)
    except Exception: return None


def parse(line):
    c = [x.strip() for x in line.split("|")[1:-1]]
    if len(c) < 19: return None
    return dict(fault=c[1], sev=c[2], rep=c[3], outcome=c[4], R_h=f(c[6]), R_far=f(c[7]),
                S_front=f(c[10]), e_lat=f(c[12]), ATE=f(c[13]), s_loc=f(c[16]))


rows = {}
for ln in open(f"{RES}/noise_sweep_batch.log", errors="replace"):
    if not ln.startswith("[live]"): continue
    r = parse(ln)
    if r is None or r["outcome"] in SKIP or r["fault"] not in OP: continue
    r["x"] = f(r["sev"].split(":")[0])
    rows[(r["fault"], r["sev"], r["rep"])] = r          # 같은 셀 재실행은 마지막 것
rows = list(rows.values())

nf = []
for ln in open(f"{RES}/noise_sweep_live.md", errors="replace"):
    if not ln.startswith("|"): continue
    r = parse(ln)
    if r and r["fault"] == "nf" and r["outcome"] not in SKIP and (r["e_lat"] or 0) <= 5: nf.append(r)   # 측위 발산한 nf 무효 런 제외


def nfmed(k):
    v = [r[k] for r in nf if r[k] is not None]
    return (float(np.median(v)), len(v)) if v else (None, 0)


def series(fault, key):
    g = collections.defaultdict(list)
    for r in rows:
        if r["fault"] == fault and r[key] is not None and r["x"] is not None: g[r["x"]].append(r[key])
    return g


def draw(ax, fault, key, color, marker, ls, label):
    g = series(fault, key); xs = sorted(g)
    full = [x for x in xs if len(g[x]) >= 2]; single = [x for x in xs if len(g[x]) < 2]
    for x in xs:                                                    # 개별 런
        ax.scatter([x] * len(g[x]), g[x], s=9, color=color, alpha=0.35, linewidths=0, zorder=2)
    med = [float(np.median(g[x])) for x in full]
    ax.plot(full, med, marker=marker, ls=ls, color=color, lw=figstyle.LW_LINE, ms=5.5, mec="white", mew=0.8, label=label, zorder=3)
    if single:                                                      # n=1 운용점: 속 빈 표식, 선에 잇지 않음
        ax.scatter(single, [g[x][0] for x in single], s=38, marker=marker, facecolors="white", edgecolors=color, linewidths=1.4, zorder=4)
    print(f"  {fault:3s} {key:7s} " + "  ".join(f"{x:g}:{np.median(g[x]):.2f}(n={len(g[x])})" for x in xs))
    return xs, [len(g[x]) for x in xs], (full[-1] if full else None), (med[-1] if med else None)


fig, axes = plt.subplots(2, 3, figsize=(12.6, 6.4), sharex="col", gridspec_kw=dict(hspace=0.10, wspace=0.28))
C_SCORE, C1, C2, C_THR = figstyle.INK, figstyle.C_NF, figstyle.C_MID, figstyle.C_HIGH
COL = [("lso", "(a) LiDAR 성김 (lso)", "S_front", "LiDAR 점수", "LiDAR 투과율 T (1 = 정상) → 나쁨"),
       ("lcl", "(b) LiDAR 비 클러터 (lcl)", "S_front", "LiDAR 점수", "강우량 (mm/h) → 나쁨"),
       ("imn", "(c) IMU 자이로 잡음 (imn)", "s_loc", "위치추정 점수", "자이로 잡음 σ (rad/s) → 나쁨")]

for j, (fault, title, skey, slabel, xlabel) in enumerate(COL):
    top, bot = axes[0, j], axes[1, j]
    # ── 위 행: 감시기 점수
    xs, ns, xe, ye = draw(top, fault, skey, C_SCORE, "o", "-", slabel)
    top.set_ylim(-0.03, 1.06)
    top.axhline(THR[fault], color=C_THR, ls=":", lw=1.1)
    tx, tha = (0.985, "right") if fault == "lcl" else (0.015, "left")
    top.text(tx, THR[fault] + 0.025, f"판단 문턱 {THR[fault]}", color=C_THR, fontsize=7.5, ha=tha, va="bottom", transform=top.get_yaxis_transform())
    m, n = nfmed(skey)
    if m is not None:
        top.axhline(m, color=REF, ls="--", lw=0.9)
        if fault == "lcl": top.text(0.015, m - 0.025, f"무고장 중앙값 {m:.2f} (n={n})", color=REF, fontsize=7.5, ha="left", va="top", transform=top.get_yaxis_transform())
        else: top.text(0.985, m + 0.012, f"무고장 중앙값 {m:.2f} (n={n})", color=REF, fontsize=7.5, ha="right", va="bottom", transform=top.get_yaxis_transform())
    top.set_title(title, loc="left", fontsize=10, pad=14)
    if j == 0: top.set_ylabel("감시기 점수 (중앙값)")
    else: top.set_ylabel(slabel)
    # ── 아래 행: 실제 성능
    if fault in ("lso", "lcl"):
        _, _, x1, y1 = draw(bot, fault, "R_h", C1, "o", "-", "재현율 0–26 m")
        _, _, x2, y2 = draw(bot, fault, "R_far", C2, "s", "--", "재현율 26–50 m")
        bot.set_ylim(0, 1.06)
        if j == 0: bot.set_ylabel("Autoware 인식 재현율\n(CARLA 정답 대비, 중앙값)")
        m, n = nfmed("R_far")
        if m is not None:
            bot.axhline(m, color=REF, ls="--", lw=0.9)
            bot.text(0.985, m - 0.025, f"무고장 26–50 m 재현율 {m:.2f}", color=REF, fontsize=7.5, ha="right", va="top", transform=bot.get_yaxis_transform())
        bot.legend(loc="center right" if fault == "lcl" else "lower left", ncol=1, handlelength=2.2, borderaxespad=0.6)
    else:
        _, _, x1, y1 = draw(bot, fault, "ATE", C1, "o", "-", "궤적 오차 ATE")
        _, _, x2, y2 = draw(bot, fault, "e_lat", C2, "s", "--", "횡오차 P95")
        bot.set_yscale("log"); bot.set_ylim(0.02, 30)
        bot.set_ylabel("EKF 위치 오차 (m, 로그)")
        m, n = nfmed("ATE")
        if m is not None:
            bot.axhline(m, color=REF, ls="--", lw=0.9)
            bot.text(0.985, m * 1.12, f"무고장 ATE {m:.2f} m", color=REF, fontsize=7.5, ha="right", va="bottom", transform=bot.get_yaxis_transform())
        bot.legend(loc="upper left", handlelength=2.2, borderaxespad=0.6)
    # ── x축·운용점
    runs = ", ".join(f"{x:g}:{c}" for x, c in zip(xs, ns))
    bot.set_xlabel(xlabel + f"\n수준별 런 수 — {runs}", fontsize=8)
    if fault == "lso": top.invert_xaxis()
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

# (b) 핵심 메시지: 기존 LiDAR 점수가 강우 세기에 무반응
axes[0, 1].annotate("기존 점수: 1–40 mm/h 전 구간 0.20\n→ 세기 구분 없음\n(확장안에서 재보정)", xy=(15, 0.20), xytext=(11, 0.40),
                    fontsize=7.8, color=figstyle.INK, ha="left", va="bottom",
                    arrowprops=dict(arrowstyle="-", color=REF, lw=0.8))
axes[0, 0].text(0.98, 0.04, "속 빈 표식: n=1 (본 캠페인 mid/high 운용점)\n작은 점: 개별 런", transform=axes[0, 0].transAxes,
                fontsize=7.2, color=REF, ha="right", va="bottom")

os.makedirs(f"{RES}/figs", exist_ok=True)
for ext in ("png", "pdf"):
    out = f"{RES}/figs/fig_noise_sweep.{ext}"; plt.savefig(out); print(out)
