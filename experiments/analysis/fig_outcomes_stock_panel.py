#!/usr/bin/env python3
"""캠페인 결말 그림 (a)(b) 오른쪽에 붙일 (c) '완전 순정 Autoware(감시기·감독기 없음)' 결말 분포 패널.
입력: stock_outcomes.csv(stock_freeze.py; 11월 순정 매트릭스, 조건당 45런) → 출력: results/figs/fig_outcomes_stock_panel.png
       + 논문 그림 PNG 와 가로로 이어 붙인 results/figs/fig_outcomes_with_stock.png
"""
import csv, sys, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from PIL import Image
RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"
SRC = sys.argv[1] if len(sys.argv) > 1 else f"{RES}/stock_outcomes.csv"
THESIS_PNG = sys.argv[2] if len(sys.argv) > 2 else None
ROWS = [("nf", ("mid", "nf"), "nf  fault-free control"), ("lso", ("mid",), "lso-mid  LiDAR sparsification"), ("lso", ("high",), "lso-high  LiDAR sparsification"),
        ("lcl", ("mid",), "lcl-mid  LiDAR clutter"), ("lcl", ("high",), "lcl-high  LiDAR clutter"), ("lf", ("mid",), "lf  LiDAR death"),
        ("cf", ("mid",), "cf  camera death"), ("cn", ("mid", "high"), "cn  camera noise (mid/high)"),
        ("gn", ("mid",), "gn-mid  GNSS position noise"), ("gn", ("high",), "gn-high  GNSS position noise"),
        ("imn", ("mid", "high"), "imn  IMU gyro noise (mid/high)"), ("NAV", None, "Navigation ext.‡ (gb, gm, imb, imd)")]
SEPS = {1, 6, 8, 10, 11}
CATS = [("drove_on", "Reached goal unaware (no reaction)", "white", ""),
        ("stall", "Stalled / frozen in lane, no MRM", "#4d4d4d", ""),
        ("stock_mrm", "Stock Autoware MRM stop", "#a6a6a6", "\\\\"),
        ("collision", "Collision", "black", "xx"),
        ("other", "Other", "white", "//")]
MAP = {"drove_on": "drove_on", "queued": "stall", "red_wait": "stall", "crawl": "stall", "frozen_light": "stall", "frozen": "stall",
       "stock_mrm": "stock_mrm", "collision": "collision"}
rows_all = [r for r in csv.DictReader(open(SRC)) if r["judge"] not in ("", "CARLA_DIED", "SETUP_FAIL", "DISK_FULL")]
# 표본 맞추기: 논문 (b) 설계(교통 3종 × rep 0–14 = 조건당 45)와 같게 — 같은 셀 재실행은 최신 1건만, rep ≤ 14 만
uniq = {}
for r in sorted(rows_all, key=lambda r: r["tag"]):
    try: rep_i = int(r["rep"])
    except ValueError: continue
    if rep_i > 14 or r["sev"] not in ("mid", "high"): continue
    uniq[(r["fault"], r["sev"], r["npc"], rep_i)] = r
rows = list(uniq.values())
cnt = collections.defaultdict(collections.Counter)
for r in rows:
    k = MAP.get(r["cls"], "other")
    if r["fault"] in ("gb", "gm", "imb", "imd"): cnt["NAV"][k] += 1
    else: cnt[(r["fault"], r["sev"])][k] += 1
plt.rcParams.update({"font.family": "STIXGeneral", "font.size": 12, "mathtext.fontset": "stix"})
# (b) 패널 픽셀 기하(논문 PNG 1334x699 실측): 축 상단 66, 하단 576.5, 행 간격 42.5 px, 막대 높이 27 px → ylim(-0.52, 11.51), height 0.635
H_PX = 699; fig = plt.figure(figsize=(6.3, H_PX / 100), dpi=100)
ax = fig.add_axes([0.02, 1 - 576.5 / H_PX, 0.88, (576.5 - 66) / H_PX])
ys = list(range(len(ROWS)))[::-1]
for y, (f, sevs, lab) in zip(ys, ROWS):
    c = collections.Counter()
    if f == "NAV": c = cnt["NAV"]
    else:
        for s_ in sevs: c += cnt.get((f, s_), collections.Counter())
    n = sum(c.values())
    if n == 0: continue
    left = 0.0
    for key, _, col, hat in CATS:
        v = c.get(key, 0)
        if v <= 0: continue
        w = v / n * 100
        ax.barh(y, w, left=left, height=0.635, color=col, hatch=hat, edgecolor="black", linewidth=0.8)
        if w >= 7: ax.text(left + w / 2, y, str(v), ha="center", va="center", fontsize=11, color="white" if col in ("#4d4d4d", "black") else "black")
        left += w
    ax.text(103, y, f"$n$ = {n}", va="center", fontsize=11)
for yb in (10.5, 5.5, 3.5, 1.5, 0.5): ax.axhline(yb, color="gray", ls="--", lw=0.7)
ax.set_yticks([]); ax.set_ylim(-0.52, 11.51)
ax.set_xlim(0, 118); ax.set_xticks([0, 20, 40, 60, 80, 100]); ax.tick_params(axis="x", labelsize=11); ax.set_xlabel("Share of valid cases (%)", fontsize=12)
fig.legend(handles=[Patch(facecolor=col, hatch=hat, edgecolor="black", label=lab) for _, lab, col, hat in CATS],
           loc="center", bbox_to_anchor=(0.46, 1 - 28 / H_PX), ncol=3, frameon=True, fontsize=9.2, handlelength=1.6, columnspacing=1.0, handletextpad=0.5, borderpad=0.4)
fig.text(0.46, 1 - 683 / H_PX, "(c)", ha="center", fontsize=12)
fig.text(0.46, 1 - 648 / H_PX, "Stock Autoware (no monitor, no MRM supervisor); ‡ gm in place of gf", ha="center", fontsize=9, color="gray")
out = f"{RES}/figs/fig_outcomes_stock_panel.png"; fig.savefig(out, dpi=100, facecolor="white"); print(out)
if THESIS_PNG:
    a = Image.open(THESIS_PNG).convert("RGB"); b = Image.open(out).convert("RGB")
    if b.height != a.height: b = b.resize((int(b.width * a.height / b.height), a.height), Image.LANCZOS)
    canvas = Image.new("RGB", (a.width + b.width, a.height), "white"); canvas.paste(a, (0, 0)); canvas.paste(b, (a.width, 0))
    out2 = f"{RES}/figs/fig_outcomes_with_stock.png"; canvas.save(out2); print(out2, canvas.size)
