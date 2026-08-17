# -*- coding: utf-8 -*-
"""그림 4-2 신규: 실험 환경·대표 장면 실사 패널 (2행 3열).

캡처 원본: scratchpad/figzip/피규어 + experiments/results/ped_centered_*.
각 패널을 동일 종횡비(1.75)로 중앙 크롭하고 (a)~(f) 라벨을 부여한다.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt
from PIL import Image

CAP = ('/tmp/claude-1000/-home-taewook-autoware-carla-leaderboard/'
       '3a654bb5-ccec-4bf3-a05d-7c11727be86b/scratchpad/figzip/피규어')
RES = '/home/taewook/autoware_carla_leaderboard/experiments/results'
OUT = '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_scene_panels.png'

ASPECT = 1.75

PANELS = [
    # (파일, 수동 크롭 box 또는 None, 라벨, 캡션)
    (os.path.join(CAP, 'KakaoTalk_20260817_115838407_05.png'), None,
     '(a)', 'Town07 주행 장면 (에고 차량)'),
    (os.path.join(CAP, '스크린샷 2026-07-29 16-14-23.png'), (0, 136, 1309, 884),
     '(b)', 'RViz 인식 화면 (라이다·카메라·계획 경로)'),
    (os.path.join(CAP, '스크린샷 2026-08-07 13-18-57.png'), (100, 195, 1386, 930),
     '(c)', '갓길·주차장 후보 주석 자체 벡터맵'),
    (os.path.join(CAP, '스크린샷 2026-07-31 15-13-01.png'), None,
     '(d)', '갓길 대피 MRC 도달 (후속 교통 통과)'),
    (os.path.join(CAP, 'KakaoTalk_20260817_115838407_07.png'), (1360, 0, 2680, 758),
     '(e)', '주차장 대피 MRC (상공 뷰)'),
    (os.path.join(RES, 'ped_centered_1786786367.png'), None,
     '(f)', '보행자 돌발 조우 (차선 우측 끝 횡단 개시)'),
]


def crop_aspect(im, box=None, aspect=ASPECT):
    if box:
        im = im.crop(box)
    w, h = im.size
    if w / h > aspect:      # 너무 넓음 → 좌우 절단
        nw = int(h * aspect)
        x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:                   # 너무 높음 → 상하 절단
        nh = int(w / aspect)
        y0 = (h - nh) // 2
        im = im.crop((0, y0, w, y0 + nh))
    return im


def main():
    figstyle.apply()
    fig, axes = plt.subplots(2, 3, figsize=(9.0, 4.4))
    fig.subplots_adjust(wspace=0.035, hspace=0.30, left=0.005, right=0.995,
                        top=0.99, bottom=0.055)
    for ax, (path, box, label, cap) in zip(axes.flat, PANELS):
        im = crop_aspect(Image.open(path).convert('RGB'), box)
        ax.imshow(im)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_edgecolor(figstyle.INK)
            s.set_linewidth(0.9)
        ax.text(0.02, 0.97, label, transform=ax.transAxes, ha='left', va='top',
                fontsize=10, fontweight='bold', color=figstyle.INK,
                bbox=dict(boxstyle='square,pad=0.25', fc='white',
                          ec=figstyle.INK, lw=0.8, alpha=0.9))
        ax.set_xlabel('%s %s' % (label, cap), fontsize=8.3, labelpad=3)
    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
