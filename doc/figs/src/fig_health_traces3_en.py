#!/usr/bin/env python3
"""그림 5-2 v4 — injection-aligned health traces, 2x2.
Top row: fused perception capability (decision input, thresholds 0.7/0.3).
Bottom row: affected sensor's raw score. Columns: (a) lso, (b) cn.
x = time since fault injection (exact sim time from fault_ledger FAULT_ACTIVE,
matched to each trace CSV by file mtime). Fault-free variability is shown as a
P5-P95 band instead of a time-aligned curve (no injection anchor exists for nf).
gn/imn excluded by design (supervisor-internal residual detectors)."""
import os, sys
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import figstyle
from fig_health_traces import parse, clean, RES, DRIVE_START_S
import matplotlib.pyplot as plt

matplotlib.rcParams['font.family'] = ['STIXGeneral']
OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig12_health.png'
LEDGER = os.path.join(RES, 'fault_ledger.log')

figstyle.apply()
matplotlib.rcParams['font.family'] = ['STIXGeneral']

_led = [(float(l.split()[0]), float(l.split()[2].split('=')[1]))
        for l in open(LEDGER) if 'FAULT_ACTIVE' in l]

def inj_sim(fname):
    """CSV 파일 mtime(레코더 종료≈케이스 종료)으로 원장 FAULT_ACTIVE를 매칭."""
    mt = os.path.getmtime(os.path.join(RES, fname))
    hits = [s for w, s in _led if mt - 420 <= w <= mt + 10]
    assert hits, f'no ledger FAULT_ACTIVE for {fname}'
    return hits[-1]

def series_rel(fname, ch, t_ref):
    d = clean(parse(os.path.join(RES, fname), ch))
    return [t - t_ref for t, v in d], [v for t, v in d]

def nf_band(ch):
    d = clean(parse(os.path.join(RES, 'scoretrace_nf_mid.csv'), ch))
    t0 = d[0][0] + DRIVE_START_S + 18.0
    vs = sorted(v for t, v in d if t >= t0)
    return vs[int(len(vs) * 0.05)], vs[int(len(vs) * 0.95)]

PANELS = [
    ('(a) LiDAR soiling (lso)', 'sensor/LIDAR_front',
     [('scoretrace_lso_mid.csv', 'mid (tolerated)', figstyle.C_MID),
      ('scoretrace_lso_high.csv', 'high (intervention)', figstyle.C_HIGH)]),
    ('(b) camera pixel noise (cn)', 'sensor/CAMERA_front',
     [('scoretrace_cn_mid.csv', 'mid (intervention)', figstyle.C_MID),
      ('scoretrace_cn_high.csv', 'high (intervention)', figstyle.C_HIGH)]),
]

fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.4), dpi=200,
                         sharex='col', sharey='row')
for col, (title, raw_ch, series) in enumerate(PANELS):
    ax_cap, ax_raw = axes[0][col], axes[1][col]
    for ax, ch in ((ax_cap, 'capability/perception'), (ax_raw, raw_ch)):
        lo, hi = nf_band(ch)
        ax.axhspan(lo, hi, color=figstyle.C_NF, alpha=0.14, lw=0,
                   label='fault-free range (P5–P95)')
        ax.axvline(0, color='#3a3f4c', lw=0.9, ls=(0, (2, 2)), alpha=0.8)
    for fname, label, color in series:
        t_inj = inj_sim(fname)
        for ax, ch in ((ax_cap, 'capability/perception'), (ax_raw, raw_ch)):
            xs, ys = series_rel(fname, ch, t_inj)
            pts = [(x, y) for x, y in zip(xs, ys) if -20 <= x <= 120]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color,
                    lw=1.1, ls='-', label=(label if ax is ax_cap else None),
                    solid_joinstyle='round')
    for y in (0.7, 0.3):
        ax_cap.axhline(y, color='#3a3f4c', lw=0.8, ls=(0, (5, 3)))
    ax_cap.set_ylim(0.0, 1.06); ax_raw.set_ylim(0.0, 1.06)
    for ax in (ax_cap, ax_raw):
        ax.set_xlim(-20, 120)
        ax.tick_params(labelsize=7)
    ax_cap.set_title(title, fontsize=8)
    ax_raw.set_xlabel('time since fault injection [s]', fontsize=7.5)
    ax_cap.text(2, 1.0, 'injection', fontsize=6.5, color='#5a6170',
                ha='left', va='top')

axes[0][0].set_ylabel('perception capability\n(decision input)', fontsize=8)
axes[1][0].set_ylabel('affected-sensor\nraw score', fontsize=8)
axes[0][0].text(-17, 0.72, r'$\theta_H$', fontsize=8, color='#3a3f4c', va='bottom')
axes[0][0].text(-17, 0.32, r'$\theta_L$', fontsize=8, color='#3a3f4c', va='bottom')
axes[0][0].legend(loc='lower right', frameon=False, fontsize=6.2)
axes[0][1].legend(loc='lower right', frameon=False, fontsize=6.2)
fig.tight_layout()
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.05)
print('saved')
