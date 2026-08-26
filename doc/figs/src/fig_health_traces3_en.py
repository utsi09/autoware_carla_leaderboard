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
    pts = [(x, y) for x, y in zip(xs, ys) if x >= EXTRA_CUT]
    return [p[0] for p in pts], [p[1] for p in pts]
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

matplotlib.rcParams['font.family'] = ['STIXGeneral']
OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig12_health.png'

figstyle.apply()
matplotlib.rcParams['font.family'] = ['STIXGeneral']

# 주입 시점: 해당 센서 원시 점수의 계단 하강(지속 확인)으로 검출.
# lso-mid(T=0.33)는 품질 지표 노이즈에 계단이 묻혀 식별 불가 -> 미표기(감내 등급의 방증).
def detect_onset(fname, ch):
    xs, ys = series_pts(fname, ch)
    if not xs:
        return None
    base = sorted(ys[:50])[min(len(ys), 50) // 2]
    for i, (t, v) in enumerate(zip(xs, ys)):
        if v < base * 0.6 and all(vv < base * 0.8 for vv in ys[i:i + 20]):
            return t
    return None

PANELS = [
    ('(a) LiDAR soiling (lso)', 'sensor/LIDAR_front',
     [('scoretrace_nf_mid.csv', 'fault-free', figstyle.C_NF, None),
      ('scoretrace_lso_mid.csv', 'mid (tolerated)', figstyle.C_MID, None),
      ('scoretrace_lso_high.csv', 'high (intervention)', figstyle.C_HIGH,
       'sensor/LIDAR_front')]),
    ('(b) camera pixel noise (cn)', 'sensor/CAMERA_front',
     [('scoretrace_nf_mid.csv', 'fault-free', figstyle.C_NF, None),
      ('scoretrace_cn_mid.csv', 'mid (intervention)', figstyle.C_MID,
       'sensor/CAMERA_front'),
      ('scoretrace_cn_high.csv', 'high (intervention)', figstyle.C_HIGH,
       'sensor/CAMERA_front')]),
]

fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.4), dpi=200,
                         sharex='col', sharey='row')
for col, (title, raw_ch, series) in enumerate(PANELS):
    ax_cap, ax_raw = axes[0][col], axes[1][col]
    onsets = []
    for fname, label, color, onset_ch in reversed(series):
        xs, ys = series_pts(fname, 'capability/perception')
        ax_cap.plot(xs, ys, color=color, lw=1.2, ls='-', label=label,
                    solid_joinstyle='round')
        rx, ry = series_pts(fname, raw_ch)
        ax_raw.plot(rx, ry, color=color, lw=1.0, ls='-', alpha=0.9,
                    solid_joinstyle='round')
        if onset_ch:
            t_inj = detect_onset(fname, onset_ch)
            if t_inj is not None:
                for ax in (ax_cap, ax_raw):
                    ax.axvline(t_inj, color=color, lw=0.9, ls=(0, (2, 2)), alpha=0.6)
                onsets.append(t_inj)
    if onsets:
        ax_cap.text(max(onsets) + 4, 1.03, 'fault onset', fontsize=7,
                    color='#5a6170', ha='left', va='top')
    for y in (0.7, 0.3):
        ax_cap.axhline(y, color='#3a3f4c', lw=0.8, ls=(0, (5, 3)))
    ax_cap.set_ylim(0.0, 1.06)
    ax_raw.set_ylim(0.0, 1.06)
    for ax in (ax_cap, ax_raw):
        ax.set_xlim(left=21)
        ax.tick_params(labelsize=7)
    ax_cap.set_title(title, fontsize=8)
    ax_raw.set_xlabel('time since engagement [s]', fontsize=7.5)

axes[0][0].set_ylabel('perception capability\n(decision input)', fontsize=8)
axes[1][0].set_ylabel('affected-sensor\nraw score', fontsize=8)
axes[0][0].text(24, 0.72, r'$\theta_H$', fontsize=8, color='#3a3f4c', va='bottom')
axes[0][0].text(24, 0.32, r'$\theta_L$', fontsize=8, color='#3a3f4c', va='bottom')
axes[0][0].legend(loc='lower right', frameon=False, fontsize=6.5)
axes[0][1].legend(loc='lower right', frameon=False, fontsize=6.5)
fig.tight_layout()
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.05)
print('saved')
