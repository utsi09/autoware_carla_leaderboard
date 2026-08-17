# -*- coding: utf-8 -*-
"""그림 4-3 (v17 신규): 보행자 돌발 조우 주입 구조.

구 그림 4-1(8 m 설계도)을 그림 4-3으로 재작성 — 캡션(content2.py fig4_3):
  고장 주입 t(시드 고정) → 감지 t_detect(섀도 공통) → 발사 t_detect+3 s,
  전방 8 m 상대 기하 표준화, 보행자는 12 m 횡단 후 정지.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OUT = '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_encounter_design.png'
INK = figstyle.INK
SUB = '#4a5262'


def tbox(ax, x, y, w, h, title, sub, fill):
    bp = FancyBboxPatch((x, y), w, h,
                        boxstyle='round,pad=0.008,rounding_size=0.010',
                        fc=fill, ec=INK, lw=figstyle.LW_BOX)
    ax.add_patch(bp)
    ax.text(x + w / 2, y + h / 2 + 0.045, title, ha='center', va='center',
            fontsize=9.0, fontweight='bold', color=INK)
    ax.text(x + w / 2, y + h / 2 - 0.052, sub, ha='center', va='center',
            fontsize=7.6, color=SUB)


def main():
    figstyle.apply()
    fig, ax = plt.subplots(figsize=(8.8, 3.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.grid(False)

    # ---- 상단: 시간축 3단계 ----
    ty, th, tw = 0.80, 0.16, 0.24
    tbox(ax, 0.03, ty, tw, th, '고장 주입 t', '케이스 키 유도 시드 고정',
         figstyle.FILL_BLUE)
    tbox(ax, 0.38, ty, tw, th, '감지 t_detect', '섀도 감지기 — 전 팔 공통',
         figstyle.FILL_AMBER)
    tbox(ax, 0.73, ty, tw, th, '발사 t_detect + 3 s', '행동 독립 시간 트리거',
         figstyle.FILL_RED)
    for x0, x1 in [(0.27, 0.38), (0.62, 0.73)]:
        ax.add_patch(FancyArrowPatch((x0, ty + th / 2), (x1, ty + th / 2),
                                     arrowstyle='-|>', mutation_scale=13,
                                     color=INK, lw=figstyle.LW_ARROW))

    # 발사 박스 → 보행자 스폰 지점 (점선 연결, 우측 우회)
    ax.plot([0.94, 0.94], [ty - 0.008, 0.235], color='#8a92a0',
            lw=1.0, ls=(0, (3, 2)), zorder=1)
    ax.add_patch(FancyArrowPatch((0.94, 0.235), (0.645, 0.235),
                                 arrowstyle='-|>', mutation_scale=11,
                                 color='#8a92a0', lw=1.0, ls=(0, (3, 2)),
                                 zorder=2))

    # ---- 도로 밴드 ----
    ry, rh = 0.18, 0.34
    ax.add_patch(plt.Rectangle((0.03, ry), 0.94, rh, fc='#e4e6ea', ec='none',
                               zorder=0))
    ax.plot([0.03, 0.97], [ry + rh / 2] * 2, color='white', lw=2.2,
            ls=(0, (6, 4)), zorder=1)
    ax.text(0.045, ry + rh - 0.045, '주행 차선', ha='left', fontsize=7.6,
            color=SUB)

    # 에고 차량 (좌) — 진행 방향 →
    ex, ey, ew, eh = 0.10, ry + 0.085, 0.16, 0.17
    bp = FancyBboxPatch((ex, ey), ew, eh,
                        boxstyle='round,pad=0.006,rounding_size=0.014',
                        fc=figstyle.FILL_BLUE, ec=INK, lw=figstyle.LW_BOX)
    ax.add_patch(bp)
    ax.text(ex + ew / 2, ey + eh / 2, '에고 v(t)', ha='center', va='center',
            fontsize=8.8, fontweight='bold', color=INK)
    ax.add_patch(FancyArrowPatch((ex + ew + 0.008, ey + eh / 2),
                                 (ex + ew + 0.065, ey + eh / 2),
                                 arrowstyle='-|>', mutation_scale=12,
                                 color=INK, lw=figstyle.LW_ARROW))

    # 보행자 (전방 8 m, 차선 우측 끝) — 횡단 ↑ 후 정지
    px = 0.615
    py = ry + 0.055          # 차선 우측 끝 (+0.5 m)
    ax.add_patch(Circle((px, py), 0.016, fc=figstyle.C_HIGH, ec='none',
                        zorder=4))
    ax.add_patch(FancyArrowPatch((px, py + 0.02), (px, ry + rh + 0.065),
                                 arrowstyle='-|>', mutation_scale=12,
                                 color=figstyle.C_HIGH,
                                 lw=figstyle.LW_ARROW, zorder=3))
    ax.text(px + 0.022, 0.465, '12 m 횡단 후 정지\n(걷기 검증 >1 m/s)',
            ha='left', va='center', fontsize=7.8, color=figstyle.C_HIGH,
            zorder=4)
    ax.text(0.40, ry - 0.065,
            '보행자 스폰 — 주행 차선 우측 끝 +0.5 m (횡 지터 ±0.2 m)',
            ha='center', fontsize=7.8, color=SUB)

    # 8 m 상대 기하 (양측 화살표)
    gy = ry + rh + 0.10
    ax.add_patch(FancyArrowPatch((ex + ew / 2, gy), (px, gy),
                                 arrowstyle='<|-|>', mutation_scale=12,
                                 color=INK, lw=figstyle.LW_ARROW))
    ax.plot([ex + ew / 2] * 2, [ey + eh + 0.012, gy + 0.015], color='#8a92a0',
            lw=0.9, ls=(0, (2, 2)))
    ax.text((ex + ew / 2 + px) / 2, gy + 0.045,
            '전방 8 m — 상대 기하 표준화 (전 팔 동일)', ha='center',
            fontsize=8.6, color=INK)

    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
