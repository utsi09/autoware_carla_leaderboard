#!/usr/bin/env python3
"""노출 지표 그림: 고장 상태 주행거리 — 순정/우리/차선정차 3그룹."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
faults = ["camera\nblur","camera\nnoise","gyro\nnoise","lidar\nsparse","imu\nnoise"]
stock  = [238, 240, 251, 264, 71]
ours   = [33.5, 32.4, 57.6, 140.4, 12.4]
base   = [16.9, 17.6, 9.4, 133.4, 8.6]
x = range(len(faults)); w = 0.27
fig, ax = plt.subplots(figsize=(7.5,4))
ax.bar([i-w for i in x], stock, w, label="stock (no supervision)")
ax.bar(x, ours, w, label="ours (detect + evacuate)")
ax.bar([i+w for i in x], base, w, label="detect + in-lane stop")
ax.set_xticks(list(x)); ax.set_xticklabels(faults, fontsize=9)
ax.set_ylabel("distance driven in degraded state [m]")
ax.set_title("Degraded-state driving exposure by fault type")
ax.legend(fontsize=9); ax.grid(alpha=0.3, axis="y")
ax.annotate("lidar-sparse(mid): judged tolerable →\nintentional continue", xy=(3, 145), fontsize=7, ha="center")
plt.tight_layout()
out="/home/taewook/autoware_carla_leaderboard/experiments/results/fig_exposure.png"
plt.savefig(out, dpi=160); print(out)
