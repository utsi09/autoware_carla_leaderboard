#!/usr/bin/env python3
"""Continuous health traces, three sensor families (EN) — 1x3 panels.
(a) LiDAR soiling (lso): decision channel = capability/perception
(b) camera pixel noise (cn): decision channel = capability/perception
(c) gyro white noise (imn): decision channel = capability/localization
gn is excluded by design (residual detector inside the supervisor, not /monitor/scores).
Reuses parse/clean pipeline from experiments/analysis/fig_health_traces.py."""
import sys
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import figstyle
from fig_health_traces import series_pts as _series_pts
EXTRA_CUT = 18.0
def series_pts(f, ch):
    xs, ys = _series_pts(f, ch)
    pts = [(x - EXTRA_CUT, y) for x, y in zip(xs, ys) if x >= EXTRA_CUT]
    return [p[0] for p in pts], [p[1] for p in pts]
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

matplotlib.rcParams['font.family'] = ['STIXGeneral']
OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig12_health.png'

figstyle.apply()
matplotlib.rcParams['font.family'] = ['STIXGeneral']

PANELS = [
    ('(a) LiDAR soiling (lso)', 'capability/perception',
     [('scoretrace_nf_mid.csv', 'fault-free', figstyle.C_NF),
      ('scoretrace_lso_mid.csv', 'mid (tolerated)', figstyle.C_MID),
      ('scoretrace_lso_high.csv', 'high (intervention)', figstyle.C_HIGH)]),
    ('(b) camera pixel noise (cn)', 'capability/perception',
     [('scoretrace_nf_mid.csv', 'fault-free', figstyle.C_NF),
      ('scoretrace_cn_mid.csv', 'mid (intervention)', figstyle.C_MID),
      ('scoretrace_cn_high.csv', 'high (intervention)', figstyle.C_HIGH)]),
]

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), dpi=200, sharey=True)
for ax, (title, channel, series) in zip(axes, PANELS):
    for fname, label, color in reversed(series):
        xs, ys = series_pts(fname, channel)
        ax.plot(xs, ys, color=color, lw=1.3, ls='-', label=label,
                solid_joinstyle='round')
    for y in (0.7, 0.3):
        ax.axhline(y, color='#3a3f4c', lw=0.8, ls=(0, (5, 3)))
    ax.set_ylim(0.0, 1.06)
    ax.set_xlim(left=3)
    ax.set_title(title, fontsize=8)
    ax.set_xlabel('time since engagement [s]', fontsize=7.5)
    ax.tick_params(labelsize=7)
axes[0].set_ylabel('perception capability score', fontsize=8.5)
axes[0].text(2, 0.72, r'$\theta_H$', fontsize=8, color='#3a3f4c', va='bottom')
axes[0].text(2, 0.32, r'$\theta_L$', fontsize=8, color='#3a3f4c', va='bottom')
axes[0].legend(loc='lower right', frameon=False, fontsize=7)
axes[1].legend(loc='lower right', frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.05)
print('saved')
