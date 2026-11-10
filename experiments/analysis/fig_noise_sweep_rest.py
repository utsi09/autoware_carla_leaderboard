#!/usr/bin/env python3
"""fig_noise_sweep 과 같은 틀로 '나머지 고장 유형'을 그린다 (2026-11-09).
위 행 = 감시기 점수, 아래 행 = 실제 성능. 자료 = 11월 순정 매트릭스(results/live/stock-*.csv, 수준당 ≈45런) + nf,
cn 은 2026-11-09 σ 스윕(stock-cn-<σ>-def-r0..2) 포함. 카메라 점수는 bag 추출(cam_scores.csv), gb 위치추정 점수는 재계산(gb_loc.csv).
출력: results/figs/fig_noise_sweep_rest_{sensor,nav}.png/.pdf
"""
import os, sys, re, csv, glob, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle; figstyle.apply({"font.size": 9, "legend.fontsize": 8})
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
SC = f"{RES}/derived"   # cam_scores.csv, gb_loc.csv (bag 추출 파생표)
REF = "#8a8f99"; C_SCORE, C1, C2, C_THR = figstyle.INK, figstyle.C_NF, figstyle.C_MID, figstyle.C_HIGH
SEV = {"cn": {"mid": 15.0, "high": 30.0}, "gn": {"mid": 1.0, "high": 2.5}, "gm": {"mid": 3.0, "high": 8.0},
       "imb": {"mid": 0.3, "high": 1.0}, "imd": {"mid": 0.005, "high": 0.02}, "gb": {"mid": 1.0}, "cf": {"mid": 1.0}, "lf": {"mid": 1.0}}

def f(x):
    try: v = float(x); return None if np.isnan(v) else v
    except Exception: return None
def load_csv(p, key="tag"):
    return {r[key]: r for r in csv.DictReader(open(p))} if os.path.exists(p) else {}
cam = load_csv(f"{SC}/cam_scores.csv"); gbl = load_csv(f"{SC}/gb_loc.csv"); outc = load_csv(f"{RES}/stock_outcomes.csv")

rows = []
for p in sorted(glob.glob(f"{RES}/live/stock-*.csv")):
    tag = os.path.basename(p)[:-4]
    m = re.match(r"stock-([a-z]+)-([^-]+)-(def|none|agg)-r(\d+)-(\d{4}_\d{4})$", tag)
    if not m: continue
    fault, sev = m.group(1), m.group(2)
    if fault not in SEV and fault != "nf": continue
    r = next(csv.DictReader(open(p)))
    if fault == "nf": x = 0.0
    elif sev in SEV[fault]: x = SEV[fault][sev]
    else:
        try: x = float(sev.split(":")[0].split("_")[0])
        except Exception: continue
    o = outc.get(tag, {}); c = cam.get(tag, {}); g = gbl.get(tag, {})
    rows.append(dict(tag=tag, fault=fault, x=x, S_perc=f(r.get("S_perc")), S_lidar=f(r.get("S_lidar_front")),
                     s_loc=f(r.get("s_loc_med")) if r.get("s_loc_med") not in (None, "") else f(g.get("s_loc_med")),
                     ATE=f(r.get("ate_rmse")), e_lat=f(r.get("e_lat_p95")), R_h=f(r.get("R_h")), R_far=f(r.get("R_far")),
                     cam=f(c.get("cam")), tl=f(c.get("tl")), missed_green=f(o.get("missed_green")), red=f(o.get("red_light_runs"))))
    if fault == "lf":   # 전방 LiDAR 단절: 검출 토픽이 비어 재현율이 정의되지 않음(nan) → 0 으로 간주
        for k in ("R_h", "R_far"):
            if rows[-1][k] is None: rows[-1][k] = 0.0
nf_rows = [r for r in rows if r["fault"] == "nf"]
def nfmed(k):
    v = [r[k] for r in nf_rows if r[k] is not None]; return (float(np.median(v)), len(v)) if v else (None, 0)

def series(fault, key, with_nf=True):
    g = collections.defaultdict(list)
    for r in rows:
        if (r["fault"] == fault or (with_nf and r["fault"] == "nf")) and r[key] is not None: g[r["x"]].append(r[key])
    return g
def draw(ax, fault, key, color, marker, ls, label, pos, stat=np.median):
    g = series(fault, key); xs = [x for x in sorted(g) if x in pos]
    for x in xs: ax.scatter([pos[x]] * len(g[x]), g[x], s=9, color=color, alpha=0.35, linewidths=0, zorder=2)
    med = [float(stat(g[x])) for x in xs]
    ax.plot([pos[x] for x in xs], med, marker=marker, ls=ls, color=color, lw=figstyle.LW_LINE, ms=5.5, mec="white", mew=0.8, label=label, zorder=3)
    print(f"  {fault:3s} {key:12s} " + "  ".join(f"{x:g}:{stat(g[x]):.2f}(n={len(g[x])})" for x in xs))
    return xs, [len(g[x]) for x in xs]

def panel(top, bot, fault, title, skey, slabel, thr, pkeys, plabels, pylabel, xunit, log_perf=False, nf_key=None, pstat=np.median):
    xs_all = sorted({r["x"] for r in rows if r["fault"] in (fault, "nf")})
    pos = {x: i for i, x in enumerate(xs_all)}
    xs, ns = draw(top, fault, skey, C_SCORE, "o", "-", slabel, pos)
    top.set_ylim(-0.03, 1.06)
    if thr is not None:
        top.axhline(thr, color=C_THR, ls=":", lw=1.1)
        top.text(0.985, thr + 0.025, f"판단 문턱 {thr}", color=C_THR, fontsize=7.5, ha="right", va="bottom", transform=top.get_yaxis_transform())
    m, n = nfmed(skey)
    if m is not None:
        top.axhline(m, color=REF, ls="--", lw=0.9)
        top.text(0.985, m + 0.012, f"무고장 중앙값 {m:.2f} (n={n})", color=REF, fontsize=7.5, ha="right", va="bottom", transform=top.get_yaxis_transform())
    top.set_title(title, loc="left", fontsize=10, pad=14); top.set_ylabel(slabel)
    for key, lab, col, mk, ls in zip(pkeys, plabels, (C1, C2), ("o", "s"), ("-", "--")):
        draw(bot, fault, key, col, mk, ls, lab, pos, stat=pstat)
    if log_perf:
        bot.set_yscale("log"); bot.set_ylim(0.02, 30)
        bot.yaxis.set_major_locator(FixedLocator([0.1, 1, 10])); bot.yaxis.set_major_formatter(FixedFormatter(["0.1", "1", "10"])); bot.yaxis.set_minor_locator(NullLocator())
    else: bot.set_ylim(-0.03, max(1.06, bot.get_ylim()[1]))
    v = [r[nf_key or pkeys[-1]] for r in nf_rows if r[nf_key or pkeys[-1]] is not None]
    m, n = (float(pstat(v)), len(v)) if v else (None, 0)
    if m is not None and (not log_perf or m > 0):
        bot.axhline(m, color=REF, ls="--", lw=0.9)
        bot.text(0.985, m * 1.12 if log_perf else m + 0.012, f"무고장 {m:.2f}", color=REF, fontsize=7.5, ha="right", va="bottom", transform=bot.get_yaxis_transform())
    bot.set_ylabel(pylabel); bot.legend(loc="upper left", handlelength=2.2, borderaxespad=0.6)
    labels = [("0\n(무고장)" if x == 0 else f"{x:g}") for x in xs_all]
    bot.set_xticks(range(len(xs_all))); bot.set_xticklabels(labels); bot.set_xlim(-0.4, len(xs_all) - 0.6)
    runs = ", ".join(f"{x:g}:{c}" for x, c in zip(xs, ns)); bot.set_xlabel(xunit + f"\n수준별 런 수 — {runs}", fontsize=8)
    for k, x in SEV[fault].items():
        if x in pos:
            for ax in (top, bot): ax.axvline(pos[x], color=REF, ls=(0, (1, 3)), lw=0.8, zorder=0)
            top.text(pos[x], 1.012, k, transform=top.get_xaxis_transform(), ha="center", va="bottom", fontsize=7.5, color=REF)
    for ax in (top, bot):
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)

os.makedirs(f"{RES}/figs", exist_ok=True)
# ── 그림 1: 센서 잡음·단절 (cn, cf, lf)
fig, axes = plt.subplots(2, 3, figsize=(12.6, 6.4), sharex="col", gridspec_kw=dict(hspace=0.10, wspace=0.30))
panel(axes[0, 0], axes[1, 0], "cn", "(d) 카메라 잡음 (cn)", "cam", "카메라 점수", 0.7, ["missed_green"], ["녹색 신호 미인식 (회/런, 평균)"], "신호등 인식 실패 (회/런, 평균)", "카메라 가우시안 잡음 σ → 나쁨", pstat=np.mean)
panel(axes[0, 1], axes[1, 1], "cf", "(e) 카메라 단절 (cf)", "S_perc", "인지 점수 (융합)", 0.7, ["missed_green"], ["녹색 신호 미인식 (회/런, 평균)"], "신호등 인식 실패 (회/런, 평균)", "카메라 영상 정지 (1 = 주입)", pstat=np.mean)
panel(axes[0, 2], axes[1, 2], "lf", "(f) 전방 LiDAR 단절 (lf)", "S_perc", "인지 점수 (융합)", 0.7, ["R_h", "R_far"], ["재현율 0–26 m", "재현율 26–50 m"], "Autoware 인식 재현율", "전방 LiDAR 데이터 정지 (1 = 주입)", nf_key="R_far")
axes[1, 2].text(0.5, 0.42, "단절 뒤 검출 토픽 비어 있음 → 재현율 0 으로 간주", transform=axes[1, 2].transAxes, ha="center", fontsize=7.5, color=REF)
axes[0, 1].text(0.5, 0.30, "영상 정지는 타임아웃·동결 검출기로 잡히며\n카메라 품질 점수가 아니라 융합 인지 점수에 반영", transform=axes[0, 1].transAxes, ha="center", fontsize=7.2, color=REF)
for ext in ("png", "pdf"):
    out = f"{RES}/figs/fig_noise_sweep_rest_sensor.{ext}"; plt.savefig(out); print(out)
# ── 그림 2: 항법 고장 (gn, gb, gm, imb, imd)
fig, axes = plt.subplots(2, 5, figsize=(15.5, 6.4), sharex="col", gridspec_kw=dict(hspace=0.10, wspace=0.34))
specs = [("gn", "(g) GNSS 잡음 (gn)", "GNSS 잡음 σ (m) → 나쁨"), ("gb", "(h) GNSS 편향 (gb)", "GNSS 고정 편향 (1 = 주입)"),
         ("gm", "(i) GNSS 상관편향 (gm)", "Gauss-Markov σ (m) → 나쁨"), ("imb", "(j) 자이로 바이어스 (imb)", "바이어스 (rad/s) → 나쁨"),
         ("imd", "(k) 자이로 드리프트 (imd)", "드리프트 (rad/s²) → 나쁨")]
for j, (fault, title, xunit) in enumerate(specs):
    panel(axes[0, j], axes[1, j], fault, title, "s_loc", "위치추정 점수", 0.5, ["ATE", "e_lat"], ["궤적 오차 ATE", "횡오차 P95"], "EKF 위치 오차 (m, 로그)", xunit, log_perf=True, nf_key="ATE")
axes[0, 1].text(0.5, 0.45, "순정 런 기록에서 주입 효과 미확인\n(GNSS 잔차 점수·ATE 모두 불변) → 별도 확인 필요", transform=axes[0, 1].transAxes, ha="center", fontsize=7.2, color=REF)
for ext in ("png", "pdf"):
    out = f"{RES}/figs/fig_noise_sweep_rest_nav.{ext}"; plt.savefig(out); print(out)
