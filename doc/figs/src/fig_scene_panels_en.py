#!/usr/bin/env python3
"""fig_scene_panels_en.png — representative scene panels, 2x3 (English).
0826 panel swap per user's picks: (a) KT_06 aerial driving (was a shoulder scene),
(e) real parking-lot aerial (K16, 8/10 demo; previous image was a shoulder),
(f) ped frame P6 (ped_centered_1786785303). Assets copied to assets/scene/."""
import os, sys
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import figstyle
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = ['STIXGeneral']
import matplotlib.pyplot as plt
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
A = f'{HERE}/assets/scene'
OUT = '/home/taewook/autoware_carla_leaderboard/doc/figs/en/fig_scene_panels_en.png'
ASPECT = 1.75

PANELS = [
    (f'{A}/kt06_driving.png', None,
     '(a)', 'Town07 driving scene (ego vehicle)'),
    (f'{A}/rviz.png', (0, 136, 1309, 884),
     '(b)', 'RViz perception view (LiDAR, camera, planned path)'),
    (f'{A}/vectormap.png', (100, 195, 1386, 930),
     '(c)', 'custom vector map with shoulder/parking-lot candidates'),
    (f'{A}/shoulder.png', None,
     '(d)', 'shoulder-evacuation MRC reached (traffic passes)'),
    (f'{A}/parking_aerial.png', (0, 140, 488, 419),
     '(e)', 'parking-lot evacuation MRC (aerial view)'),
    (f'{A}/ped.png', None,
     '(f)', 'pedestrian dart-out (crossing from right lane edge)'),
]

def crop_aspect(im, box=None, aspect=ASPECT):
    if box:
        im = im.crop(box)
    w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect); x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / aspect); y0 = (h - nh) // 2
        im = im.crop((0, y0, w, y0 + nh))
    return im

figstyle.apply()
fig, axes = plt.subplots(2, 3, figsize=(9.0, 4.4))
fig.subplots_adjust(wspace=0.035, hspace=0.30, left=0.005, right=0.995,
                    top=0.99, bottom=0.055)
for ax, (path, box, label, cap) in zip(axes.flat, PANELS):
    im = crop_aspect(Image.open(path).convert('RGB'), box)
    ax.imshow(im)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_edgecolor(figstyle.INK); s.set_linewidth(0.9)
    ax.text(0.02, 0.97, label, transform=ax.transAxes, ha='left', va='top',
            fontsize=10, fontweight='bold', color=figstyle.INK,
            bbox=dict(boxstyle='square,pad=0.25', fc='white',
                      ec=figstyle.INK, lw=0.8, alpha=0.9))
    ax.set_xlabel('%s %s' % (label, cap), fontsize=8.3, labelpad=3)
fig.savefig(OUT)
print('saved')
