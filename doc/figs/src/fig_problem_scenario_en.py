#!/usr/bin/env python3
"""fig_problem_scenario_en.png — two PPT-drawn panels + caption/legend overlay.
Panels (assets/image1.png, image2.png) come from the user's PowerPoint drawing.
0826: legend (1) 'adjacent shoulder' -> 'free space'."""
import os, sys
sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
import figstyle, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

figstyle.apply()
matplotlib.rcParams['font.family'] = ['STIXGeneral']
INK = figstyle.INK
HERE = os.path.dirname(os.path.abspath(__file__))
E = '/home/taewook/autoware_carla_leaderboard/doc/figs/en'

def white(p):
    im = Image.open(p).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert('RGB')

im1 = white(f'{HERE}/assets/image1.png')
im2 = white(f'{HERE}/assets/image2.png')
fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.6))
fig.subplots_adjust(wspace=0.06, left=0.01, right=0.99, top=0.98, bottom=0.17)
for ax, im, lab, cap in [(axes[0], im1, '(a)', 'Refuge options upon sensor fault'),
                         (axes[1], im2, '(b)', 'Edge case — pedestrian dart-out during evacuation')]:
    ax.imshow(im); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel(f'{lab} {cap}', fontsize=8.6, labelpad=6)
fig.text(0.5, 0.035, '① free space    ② parking lot    ③ downstream shoulder    ④ in-lane stop'
         '     —  candidates ranked by the cost function', ha='center', fontsize=8.0, color=INK)
fig.savefig(f'{E}/fig_problem_scenario_en.png')
print('saved')
