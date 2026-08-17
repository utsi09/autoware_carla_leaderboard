# -*- coding: utf-8 -*-
"""그림 4-1 재제작(v17): 실험 환경 폐루프 블록도.

캡션(content2.py fig4_1)과 일치하도록:
  CARLA 0.9.16(호스트) ↔ ROS 2 브리지(컨테이너) ↔ Autoware 0.39.0(컨테이너)의
  폐루프 — 센서 데이터(CARLA→브리지→Autoware)와 제어 명령(Autoware→브리지→CARLA)
  양방향 화살표 명시. 시나리오 러너·리더보드(컨테이너)가 CARLA를 제어·평가.
  하단에 갓길·주차장 후보가 주석된 자체 제작 Town07 벡터맵 블록.
  감시(cdr_monitor)·감독자(mrm_supervisor)는 Autoware 컨테이너 내부 애드온 소박스.

구판(8 m 보행자 돌발 설계도)은 그림 4-3(fig_encounter_design.png)으로 분리.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_experiment_setup.png'
INK = figstyle.INK
SUB = '#4a5262'


def box(ax, x, y, w, h, title, sub=None, fill='white', fs=9.5, sub_fs=8.0,
        ls='-', lw=None, bold=True):
    bp = FancyBboxPatch((x, y), w, h,
                        boxstyle='round,pad=0.008,rounding_size=0.010',
                        fc=fill, ec=INK, lw=lw or figstyle.LW_BOX, ls=ls)
    ax.add_patch(bp)
    cy = y + h / 2 + (0.032 if sub else 0)
    ax.text(x + w / 2, cy, title, ha='center', va='center', fontsize=fs,
            color=INK, fontweight='bold' if bold else 'normal')
    if sub:
        ax.text(x + w / 2, cy - 0.066, sub, ha='center', va='center',
                fontsize=sub_fs, color=SUB)


def arrow(ax, p0, p1, color=INK, lw=None):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>',
                                 mutation_scale=13, color=color,
                                 lw=lw or figstyle.LW_ARROW,
                                 shrinkA=1, shrinkB=1, zorder=4))


def main():
    figstyle.apply()
    fig, ax = plt.subplots(figsize=(9.0, 4.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.grid(False)

    # ---- 실행 구획: 호스트 / 컨테이너 (점선 프레임) ----
    box(ax, 0.02, 0.28, 0.24, 0.65, '', ls=(0, (4, 3)), lw=1.0, fill='none')
    ax.text(0.035, 0.905, '호스트', fontsize=8.8, color=SUB, ha='left',
            fontweight='bold')
    box(ax, 0.295, 0.28, 0.685, 0.65, '', ls=(0, (4, 3)), lw=1.0, fill='none')
    ax.text(0.31, 0.905, '독립 컨테이너 ×3', fontsize=8.8, color=SUB,
            ha='left', fontweight='bold')

    # ---- 주 블록 ----
    box(ax, 0.04, 0.40, 0.20, 0.32, 'CARLA 0.9.16',
        '시뮬레이터 서버\nTown07 (저속 도심·농촌)', fill=figstyle.FILL_BLUE,
        fs=9.8, sub_fs=7.6)
    box(ax, 0.425, 0.45, 0.13, 0.21, 'ROS 2\n브리지',
        'AWCL C++', fill=figstyle.FILL_BLUE, fs=9.0, sub_fs=7.6)
    # Autoware + 내부 애드온
    box(ax, 0.595, 0.315, 0.37, 0.40, '', fill=figstyle.FILL_BLUE)
    ax.text(0.78, 0.672, 'Autoware 0.39.0', ha='center', fontsize=10,
            fontweight='bold', color=INK)
    ax.text(0.78, 0.628, '인지·계획·제어 스택', ha='center', fontsize=8.0,
            color=SUB)
    box(ax, 0.612, 0.372, 0.158, 0.20, 'cdr_monitor',
        '감시 모듈\n(건강 점수)', fill=figstyle.FILL_GREEN, fs=8.6, sub_fs=7.4)
    box(ax, 0.792, 0.372, 0.158, 0.20, 'mrm_supervisor',
        '감독자\n(MRM 선택)', fill=figstyle.FILL_GREEN, fs=8.6, sub_fs=7.4)
    ax.text(0.78, 0.336, '제안 애드온 — 진단 그래프로 스택에 연결',
            ha='center', fontsize=7.4, color=SUB)

    # 시나리오 러너·리더보드
    box(ax, 0.425, 0.775, 0.245, 0.115, '시나리오 러너·리더보드',
        '케이스 실행·공식 판정', fill=figstyle.FILL_GRAY, fs=8.8, sub_fs=7.6)

    # Town07 벡터맵 (하단)
    box(ax, 0.04, 0.05, 0.48, 0.15, '자체 제작 Town07 벡터맵 (lanelet2)',
        '갓길(road_shoulder)·주차장(parking_lot) 대피 후보 수동 주석',
        fill=figstyle.FILL_AMBER, fs=9.2, sub_fs=7.8)

    # ---- 폐루프 화살표 ----
    y_up = 0.60    # 센서 데이터 레인 (좌 → 우)
    arrow(ax, (0.24, y_up), (0.425, y_up))
    arrow(ax, (0.555, y_up), (0.595, y_up))
    ax.text(0.348, y_up + 0.035, '센서 데이터', ha='center', fontsize=8.4,
            color=INK)
    ax.text(0.348, y_up + 0.098, '라이다·카메라\nGNSS·IMU', ha='center',
            fontsize=6.8, color=SUB)
    y_dn = 0.47    # 제어 명령 레인 (우 → 좌)
    arrow(ax, (0.595, y_dn), (0.555, y_dn))
    arrow(ax, (0.425, y_dn), (0.24, y_dn))
    ax.text(0.348, y_dn - 0.040, '제어 명령', ha='center', fontsize=8.4,
            color=INK)
    ax.text(0.348, y_dn - 0.078, '조향·가감속', ha='center', fontsize=6.8,
            color=SUB)

    # 시나리오 러너 → CARLA: 제어·평가
    ax.plot([0.425, 0.14], [0.832, 0.832], color=INK,
            lw=figstyle.LW_ARROW, zorder=3)
    arrow(ax, (0.14, 0.832), (0.14, 0.725))
    ax.text(0.152, 0.782, '시나리오\n제어·평가(채점)', ha='left', va='center',
            fontsize=7.4, color=SUB)

    # 벡터맵 연결 (점선)
    ax.plot([0.14, 0.14], [0.203, 0.397], color='#8a92a0', lw=1.0,
            ls=(0, (3, 2)), zorder=1)
    ax.text(0.152, 0.235, 'Town07 지형 정합', fontsize=7.2, color=SUB,
            ha='left')
    ax.plot([0.523, 0.78, 0.78], [0.125, 0.125, 0.312], color='#8a92a0',
            lw=1.0, ls=(0, (3, 2)), zorder=1)
    ax.text(0.652, 0.148, '지도 로드 (경로·대피 후보)', fontsize=7.2,
            color=SUB, ha='center')

    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
