#!/usr/bin/env python3
"""Continuous health traces (EN) — band separation w.r.t. dual thresholds.
Reuses parse/clean pipeline from experiments/analysis/fig_health_traces.py."""
import sys
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import figstyle
from fig_health_traces import series_pts, CH_MAIN, CH_AUX
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

matplotlib.rcParams['font.family'] = ['STIXGeneral']
OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig12_health.png'

figstyle.apply()
matplotlib.rcParams['font.family'] = ['STIXGeneral']
series = [
    ('scoretrace_nf_mid.csv', 'fault-free (nf)', figstyle.C_NF),
    ('scoretrace_lso_mid.csv', 'lso-mid (tolerated)', figstyle.C_MID),
    ('scoretrace_lso_high.csv', 'lso-high (intervention)', figstyle.C_HIGH),
]
fig, ax = plt.subplots(figsize=(7.2, 3.3), dpi=200)
for fname, label, color in reversed(series):
    xa, ya = series_pts(fname, CH_AUX)
    ax.plot(xa, ya, color=color, lw=figstyle.LW_LINE * 0.7,
            ls=(0, (2.5, 2.5)), alpha=0.40, solid_joinstyle='round')
    xs, ys = series_pts(fname, CH_MAIN)
    ax.plot(xs, ys, color=color, lw=figstyle.LW_LINE, ls='-', label=label,
            solid_joinstyle='round')

for y, name in [(0.7, r'$\theta_H$ = 0.7'), (0.3, r'$\theta_L$ = 0.3')]:
    ax.axhline(y, color='#3a3f4c', lw=0.9, ls=(0, (5, 3)))
    ax.text(ax.get_xlim()[1], y + 0.015, name, ha='right', fontsize=8.5,
            color='#3a3f4c')

ax.set_xlabel('time since engagement [s]')
ax.set_ylabel('capability score')
ax.set_ylim(0.0, 1.06); ax.set_xlim(left=0)
leg1 = ax.legend(loc='lower right', frameon=False, fontsize=8.5)
ax.add_artist(leg1)
style_handles = [
    Line2D([], [], color='#4a5160', lw=figstyle.LW_LINE, ls='-',
           label='perception (state-transition input)'),
    Line2D([], [], color='#4a5160', lw=figstyle.LW_LINE * 0.7,
           ls=(0, (2.5, 2.5)), alpha=0.55, label='obstacle (move gate)'),
]
ax.legend(handles=style_handles, loc='lower left', frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.05)
print('saved')
