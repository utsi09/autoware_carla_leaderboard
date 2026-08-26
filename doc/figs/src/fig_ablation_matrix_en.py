#!/usr/bin/env python3
"""fig_ablation_matrix_en.png — ablation seed x arm dot matrix (English).
0826: no red fill (B/W: collision = filled black, avoided = open circle); legend moved to top."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
})

seeds = ['S02','S03','S04','S05','S06','S07','S08','S09','S10','S11',
         'S12','S13','S14','S15','S16','S17','S18','S19','S20','S21']
C = {'A1': ['S02','S03','S04','S05','S07','S08','S10','S12','S13','S15','S18','S19','S20','S21'],
     'A2': [],
     'A3': ['S05','S07','S08','S12','S13','S14','S15','S19','S20','S21'],
     'A4': ['S03','S05','S07','S08','S12','S13','S14','S15','S19','S20','S21']}
arms = ['A1','A2','A3','A4']
labels = ['A1\nnative', 'A2\ndetect\n+ stop', 'A3\nevac\n(no cap)', 'A4\nevac\n(capped)']

fig, ax = plt.subplots(figsize=(3.4, 5.2), dpi=200)
for j, a in enumerate(arms):
    for i, s in enumerate(seeds):
        hit = s in C[a]
        ax.plot(j, len(seeds) - 1 - i, marker='o', ms=6.5,
                mfc=('#222222' if hit else 'white'), mec='black', mew=0.7, ls='none')
ax.axhline(len(seeds) - 10 - 0.5, color='black', lw=0.7, ls='--')
ax.text(3.6, len(seeds) - 5.5, 'Round 1\nS02–S11', fontsize=8, va='center')
ax.text(3.6, 4.5, 'Extension\nS12–S21', fontsize=8, va='center')
ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=8)
ax.set_yticks(range(len(seeds))); ax.set_yticklabels(seeds[::-1], fontsize=7)
ax.set_xlim(-0.6, 4.9); ax.set_ylim(-0.8, len(seeds) - 0.2)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(length=0)
ax.plot([], [], marker='o', mfc='#222222', mec='black', ls='none', ms=6.5, label='collision')
ax.plot([], [], marker='o', mfc='white', mec='black', ls='none', ms=6.5, label='avoided')
ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.005), ncol=2, fontsize=8,
          frameon=False, handletextpad=0.4, columnspacing=1.6)
fig.tight_layout()
fig.savefig('/home/taewook/autoware_carla_leaderboard/doc/figs/en/fig_ablation_matrix_en.png',
            bbox_inches='tight', pad_inches=0.06, facecolor='white')
print('saved')
