#!/usr/bin/env python3
"""Encounter injection protocol — timeline + standardized geometry (candidate 그림 4-x)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle, Circle

plt.rcParams.update({'font.family': 'serif',
                     'font.serif': ['STIXGeneral', 'DejaVu Serif'],
                     'mathtext.fontset': 'stix'})
INK = '#1f2430'; RED = '#a50f15'; GRAY = '#9aa3b2'
OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig11_encounter.png'

fig = plt.figure(figsize=(7.2, 3.5), dpi=200)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 48); ax.axis('off')

# ---------------- timeline (top) ----------------
TY = 40
ax.add_patch(FancyArrowPatch((6, TY), (96, TY), arrowstyle='-|>',
                             mutation_scale=16, color=INK, lw=1.6))
events = [(14, 'fault injection', 'seed-fixed waveform'),
          (46, 'detection  $t_{detect}$', 'shadow detector — common to all arms'),
          (78, 'launch  $t_{detect}$ + 3 s', 'behavior-independent trigger')]
for ex, top, sub in events:
    ax.plot([ex], [TY], marker='o', ms=6, mfc='white', mec=INK, mew=1.4, zorder=5)
    ax.text(ex, TY + 3.2, top, ha='center', fontsize=9.5, color=INK)
    ax.text(ex, TY - 3.6, sub, ha='center', fontsize=7.5, color='#5a6170')
ax.plot([78], [TY], marker='o', ms=6, mfc=RED, mec=INK, mew=1.2, zorder=6)

# launch → spawn connector
ax.plot([78, 78], [TY - 6, 26.5], color=RED, lw=1.1, ls=(0, (3, 2.5)))

# ---------------- plan-view geometry (bottom) ----------------
ax.add_patch(Rectangle((6, 10), 90, 12, fc='#eceef2', ec=INK, lw=1.0))
ax.plot([6, 96], [22, 22], color=INK, lw=1.0)
ax.plot([6, 96], [10, 10], color=INK, lw=1.0)
for xx in range(10, 96, 8):
    ax.plot([xx, xx + 4], [16, 16], color='white', lw=1.6)
ax.text(8, 23.4, 'driving lane', fontsize=8, color='#5a6170')

# ego
ax.add_patch(FancyBboxPatch((22, 12.6), 12, 6.8, boxstyle='round,pad=0.15,rounding_size=1.4',
                            fc='#c8d3e8', ec=INK, lw=1.2))
ax.text(28, 16, 'ego', ha='center', va='center', fontsize=9, color=INK)
ax.add_patch(FancyArrowPatch((34.6, 16), (42, 16), arrowstyle='-|>',
                             mutation_scale=13, color=INK, lw=1.4))
ax.text(38.3, 18.0, '$v(t)$', ha='center', fontsize=8.5)

# pedestrian at right lane edge, 8 m ahead
ax.plot([78], [11.6], marker='o', ms=7, mfc=RED, mec='black', mew=0.8, zorder=5)
ax.add_patch(FancyArrowPatch((78, 12.8), (78, 21.2), arrowstyle='-|>',
                             mutation_scale=12, color=RED, lw=1.3))
ax.text(80, 24.5, 'crosses 12 m, then stops', fontsize=8, color=RED, ha='left')
ax.text(80.5, 7.2, 'pedestrian — right lane edge + 0.5 m  (lateral jitter ± 0.2 m)',
        fontsize=8, ha='center', color=INK)

# 8 m dimension
ax.add_patch(FancyArrowPatch((34.6, 6.2), (78, 6.2), arrowstyle='<|-|>',
                             mutation_scale=11, color=INK, lw=1.0))
ax.plot([34.6, 34.6], [7.6, 10], color=INK, lw=0.8, ls=(0, (2, 2)))
ax.plot([78, 78], [7.6, 10], color=INK, lw=0.8, ls=(0, (2, 2)))
ax.text(56, 3.2, '8 m — standardized relative geometry (same for all arms)',
        ha='center', fontsize=8.5, color=INK)

fig.savefig(OUT, bbox_inches='tight', pad_inches=0.08, facecolor='white')
print('saved')
