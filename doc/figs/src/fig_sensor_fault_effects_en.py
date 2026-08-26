#!/usr/bin/env python3
"""fig_sensor_fault_effects_en.png — sensor fault effect gallery (English).
0826: nav waveform row expanded to all five nav faults —
GNSS family: gn (white noise) / gb (correlated bias, was 'gm') / gf (blackout, was 'gb'),
gyro family: imb (fixed bias) / imd (bias ramp). Naming follows the thesis
renaming rule (extra_faults_supplement_0820.md): gm->gb, gb->gf."""
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import ieee_style as st
matplotlib.rcParams['font.family'] = ['STIXGeneral']
import matplotlib.pyplot as plt

R = '/home/taewook/autoware_carla_leaderboard/experiments/results'
OUT = '/home/taewook/autoware_carla_leaderboard/doc/figs/en/fig_sensor_fault_effects_en.png'
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

def bev(ax, p, clut=None, title=""):
    ax.scatter(p[:, 0], p[:, 1], s=0.25, c='#333333', alpha=0.55, rasterized=True, linewidths=0)
    if clut is not None:
        ax.scatter(clut[:, 0], clut[:, 1], s=0.6, c=st.RED, rasterized=True, linewidths=0)
    ax.plot(0, 0, 'k^', ms=4)
    ax.set_xlim(-60, 60); ax.set_ylim(-60, 60); ax.set_aspect('equal')
    ax.set_title(f"{title}\n({len(p):,} pts)", fontsize=7)
    ax.tick_params(labelsize=5.5); ax.grid(alpha=0.2)

fig = plt.figure(figsize=(6.4, 10.6))
gs = fig.add_gridspec(5, 3, hspace=0.55, wspace=0.3)

for j, (T, w, t) in enumerate([(1.0, 0, 'nominal'), (0.33, 90, 'lso-mid (T=0.33, 90°)'),
                               (0.07, 150, 'lso-high (T=0.07, 150°)')]):
    ax = fig.add_subplot(gs[0, j]); bev(ax, lso(pts, T, w) if T < 1 else pts, title=t)
    if j == 0: ax.set_ylabel('(a) LiDAR soiling\ny [m]', fontsize=7)
for j, (Rr, N, t) in enumerate([(0, 0, 'nominal'), (5, 1500, 'lcl-mid (5 mm/h)'),
                                (25, 4000, 'lcl-high (25 mm/h)')]):
    ax = fig.add_subplot(gs[1, j])
    if Rr == 0: bev(ax, pts, title=t)
    else:
        b, c = lcl(pts, Rr, N); bev(ax, b, clut=c, title=t)
    if j == 0: ax.set_ylabel('(b) LiDAR clutter (rain)\ny [m]', fontsize=7)
for j, (s, t) in enumerate([(0, 'nominal'), (15, 'cn-mid (σ=15)'), (30, 'cn-high (σ=30)')]):
    ax = fig.add_subplot(gs[2, j])
    im = np.clip(img.astype(float) + rng.normal(0, s, img.shape), 0, 255).astype(np.uint8) if s > 0 else img
    ax.imshow(im); ax.set_xticks([]); ax.set_yticks([]); ax.set_title(t, fontsize=7)
    if j == 0: ax.set_ylabel('(c) camera pixel noise', fontsize=7)

t_ = np.arange(0, 120, 0.05)
gn = rng.normal(0, 1.0, len(t_))
a = np.exp(-0.05 / 30.0); drv = 3.0 * np.sqrt(1 - a * a)
gm = np.zeros(len(t_))
for i in range(1, len(t_)):
    gm[i] = a * gm[i - 1] + rng.normal(0, drv)

def wave(ax, t, yl):
    ax.set_title(t, fontsize=7); ax.tick_params(labelsize=5.5); ax.grid(alpha=0.25)
    ax.set_xlabel('time [s]', fontsize=6.5)
    if yl: ax.set_ylabel(yl, fontsize=7)
    st.clean_axes(ax)

# row (d): GNSS family — white noise / correlated bias / blackout
ax = fig.add_subplot(gs[3, 0])
ax.plot(t_, gn, lw=0.5, color='black')
wave(ax, 'gn — white noise (σ=1 m)', '(d) nav faults: GNSS\nerror [m]')
ax = fig.add_subplot(gs[3, 1])
ax.plot(t_, gm, lw=0.9, color='black')
wave(ax, 'gb — correlated bias (σ=3 m, τ=30 s)', None)
ax = fig.add_subplot(gs[3, 2])
T_OFF = 40.0
ax.step([0, T_OFF, 120], [1, 0, 0], where='post', lw=1.2, color='black')
ax.axvspan(T_OFF, 120, color='0.85', zorder=0)
ax.text((T_OFF + 120) / 2, 0.5, 'no fix', ha='center', fontsize=6.5)
ax.set_ylim(-0.1, 1.25); ax.set_yticks([0, 1]); ax.set_yticklabels(['off', 'on'], fontsize=5.5)
wave(ax, 'gf — GNSS blackout (no fix after onset)', None)

# row (e-cont.): gyro family — fixed bias / bias ramp
ax = fig.add_subplot(gs[4, 0])
ax.plot(t_, np.full_like(t_, 0.3), lw=1.2, color='black')
ax.set_ylim(0, 0.65)
wave(ax, 'imb — fixed bias (0.3 rad/s)', 'nav faults: gyro\nbias [rad/s]')
ax = fig.add_subplot(gs[4, 1])
ax.plot(t_, 0.005 * t_, lw=1.2, color='black')
ax.set_ylim(0, 0.65)
wave(ax, 'imd — bias ramp (0.005 rad/s²)', None)
fig.add_subplot(gs[4, 2]).axis('off')

plt.savefig(OUT); plt.close()
print('saved')
