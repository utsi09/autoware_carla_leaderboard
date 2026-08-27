#!/usr/bin/env python3
"""Ablation results (n=20 pooled) + two-regime comparison — candidate 그림 5-x."""
import sys
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import ieee_style as st
matplotlib.rcParams['font.family'] = ['STIXGeneral']
import matplotlib.pyplot as plt

OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig10_ablation.png'
RED = st.RED
AVOID = '#d9dce2'

ARMS = ['A1\nnative', 'A2\ndetect\n+ stop', 'A3\nevacuation']
COLL = [14, 0, 10]
N = 20

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9), dpi=200,
                               gridspec_kw={'width_ratios': [1.35, 1]})
x = range(3)
avoid = [N - c for c in COLL]
ax1.bar(x, avoid, width=0.62, color=AVOID, edgecolor='black', lw=0.5)
ax1.bar(x, COLL, bottom=avoid, width=0.62, color=RED, edgecolor='black', lw=0.5)
for i, c in enumerate(COLL):
    ax1.text(i, N + 0.5, f'{c}/{N}', ha='center', fontsize=9)
ax1.text(0, avoid[0] + COLL[0] / 2, 'collided', ha='center', va='center',
         fontsize=7.5, color='white')
ax1.text(0, avoid[0] / 2, 'avoided', ha='center', va='center', fontsize=7.5,
         color='#3a3f4c')
ax1.set_xticks(x); ax1.set_xticklabels(ARMS, fontsize=8)
ax1.set_ylim(0, 23); ax1.set_yticks([0, 5, 10, 15, 20])
ax1.set_ylabel('seeds (paired, S02–S21)', fontsize=8.5)
ax1.set_title('(a) dart-out at $t_{detect}$ + 3 s  (n = 20)', fontsize=9)
ax1.grid(axis='y', alpha=0.25); ax1.set_axisbelow(True)
st.clean_axes(ax1)

rates = [10 / 20, 0 / 8]
ax2.bar([0, 1], rates, width=0.5, color=RED, edgecolor='black', lw=0.5)
ax2.text(0, rates[0] + 0.03, '10/20', ha='center', fontsize=9)
ax2.text(1, 0.03, '0/8', ha='center', fontsize=9)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(['transient\n($t_{detect}$ + 3 s)', 'settled cruise\n(low speed)'], fontsize=8)
ax2.set_ylim(0, 1.0)
ax2.set_ylabel('collision rate', fontsize=8.5)
ax2.set_title('(b) evacuation policy, two regimes', fontsize=9)
ax2.grid(axis='y', alpha=0.25); ax2.set_axisbelow(True)
st.clean_axes(ax2)

fig.tight_layout()
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.05)
print('saved')
