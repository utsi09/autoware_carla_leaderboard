#!/usr/bin/env python3
"""그림 2종: (a) 거리 사다리 곡선 (무고장/실명 순정), (b) 8m 경계 3팔 간격 비교."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# (a) 사다리: 스폰거리 vs 최소간격 (충돌=0 처리), 무고장 vs 실명
nf_d   = [14,14,11, 8, 8, 6, 6, 5, 5]
nf_g   = [4.4,4.3,4.25, 0,0, 0,0, 0,0]          # 충돌은 0
lso_d  = [11,11, 8, 8, 6, 5, 5]
lso_g  = [11.4,6.2,0.11,0.38,0.14,0.32,0.27]
fig, ax = plt.subplots(1, 2, figsize=(11,4.2))
ax[0].scatter(nf_d, nf_g, s=70, marker="o", label="fault-free stock (collision=0)", zorder=3)
ax[0].scatter(lso_d, lso_g, s=70, marker="s", label="lidar-blind stock (freeze)", zorder=3)
ax[0].axhline(0.30, ls="--", lw=1, c="crimson"); ax[0].text(13.9,0.4,"contact 0.30 m",c="crimson",fontsize=8)
ax[0].axvspan(8,11,alpha=0.08,color="gray")
ax[0].text(9.5,8.5,"stopping-distance\nboundary 8–11 m",ha="center",fontsize=8)
ax[0].set_xlabel("pedestrian spawn distance ahead [m]"); ax[0].set_ylabel("min surface gap [m]")
ax[0].set_title("(a) Dart-out distance ladder @4.2 m/s"); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
# (b) 8m 경계 3팔
arms = {"ours slow-MRM\n3.0 m/s (n=9)": [3.42,3.61,3.31,3.25,3.31,3.06,0.80,3.19,3.33],
        "stock w/ fault\n4.2 m/s (n=3, reverified)": [0,0,0],
        "fault-free stock\n4.2 m/s (n=4)": [0,0,0,0]}
for i,(k,v) in enumerate(arms.items()):
    ax[1].scatter([i]*len(v), v, s=60, alpha=0.75, zorder=3)
    ax[1].hlines(sorted(v)[len(v)//2], i-0.18, i+0.18, lw=2.5, zorder=4)
ax[1].axhline(0.30, ls="--", lw=1, c="crimson")
ax[1].set_xticks(range(3)); ax[1].set_xticklabels(arms.keys(), fontsize=8)
ax[1].set_ylabel("min surface gap [m] (0 = collision)")
ax[1].set_title("(b) Same 8 m dart-out, three arms"); ax[1].grid(alpha=0.3, axis="y")
plt.tight_layout()
out="/home/taewook/autoware_carla_leaderboard/experiments/results/fig_ladder_boundary.png"
plt.savefig(out, dpi=160); print(out)
