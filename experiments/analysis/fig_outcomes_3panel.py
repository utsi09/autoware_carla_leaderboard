#!/usr/bin/env python3
"""캠페인 결말 그림 (a) 검출률, (b) 제안 대응 결말, (c) 완전 순정 Autoware 결말 — 범례 한 박스.
(a)(b) = 논문 Figure/Table 5.1·5.2 값(8월, 조건당 45; 항법 확장은 유형별 행), 미항목화 건은 로그 확인대로 정지에 합산.
(c) = 11월 순정 매트릭스 stock_outcomes.csv, (b)와 같은 표본 설계(교통 3 × rep 0–14). 러너 코드 ↔ 논문 명칭: gm→GNSS correlated bias, gb→GNSS outage.
출력: results/figs/fig_outcomes_3panel.png / .pdf
"""
import csv, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"
plt.rcParams.update({"font.family": "STIXGeneral", "font.size": 11, "mathtext.fontset": "stix"})
# (라벨, 검출률 %, (continue, move, stop), 순정 (fault, sev) 목록)
ROWS = [("Fault-free control",            0,   (45, 0, 0),   [("nf", "mid")]),
        ("LiDAR sparsification (mid)",    2,   (44, 0, 1),   [("lso", "mid")]),
        ("LiDAR sparsification (high)",  98,   (0, 44, 1),   [("lso", "high")]),   # 사용자 확정(11/09 16:45): 논문 그림 값 그대로 (0813 감독기 로그 집계 DEFER 40/PARKED 2 와 다르나 사용자 결정)
        ("LiDAR clutter (mid/high)",    100,   (0, 0, 90),   [("lcl", "mid"), ("lcl", "high")]),
        ("LiDAR death",                 100,   (0, 1, 44),   [("lf", "mid")]),
        ("Camera death",                100,   (0, 16, 29),  [("cf", "mid")]),
        ("Camera noise (mid/high)",      99,   (0, 25, 65),  [("cn", "mid"), ("cn", "high")]),
        ("GNSS position noise (mid)",   100,   (0, 40, 5),   [("gn", "mid")]),
        ("GNSS position noise (high)",  100,   (0, 2, 43),   [("gn", "high")]),
        ("IMU gyro noise (mid/high)",    99,   (0, 0, 90),   [("imn", "mid"), ("imn", "high")]),
        ("GNSS correlated bias (mid/high)", 100, (0, 0, 90), [("gm", "mid"), ("gm", "high")]),
        ("GNSS outage",                 100,   (0, 0, 45),   [("gb", "mid")]),
        ("IMU gyro bias (mid/high)",    100,   (0, 0, 90),   [("imb", "mid"), ("imb", "high")]),   # 0821 캠페인 CARLA_DIED 2셀은 같은 날 재실행 유효(results_0821_2337)
        ("IMU bias ramp (mid/high)",    100,   (0, 0, 90),   [("imd", "mid"), ("imd", "high")])]   # 3셀 재실행 유효(results_0821_2351)
SEPS = {1, 5, 7, 10}   # 그룹 구분선: 행 인덱스 앞
MAP = {"drove_on": "cont", "queued": "stall", "red_wait": "stall", "crawl": "stall", "frozen_light": "stall", "frozen": "stall", "stock_mrm": "stop", "collision": "coll"}
uniq = {}
for r in sorted(csv.DictReader(open(f"{RES}/stock_outcomes.csv")), key=lambda r: r["tag"]):
    if r["judge"] in ("", "CARLA_DIED", "SETUP_FAIL", "DISK_FULL"): continue
    try: rep = int(r["rep"])
    except ValueError: continue
    if rep > 14 or r["sev"] not in ("mid", "high"): continue
    uniq[(r["fault"], r["sev"], r["npc"], rep)] = MAP.get(r["cls"], "stall")
stock = collections.defaultdict(collections.Counter)
for (f, s, _, _), k in uniq.items(): stock[(f, s)][k] += 1

C = {"cont": ("white", ""), "move": ("#c8c8c8", ""), "stop": ("#4d4d4d", ""), "stall": ("#4d4d4d", "//"), "coll": ("black", "xx")}
LEG = [("cont", "Continue driving"), ("move", "Evacuation (MRM_MOVE)"), ("stop", "Stop (MRM_DEFER / Autoware MRM)"),
       ("stall", "Stalled or frozen in lane, no MRM (stock only)"), ("coll", "Collision (stock only)")]
def seg(ax, y, parts, n):
    left = 0.0
    for k, v in parts:
        if v <= 0: continue
        w = v / n * 100; col, hat = C[k]
        ax.barh(y, w, left=left, height=0.62, color=col, hatch=hat, edgecolor="black", linewidth=0.8)
        if w >= 7: ax.text(left + w / 2, y, str(v), ha="center", va="center", fontsize=10, color="white" if col in ("#4d4d4d", "black") else "black")
        left += w
    ax.text(103, y, f"$n$ = {n}", va="center", fontsize=10)

fig, axes = plt.subplots(1, 3, figsize=(16.5, 7.8), gridspec_kw=dict(width_ratios=[1.0, 2.4, 2.4], wspace=0.08))
a, b, c = axes
ys = list(range(len(ROWS)))[::-1]
for y, (lab, det, (co, mv, st), skeys) in zip(ys, ROWS):
    a.barh(y, det, height=0.62, color="#6f6f6f", edgecolor="black", linewidth=0.8); a.text(det + 2, y, str(det), va="center", fontsize=10)
    seg(b, y, [("cont", co), ("move", mv), ("stop", st)], co + mv + st)
    cnt = collections.Counter()
    for fs in skeys: cnt += stock.get(fs, collections.Counter())
    n2 = sum(cnt.values())
    if n2: seg(c, y, [(k, cnt.get(k, 0)) for k in ("cont", "stop", "stall", "coll")], n2)
    else: c.text(50, y, "not run", ha="center", va="center", fontsize=9, color="gray")
a.set_yticks(ys); a.set_yticklabels([r[0] for r in ROWS], fontsize=11)
for ax in (b, c): ax.set_yticks(ys); ax.set_yticklabels([])
for ax in axes:
    for i in SEPS: ax.axhline(len(ROWS) - i - 0.5, color="gray", ls="--", lw=0.7)
    ax.set_ylim(-0.55, len(ROWS) - 0.45); ax.tick_params(axis="x", labelsize=10)
a.set_xlim(0, 125); a.set_xticks([0, 50, 100]); a.set_xlabel("Detection rate (%)", fontsize=12)
for ax in (b, c): ax.set_xlim(0, 118); ax.set_xticks([0, 20, 40, 60, 80, 100]); ax.set_xlabel("Share of valid cases (%)", fontsize=12)
for ax, t in zip(axes, ("(a)", "(b)  Proposed", "(c)  Stock Autoware")):
    ax.text(0.5, -0.115, t, transform=ax.transAxes, ha="center", fontsize=11)
fig.legend(handles=[Patch(facecolor=C[k][0], hatch=C[k][1], edgecolor="black", label=l) for k, l in LEG], loc="upper center", bbox_to_anchor=(0.56, 0.995),
           ncol=5, frameon=True, fontsize=10, handlelength=1.8, columnspacing=1.3, handletextpad=0.6)
fig.subplots_adjust(left=0.16, right=0.99, top=0.93, bottom=0.11)
for ext in ("png", "pdf"):
    out = f"{RES}/figs/fig_outcomes_3panel.{ext}"; fig.savefig(out, dpi=200, facecolor="white"); print(out)
