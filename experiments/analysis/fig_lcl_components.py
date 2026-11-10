#!/usr/bin/env python3
"""lcl 점수가 비 세기를 구분 못 하는 이유: (a) 점수 바닥 0.2 제거 전후 (b) 주입 모델의 지터 포화 (c) 원거리 잔존율 vs 실제 원거리 recall.
입력: results/lcl_components.csv (lcl_components.py).  (c) 의 recall 은 [live] 순정 def 중앙값 (nf 0.89, 5 mm/h 0.41, 25 mm/h 0.05).
nf 원거리 비율 1.056 은 고장 케이스의 CUSUM 발화 위치(프레임 363)와 같은 구간에서 잰 값. 출력: results/figs/fig_lcl_components.png"""
import csv, math, statistics as st
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = ["NanumGothic", "DejaVu Sans"]; matplotlib.rcParams["axes.unicode_minus"] = False
R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e"
rows = list(csv.DictReader(open(f"{R}/lcl_components.csv")))
SEV = ["nf", "mid", "high"]; X = [0, 1, 2]; LAB = ["비 없음", "5 mm/h", "25 mm/h"]
def stat(k, s):
    a = sorted(float(r[k]) for r in rows if r["sev"] == s)
    return st.median(a), a[len(a)//4], a[3*len(a)//4], len(a)
NF_FAR = 1.056
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.9))
def series(a, k, c, m, label, ls="-"):
    d = [stat(k, s) for s in SEV]; y = [x[0] for x in d]
    a.fill_between(X, [x[1] for x in d], [x[2] for x in d], color=c, alpha=.15, lw=0)
    a.plot(X, y, ls, color=c, marker=m, ms=8, lw=2, label=label); return y
series(ax[0], "q", BLUE, "o", "기록된 점수")
series(ax[0], "uncapped", ORANGE, "s", "0.2 바닥을 뺀 점수", "--")
ax[0].axhline(.7, color=MUTED, ls=":", lw=1); ax[0].text(2.05, .715, "감지 임계 0.7", ha="right", fontsize=8.5, color=MUTED)
ax[0].set_xticks(X, LAB); ax[0].set_ylim(0, 1.05); ax[0].set_ylabel("전방 LiDAR 점수")
ax[0].set_title("(a) 바닥을 빼도 세기가 구분되지 않음", loc="left", fontsize=11)
r = np.array([0.1, .25, .5, 1, 2, 3, 5, 10, 15, 25, 40]); 
ax[1].plot(r, (1-np.exp(-r))**2, color=BLUE, lw=2, marker="o", ms=5, label="거리 지터 계수")
ax[1].plot(r, np.exp(-2*0.01*r**0.6*35), color=ORANGE, lw=2, ls="--", marker="s", ms=5, label="35 m 왕복 투과율")
ax[1].set_xscale("log"); ax[1].set_xticks([.1, 1, 5, 25]); ax[1].set_xticklabels(["0.1", "1", "5", "25"]); ax[1].set_ylim(0, 1.3); ax[1].set_yticks([0, .2, .4, .6, .8, 1])
ax[1].set_xlabel("강우량 R (mm/h, 로그축)"); ax[1].set_ylabel("계수 (0~1)")
ax[1].set_title("(b) 주입 모델의 지터는 5 mm/h에서 포화", loc="left", fontsize=11)
far = [stat("far_ratio", s) for s in SEV]; yf = [NF_FAR/NF_FAR, far[1][0]/NF_FAR, far[2][0]/NF_FAR]
rec = [.89, .41, .05]
ax[2].plot(X, yf, color=BLUE, marker="o", ms=8, lw=2, label="LiDAR 원거리(>35 m) 점 잔존율")
ax[2].plot(X, [v/rec[0] for v in rec], color=ORANGE, ls="--", marker="s", ms=8, lw=2, label="실제 원거리 recall (26–50 m)")
ax[2].set_xticks(X, LAB); ax[2].set_ylim(0, 1.05); ax[2].set_ylabel("비 없음 대비 비율")
ax[2].set_title("(c) 세기를 따라가는 성분은 원거리 잔존율", loc="left", fontsize=11)
for a in ax:
    a.grid(axis="y", alpha=.25); a.spines[["top", "right"]].set_visible(False); a.legend(frameon=False, fontsize=8.5, loc={0:"center right",1:"upper left",2:"upper right"}[list(ax).index(a)])
fig.text(.01, .005, f"n = 비 없음 {stat('q','nf')[3]}, 5 mm/h {stat('q','mid')[3]}, 25 mm/h {stat('q','high')[3]} (8월 캠페인 제안·baseline 로그). 선 = 중앙값, 음영 = 사분위 범위. (b)는 주입 식 계산값.", fontsize=8.5, color=MUTED)
fig.tight_layout(rect=(0, .05, 1, 1))
out = f"{R}/figs/fig_lcl_components.png"; fig.savefig(out, dpi=180); print(out)
