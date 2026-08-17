# -*- coding: utf-8 -*-
"""그림 3-1(시스템 구조)·그림 3-3(상태기계) 재정렬 — BT 구조도와 동일 시각 언어.

선 굵기·서체(나눔명조)·색(figstyle)을 fig_bt_structure와 통일한다.
내용은 v4와 동일(검증된 캡션 유지), 표현만 재정렬.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FIGS = '/home/taewook/autoware_carla_leaderboard/doc/figs'
INK = figstyle.INK


def box(ax, x, y, w, h, title, sub=None, fill='white', fs=9.5, sub_fs=8.0,
        title_dy=0.0):
    bp = FancyBboxPatch((x, y), w, h,
                        boxstyle='round,pad=0.012,rounding_size=0.014',
                        fc=fill, ec=INK, lw=figstyle.LW_BOX)
    ax.add_patch(bp)
    cy = y + h / 2 + (0.030 if sub else 0) + title_dy
    ax.text(x + w / 2, cy, title, ha='center', va='center', fontsize=fs,
            color=INK, fontweight='bold')
    if sub:
        ax.text(x + w / 2, cy - 0.070, sub, ha='center', va='center',
                fontsize=sub_fs, color='#4a5262')
    return dict(l=(x, y + h / 2), r=(x + w, y + h / 2),
                t=(x + w / 2, y + h), b=(x + w / 2, y))


def arrow(ax, p0, p1, label=None, ldx=0, ldy=0.018, ls='-', color=INK):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=13,
                                 lw=figstyle.LW_ARROW, color=color,
                                 linestyle=ls, shrinkA=1, shrinkB=1))
    if label:
        mx, my = (p0[0] + p1[0]) / 2 + ldx, (p0[1] + p1[1]) / 2 + ldy
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=7.8,
                color='#3a4252',
                bbox=dict(boxstyle='square,pad=0.12', fc='white', ec='none'))


def fig_system_arch():
    figstyle.apply()
    fig, ax = plt.subplots(figsize=(8.6, 4.3))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.grid(False)

    # 상단: 평가 스택 파이프라인
    yT, hT = 0.66, 0.20
    a = box(ax, 0.02, yT, 0.20, hT, 'CARLA 0.9.16', 'Town07 · 센서\n고장 주입',
            fill=figstyle.FILL_GRAY, fs=9.0)
    b = box(ax, 0.28, yT, 0.17, hT, '브리지', '센서 토픽 변환', fill=figstyle.FILL_BLUE,
            fs=9.0)
    c = box(ax, 0.51, yT, 0.25, hT, 'Autoware 0.39.0',
            '인지·계획·제어\nmission/goal_planner · mrm_handler',
            fill=figstyle.FILL_BLUE, fs=9.0)
    d = box(ax, 0.82, yT, 0.16, hT, '차량 제어', '가감속·조향 명령',
            fill=figstyle.FILL_GRAY, fs=9.0)
    arrow(ax, a['r'], b['l'])
    arrow(ax, b['r'], c['l'])
    arrow(ax, c['r'], d['l'])

    # 하단: 제안 감독 계층 (부가 계층)
    yB, hB = 0.13, 0.24
    m = box(ax, 0.17, yB, 0.26, hB, 'cdr_monitor',
            '행동트리 감시 (그림 3-2)\n신선도·품질·물리 3계열 점수화',
            fill=figstyle.FILL_GREEN, fs=9.5)
    s = box(ax, 0.55, yB, 0.28, hB, 'mrm_supervisor',
            '상태기계 (그림 3-3) · 대피지 비용함수\n속도 상한 3.0 m/s 부과',
            fill=figstyle.FILL_GREEN, fs=9.5)

    # 연결
    arrow(ax, (0.335, yT), (0.30, yB + hB), label='센서 토픽 구독', ldx=-0.065,
          ldy=-0.02)
    arrow(ax, m['r'], s['l'], label='/monitor/scores\n(건강도 점수)', ldy=0.012)
    arrow(ax, (0.69, yB + hB), (0.665, yT),
          label='경로 재설정(AD API) ·\n속도 상한 후보 · 진단 ERROR', ldx=0.135,
          ldy=-0.055)

    # 제안 계층 묶음 표시
    ax.plot([0.145, 0.145, 0.855, 0.855], [yB + hB + 0.055, yB - 0.045,
                                           yB - 0.045, yB + hB + 0.055],
            color='#7c8b7a', lw=1.0, ls=(0, (4, 3)))
    ax.text(0.50, yB - 0.075, '제안 감독 계층 (부가 add-on — 스택 본체 수정 최소화)',
            ha='center', fontsize=8.2, color='#4c5a4a')
    fig.savefig(os.path.join(FIGS, 'fig_system_arch.png'))
    print('saved fig_system_arch.png')
    plt.close(fig)


def fig_state_machine():
    figstyle.apply()
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.grid(False)

    hS = 0.22
    n = box(ax, 0.03, 0.40, 0.17, hS, 'NORMAL', '정상 주행',
            fill=figstyle.FILL_BLUE)
    mv = box(ax, 0.38, 0.66, 0.22, hS, 'MRM_MOVE', '저속 대피 이동\n(상한 3.0 m/s)',
             fill=figstyle.FILL_GREEN)
    pk = box(ax, 0.76, 0.66, 0.21, hS, 'MRM_PARKED', '갓길/주차장 MRC',
             fill=figstyle.FILL_GREEN)
    df = box(ax, 0.38, 0.10, 0.22, hS, 'MRM_DEFER', '순정 정차 위임',
             fill=figstyle.FILL_RED)
    aw = box(ax, 0.76, 0.10, 0.21, hS, 'Autoware 정지 MRM', '차선 내 정지',
             fill=figstyle.FILL_RED, fs=8.8)

    arrow(ax, (0.20, 0.57), (0.38, 0.74),
          label='0.3 < health ≤ 0.7\n(대피 후보 있음)', ldx=-0.045, ldy=0.030)
    arrow(ax, mv['r'], pk['l'], label='대피 목표 도달', ldy=0.014)
    arrow(ax, (0.20, 0.45), (0.38, 0.28),
          label='health ≤ 0.3 또는\n위치 신뢰 붕괴·후보 없음', ldx=-0.055, ldy=-0.085)
    arrow(ax, df['r'], aw['l'], label='진단 그래프\nERROR 주입', ldy=0.020)
    # MOVE 실패 → DEFER 폴백
    arrow(ax, (0.49, 0.66), (0.49, 0.32),
          label='이동 실패\n(정체·워치독)', ldx=0.062, ldy=-0.058, ls=(0, (4, 3)))

    # 임계 밴드 요약 (좌하단 여백)
    ax.text(0.02, 0.055, '건강도 이중 임계: 상단 0.7 (개입 진입) · 하단 0.3 (이동 포기·위임)',
            fontsize=8.4, color='#3a4252')
    ax.text(0.02, 0.000, '오발동 방지: 부팅 건강 확인 · 경로변경 워치독 · 후보 블랙리스트 · 크립 가드',
            fontsize=7.8, color='#5a6270')
    fig.savefig(os.path.join(FIGS, 'fig_state_machine.png'))
    print('saved fig_state_machine.png')
    plt.close(fig)


if __name__ == '__main__':
    fig_system_arch()
    fig_state_machine()
