#!/usr/bin/env python3
"""순정(stock) 결말 분포를 캠페인 그림 (b)(c) 와 같은 양식으로 그린다.
   --project : 지금까지 비율을 조건당 n=45 로 외삽한 '예상' 패널 (유효 케이스 기준, CARLA_DIED 제외)
   입력: results/stock_outcomes.csv (stock_freeze.py)  출력: results/figs/fig_stock_outcome[_projected].png
"""
import csv, sys, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"
ROWS = [("nf", "mid", "nf  fault-free control"), ("lso", "mid", "lso-mid  LiDAR sparsification"), ("lso", "high", "lso-high  LiDAR sparsification"),
        ("lcl", "mid", "lcl-mid  LiDAR clutter"), ("lcl", "high", "lcl-high  LiDAR clutter"), ("lf", "mid", "lf  LiDAR death"),
        ("cf", "mid", "cf  camera death"), ("cn", "mid", "cn-mid  camera noise"), ("cn", "high", "cn-high  camera noise"),
        ("gn", "mid", "gn-mid  GNSS position noise"), ("gn", "high", "gn-high  GNSS position noise"),
        ("imn", "mid", "imn-mid  IMU gyro noise"), ("imn", "high", "imn-high  IMU gyro noise")]
SEPS = {1, 6, 9, 11}   # 그룹 구분 점선 위치 (행 인덱스 앞)
# 분류 → (범례, 면색, 해치)
CATS = [("drove_on", "Drove on unaware (route completed)", "white", ""),
        ("queued", "Held behind traffic", "#d9d9d9", ""),
        ("red_wait", "Red-light wait at case end", "#d9d9d9", "..."),
        ("crawl", "Crawl (<1 m/s mean) then stop", "#bdbdbd", "//"),
        ("frozen_light", "Frozen at signal (missed green)", "#4d4d4d", ""),
        ("frozen", "Frozen in lane (no signal, no lead)", "#4d4d4d", "\\\\"),
        ("stock_mrm", "Stock MRM stop (20-30 s late)", "#8c8c8c", "\\\\"),
        ("collision", "Collision", "black", "xx"),
        ("other", "Other", "white", "xx")]
N_TARGET = 45

def main():
    project = "--project" in sys.argv
    npc = [a.split("=")[1] for a in sys.argv if a.startswith("--npc=")]
    rows = [r for r in csv.DictReader(open(f"{RES}/stock_outcomes.csv")) if r["judge"] not in ("CARLA_DIED", "SETUP_FAIL", "DISK_FULL")]
    if npc: rows = [r for r in rows if r["npc"] == npc[0]]
    rows = [r for r in rows if r["judge"] != ""]        # 진행 중(judge 없음) 제외
    cnt = collections.defaultdict(collections.Counter)
    for r in rows: cnt[(r["fault"], r["sev"])][r["cls"]] += 1
    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    plt.rcParams.update({"font.family": "serif", "font.size": 10})
    ys = list(range(len(ROWS)))[::-1]
    for y, (f, s, lab) in zip(ys, ROWS):
        c = cnt.get((f, s), collections.Counter()); n = sum(c.values())
        if n == 0: continue
        if project:   # 비율 × 45, 반올림 뒤 합이 45 가 되게 가장 큰 항목으로 보정
            vals = {k: round(v / n * N_TARGET) for k, v in c.items()}
            diff = N_TARGET - sum(vals.values()); kmax = max(vals, key=vals.get); vals[kmax] += diff; n_show = N_TARGET
        else:
            vals = dict(c); n_show = n
        left = 0.0
        for key, _, col, hat in CATS:
            v = vals.get(key, 0)
            if v <= 0: continue
            w = v / n_show * 100
            ax.barh(y, w, left=left, height=0.62, color=col, hatch=hat, edgecolor="black", linewidth=0.8)
            if w >= 7:
                ax.text(left + w / 2, y, str(v), ha="center", va="center", fontsize=9, color="white" if col in ("#4d4d4d", "black") else "black")
            left += w
        ax.text(103, y, str(n_show) + ("" if project else f"  (n={n})"), va="center", fontsize=9)
    for i in SEPS:
        ax.axhline(len(ROWS) - i - 0.5, color="gray", ls="--", lw=0.7)
    ax.set_yticks(ys); ax.set_yticklabels([r[2] for r in ROWS], fontsize=9)
    ax.set_xlim(0, 100); ax.set_xticks([0, 50, 100]); ax.set_xlabel("Share of valid cases (%)")
    ax.text(103, len(ROWS) - 0.3, "n", fontsize=9, style="italic")
    ax.set_ylim(-0.6, len(ROWS) - 0.4)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    title = "(d) Stock Autoware (no monitor, no responder)" + (", projected to n=45 from %d cases" % len(rows) if project else " (%d cases so far)" % len(rows))
    ax.set_title(title, fontsize=9, loc="left", pad=14)
    used = {k for c in cnt.values() for k in c}
    ax.legend(handles=[Patch(facecolor=col, hatch=hat, edgecolor="black", label=lab) for k, lab, col, hat in CATS if k in used],
              loc="upper center", bbox_to_anchor=(0.35, -0.12), ncol=2, fontsize=8, frameon=True)
    out = f"{RES}/figs/fig_stock_outcome{'_projected' if project else ''}{'_' + npc[0] if npc else ''}.png"
    plt.tight_layout(); plt.savefig(out, dpi=200, bbox_inches="tight"); print(out)

if __name__ == "__main__":
    main()
