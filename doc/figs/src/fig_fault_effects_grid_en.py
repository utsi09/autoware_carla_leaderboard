#!/usr/bin/env python3
"""그림 4-2 v3 — fault effects as 3x5 grid (columns = sensor families).
(a) lso: nominal/mid/high BEV, (b) lcl: nominal/mid/high, (c) cn: nominal/mid/high,
(d) GNSS waveforms: gn/gb/gf, (e) gyro waveforms: imn/imb/imd.
Output: doc/paper_build/figs/fig6_faults.png (thesis 그림 4-2)."""
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import ieee_style as st
matplotlib.rcParams['font.family'] = ['STIXGeneral']
import matplotlib.pyplot as plt

R = '/home/taewook/autoware_carla_leaderboard/experiments/results'
OUT = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig6_faults.png'
rng = np.random.default_rng(4)
pts = np.load(f'{R}/figframe_lidar.npy'); img = np.load(f'{R}/figframe_cam.npy')
PMIN = 0.9 / (np.pi * 100.0 ** 2)

def lso(p, T, w):
    x, y, z, rho = p[:, 0], p[:, 1], p[:, 2], np.clip(p[:, 3], 0, 1)
    r2 = x * x + y * y + z * z
    az = np.degrees(np.arctan2(y, x)); d = np.abs(az); d = np.where(d > 180, 360 - d, d)
    sect = d <= w * 0.5; rho = np.where(sect, rho * T * T, rho)
    keep = ~(sect & (r2 > 0.01) & (rho / r2 < PMIN))
    return np.column_stack([x, y, z, rho])[keep]

def lcl(p, Rr, N):
    x, y, z, rho = p[:, 0].copy(), p[:, 1].copy(), p[:, 2].copy(), np.clip(p[:, 3], 0, 1)
    r = np.sqrt(x * x + y * y + z * z); a = 0.01 * Rr ** 0.6; jit = 0.02 * (1 - np.exp(-Rr)) ** 2
    rho = rho * np.exp(-2 * a * r); keep = (rho / np.maximum(r * r, 0.01)) >= PMIN
    sc = 1 + jit * r * rng.standard_normal(len(r)) / np.maximum(r, 0.01)
    base = np.column_stack([x * sc, y * sc, z * sc, rho])[keep]
    az = rng.uniform(0, 2 * np.pi, N); u = rng.uniform(0, 1, N); cr = 2 + u * u * 8.0
    clut = np.column_stack([cr * np.cos(az), cr * np.sin(az),
                            rng.uniform(-0.4, 1.2, N), np.full(N, 4 / 255)])
    return base, clut

def bev(ax, p, clut=None, title=''):
    ax.scatter(p[:, 0], p[:, 1], s=0.12, c='#333333', alpha=0.55, rasterized=True, linewidths=0)
    if clut is not None:
        ax.scatter(clut[:, 0], clut[:, 1], s=0.35, c=st.RED, rasterized=True, linewidths=0)
    ax.plot(0, 0, 'k^', ms=3)
    ax.set_xlim(-60, 60); ax.set_ylim(-60, 60); ax.set_aspect('equal')
    ax.set_title(title, fontsize=6.6)
    ax.tick_params(labelsize=4.6, length=1.5, pad=1); ax.grid(alpha=0.2)

def wpanel(ax, x, y, title, ylab=None):
    ax.plot(x, y, lw=0.55, color='black')
    ax.set_title(title, fontsize=6.6)
    ax.tick_params(labelsize=4.6, length=1.5, pad=1); ax.grid(alpha=0.25)
    if ylab:
        ax.set_ylabel(ylab, fontsize=5.4, labelpad=1)
    st.clean_axes(ax)

fig, axes = plt.subplots(3, 5, figsize=(12.6, 7.4), dpi=200)
plt.subplots_adjust(wspace=0.34, hspace=0.42, left=0.045, right=0.99, top=0.90, bottom=0.06)

# (a) lso
bev(axes[0][0], pts, title='nominal\n(55,313 pts)')
bev(axes[1][0], lso(pts, 0.33, 90), title='lso-mid (T=0.33, 90°)\n(53,585 pts)')
bev(axes[2][0], lso(pts, 0.07, 150), title='lso-high (T=0.07, 150°)\n(46,153 pts)')
# (b) lcl
bev(axes[0][1], pts, title='nominal\n(55,313 pts)')
b, c = lcl(pts, 5, 1500); bev(axes[1][1], b, clut=c, title='lcl-mid (5 mm/h)\n(49,373 pts)')
b, c = lcl(pts, 25, 4000); bev(axes[2][1], b, clut=c, title='lcl-high (25 mm/h)\n(43,987 pts)')
# (c) cn
for ri, (s_, t) in enumerate([(0, 'nominal'), (15, 'cn-mid (σ=15)'), (30, 'cn-high (σ=30)')]):
    ax = axes[ri][2]
    im = np.clip(img.astype(float) + rng.normal(0, s_, img.shape), 0, 255).astype(np.uint8) if s_ else img
    ax.imshow(im); ax.set_xticks([]); ax.set_yticks([]); ax.set_title(t, fontsize=6.6)
# (d) GNSS waveforms
t_ = np.arange(0, 120, 0.05)
gn = rng.normal(0, 1.0, len(t_))
a = np.exp(-0.05 / 30.0); drv = 3.0 * np.sqrt(1 - a * a)
gm = np.zeros(len(t_))
for i in range(1, len(t_)):
    gm[i] = a * gm[i - 1] + rng.normal(0, drv)
wpanel(axes[0][3], t_, gn, 'gn — white noise (σ=1 m)', 'error [m]')
wpanel(axes[1][3], t_, gm, 'gb — correlated bias (σ=3 m, τ=30 s)', 'bias [m]')
ax = axes[2][3]
T_OFF = 40.0
ax.step([0, T_OFF, 120], [1, 0, 0], where='post', lw=1.0, color='black')
ax.axvspan(T_OFF, 120, color='0.9', zorder=0)
ax.text((T_OFF + 120) / 2, 0.5, 'no fix', ha='center', fontsize=5.6)
ax.set_ylim(-0.1, 1.25); ax.set_yticks([0, 1]); ax.set_yticklabels(['off', 'on'], fontsize=4.6)
ax.set_title('gf — GNSS blackout', fontsize=6.6)
ax.tick_params(labelsize=4.6, length=1.5, pad=1)
ax.set_xlabel('time [s]', fontsize=5.2, labelpad=1)
st.clean_axes(ax)
# (e) gyro waveforms
wpanel(axes[0][4], t_, rng.normal(0, 0.05, len(t_)), 'imn — white noise (σ=0.05 rad/s)', 'yaw-rate error [rad/s]')
ax = axes[1][4]
ax.plot(t_, np.full_like(t_, 0.3), lw=1.0, color='black'); ax.set_ylim(0, 0.65)
ax.set_title('imb — fixed bias (0.3 rad/s)', fontsize=6.6)
ax.tick_params(labelsize=4.6, length=1.5, pad=1); ax.grid(alpha=0.25)
ax.set_ylabel('bias [rad/s]', fontsize=5.4, labelpad=1); st.clean_axes(ax)
ax = axes[2][4]
ax.plot(t_, 0.005 * t_, lw=1.0, color='black'); ax.set_ylim(0, 0.65)
ax.set_title('imd — bias ramp (0.005 rad/s²)', fontsize=6.6)
ax.tick_params(labelsize=4.6, length=1.5, pad=1); ax.grid(alpha=0.25)
ax.set_ylabel('bias [rad/s]', fontsize=5.4, labelpad=1)
ax.set_xlabel('time [s]', fontsize=5.2, labelpad=1); st.clean_axes(ax)
for ci in (3, 4):
    axes[2][ci].set_xlabel('time [s]', fontsize=5.2, labelpad=1)
axes[2][0].set_xlabel('x [m]', fontsize=5.2, labelpad=1)
axes[2][1].set_xlabel('x [m]', fontsize=5.2, labelpad=1)
axes[1][0].set_ylabel('y [m]', fontsize=5.4, labelpad=1)

# 열 헤더
HEADS = ['(a) LiDAR sparsification (lso)', '(b) LiDAR clutter (lcl)', '(c) camera noise (cn)',
         '(d) GNSS faults', '(e) gyro faults']
for ci, h in enumerate(HEADS):
    pos = axes[0][ci].get_position()
    fig.text((pos.x0 + pos.x1) / 2, 0.965, h, ha='center', fontsize=8, fontweight='bold')

fig.savefig(OUT, bbox_inches='tight', pad_inches=0.06)
print('saved')
