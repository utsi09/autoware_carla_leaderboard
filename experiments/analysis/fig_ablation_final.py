# 그림 5-5. 절제 실험 결과 — 원장(RAW-HIT) 기준.
# A2는 0/10: S05R A2의 walker_hits=300은 저속 사다리 6런(01:02~01:17)의
# 히트 합이 케이스 창에 오귀속된 것으로, 케이스 창 내 RAW-HIT은 0건
# (0817 수치 감사에서 적발·정정).
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ARMS = ['A1 native\ncontinuation', 'A2 detection\n+ in-lane stop',
        'A3 uncapped\nevacuation', 'A4 capped(3.0)\nevacuation']
COLL = [7, 0, 3, 4]
N = 10

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.2), dpi=160,
                               gridspec_kw={'width_ratios': [1.15, 1]})
avoid = [N - c for c in COLL]
ax1.bar(ARMS, avoid, color='#2a8f4a', label='avoided')
ax1.bar(ARMS, COLL, bottom=avoid, color='#cc2f2f', label='collided')
for i, c in enumerate(COLL):
    ax1.text(i, N + 0.25, f'{c}/{N}', ha='center', fontsize=11)
ax1.set_ylim(0, 11.5)
ax1.set_ylabel('seeds (paired, S02–S11)')
ax1.set_title('(a) 8 m dart-out at t_detect+3 s (transient regime)')
ax1.legend(loc='lower right', fontsize=9)
ax1.grid(axis='y', alpha=0.3)
ax1.set_axisbelow(True)

ax2.bar(['transient\n(t_detect+3s)\nA4 capped', 'settled cruise\n(3.0, re-departure)\ncapped MRM'],
        [0.4, 0.0], color='#e8720c')
ax2.text(0, 0.41, '4/10', ha='center', fontsize=11)
ax2.text(1, 0.01, '0/8', ha='center', fontsize=11)
ax2.set_ylim(0, 1.0)
ax2.set_ylabel('collision rate')
ax2.set_title('(b) Same policy, two temporal regimes')
ax2.grid(axis='y', alpha=0.3)
ax2.set_axisbelow(True)

fig.tight_layout()
fig.savefig('/home/taewook/autoware_carla_leaderboard/experiments/results/fig_ablation_final.png')
print('saved fig_ablation_final.png')
