# -*- coding: utf-8 -*-
"""그림 5-2 재생성: 본 캠페인 MRM 결과 히트맵 (v5 오딧 정정 A4).

baseline은 설계상 차선 내 정지 정책이므로 '대피 완료 0'이 실패가 아니라
정의상 결과(N/A)이다 — v4의 0/45 숫자 셀은 실패로 오독될 여지가 있어,
baseline 열을 회색 + "N/A — in-lane stop by design" 텍스트로 처리한다.

데이터: experiments/results/merged_final.csv (ours만 색상).
"""
import csv, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

RES = '/home/taewook/autoware_carla_leaderboard/experiments/results'
OUT = os.path.join(RES, 'fig_campaign_heatmap.png')

FAULT_KO = {
    'cf': '카메라 사망', 'cn': '카메라 노이즈', 'gn': 'GNSS 위치 노이즈',
    'imn': 'IMU 노이즈', 'lcl': '라이다 클러터', 'lf': '라이다 사망',
    'lso': '라이다 희박화',
}


def main():
    figstyle.apply()
    cnt = collections.defaultdict(lambda: [0, 0])   # (fault-sev) -> [evac, n] for ours
    for r in csv.DictReader(open(os.path.join(RES, 'merged_final.csv'))):
        if r['method'] != 'ours' or r['fault'] == 'nf':
            continue
        key = '%s-%s' % (r['fault'], r['severity'])
        cnt[key][1] += 1
        if r['outcome'] in ('SHOULDER_SUCCESS', 'PARKED_SUCCESS'):
            cnt[key][0] += 1
    rows = sorted(cnt)
    total = sum(v[1] for v in cnt.values())

    rates = np.array([[cnt[k][0] / cnt[k][1]] for k in rows])
    fig, ax = plt.subplots(figsize=(5.6, 6.4))
    ax.grid(False)
    # sequential 단일 색상(녹) 램프 — ours 열만 색상
    cmap = mcolors.LinearSegmentedColormap.from_list(
        'evac', ['#f4f9f3', '#1b6e3c'])
    im = ax.imshow(rates, cmap=cmap, vmin=0, vmax=1, aspect='auto',
                   extent=(0, 1, len(rows), 0))
    # baseline 열: 회색 (N/A)
    ax.axvspan(1, 2, color='#e4e4e4', zorder=0)
    for y in range(len(rows) + 1):
        ax.axhline(y, color='white', lw=2)
    ax.axvline(1, color='white', lw=2)

    for i, k in enumerate(rows):
        e, n = cnt[k]
        rate = e / n
        ax.text(0.5, i + 0.5, '%d/%d' % (e, n), ha='center', va='center',
                fontsize=9.5, color='white' if rate > 0.55 else figstyle.INK)
    ax.text(1.5, len(rows) / 2, 'N/A — in-lane stop by design',
            ha='center', va='center', rotation=90, fontsize=10.5,
            color='#6f6f6f')

    ax.set_xticks([0.5, 1.5])
    ax.set_xticklabels(['ours\n(대피 완료/전체 유효 케이스)', 'baseline\n(차선 내 정지 정책)'])
    ax.set_yticks([i + 0.5 for i in range(len(rows))])
    ax.set_yticklabels(['%s  (%s)' % (k, FAULT_KO[k.split('-')[0]]) for k in rows],
                       fontsize=9)
    ax.set_ylim(len(rows), 0)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title('MRM 결과: 대피 vs 차선 내 정지\n(본 캠페인 1,131 유효 케이스 중 고장 케이스, ours 열만 색상)',
                 fontsize=11)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cb.set_label('갓길·주차장 대피 완료 비율', fontsize=9)
    cb.outline.set_visible(False)
    fig.savefig(OUT)
    print('saved', OUT, 'ours cases:', total)


if __name__ == '__main__':
    main()
