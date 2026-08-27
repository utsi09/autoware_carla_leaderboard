#!/usr/bin/env python3
"""Speed-dose causal experiment (0827, 120 runs) — candidate 그림 5-x.

(a) collision rate vs spawn distance per cap (Wilson 95% CI) — boundary shift.
(b) primary endpoint: paired 8 m contrast 4.2 vs 3.0 (10 seeds), McNemar p.
Data: speed_dose_progress.csv + collision_live.log (ego RAW-HIT), see
experiments/analysis/speed_dose_report.py."""
import sys
import math
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import ieee_style as st
matplotlib.rcParams['font.family'] = ['STIXGeneral']
import matplotlib.pyplot as plt

OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig13_speeddose.png'

DIST = [6, 7, 8, 9]
# 충돌수/10 (speed_dose_report.py 0827 10:50 집계)
COLL = {'4.2': [10, 10, 10, 10], '3.6': [10, 10, 10, 2], '3.0': [8, 5, 0, 0]}
COLOR = {'4.2': st.RED, '3.6': '#8a6d2c', '3.0': st.BLUE}
MARK = {'4.2': 'o', '3.6': 's', '3.0': '^'}
OFF = {'4.2': -0.07, '3.6': 0.0, '3.0': 0.07}


def wilson(k, n=10):
    z, p = 1.959964, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9), dpi=200,
                               gridspec_kw={'width_ratios': [1.5, 1]})

for cap in ['4.2', '3.6', '3.0']:
    xs = [d + OFF[cap] for d in DIST]
    ys = [k / 10 for k in COLL[cap]]
    los = [y - wilson(k)[0] for k, y in zip(COLL[cap], ys)]
    his = [wilson(k)[1] - y for k, y in zip(COLL[cap], ys)]
    ax1.errorbar(xs, ys, yerr=[los, his], color=COLOR[cap], marker=MARK[cap],
                 ms=4.5, lw=1.2, capsize=2.5, elinewidth=0.8,
                 label=f'cap {cap} m/s')
# 겹침 방지: 10/10 라벨은 상단에 1회(4.2·3.6 공통), 나머지는 점 옆
ax1.text(6.05, 1.045, '10/10', fontsize=7, color='#3a3f4c')
ax1.text(8.72, 1.045, '10/10 (4.2)', fontsize=7, color=st.RED)
ax1.text(9.13, 0.20, '2/10', fontsize=7, color='#8a6d2c', va='center')
ax1.text(6.17, 0.80, '8/10', fontsize=7, color=st.BLUE, va='center')
ax1.text(7.17, 0.50, '5/10', fontsize=7, color=st.BLUE, va='center')
ax1.text(8.16, 0.05, '0/10', fontsize=7, color=st.BLUE)
ax1.set_xticks(DIST)
ax1.set_xticklabels([f'{d}' for d in DIST])
ax1.set_xlabel('pedestrian spawn distance [m]', fontsize=8.5)
ax1.set_ylabel('collision rate (n = 10 seeds)', fontsize=8.5)
ax1.set_ylim(-0.04, 1.13)
ax1.set_xlim(5.6, 9.6)
ax1.grid(axis='y', alpha=0.25)
ax1.set_axisbelow(True)
ax1.legend(loc='center left', bbox_to_anchor=(0.02, 0.42), fontsize=7.5)
ax1.set_title('(a) settled-encounter boundary shift by speed cap', fontsize=9)
st.clean_axes(ax1)

# (b) 1차 종결점 8 m paired
AVOID = '#d9dce2'
N = 10
coll = {'4.2': 10, '3.0': 0}
for i, cap in enumerate(['4.2', '3.0']):
    a = N - coll[cap]
    ax2.bar(i, a, width=0.52, color=AVOID, edgecolor='black', lw=0.5)
    ax2.bar(i, coll[cap], bottom=a, width=0.52,
            color=COLOR[cap] if cap == '4.2' else st.BLUE,
            edgecolor='black', lw=0.5)
    ax2.text(i, N + 0.25, f'{coll[cap]}/{N}', ha='center', fontsize=9)
ax2.text(0, 5, 'collided', ha='center', va='center', fontsize=7.5, color='white')
ax2.text(1, 5, 'avoided', ha='center', va='center', fontsize=7.5, color='#3a3f4c')
ax2.set_xticks([0, 1])
ax2.set_xticklabels(['cap 4.2 m/s', 'cap 3.0 m/s'], fontsize=8)
ax2.set_ylim(0, 12.9)
ax2.set_yticks([0, 5, 10])
ax2.set_ylabel('seeds (paired, S12–S21)', fontsize=8.5)
ax2.set_title('(b) primary contrast at 8 m', fontsize=9)
ax2.text(0.5, 0.985, 'discordant 10:0,  exact McNemar p = 0.002',
         transform=ax2.transAxes, ha='center', va='top', fontsize=7.5)
ax2.grid(axis='y', alpha=0.25)
ax2.set_axisbelow(True)
st.clean_axes(ax2)

fig.tight_layout(w_pad=2.0)
fig.savefig(OUT)
print('saved', OUT)
