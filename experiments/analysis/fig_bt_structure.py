# -*- coding: utf-8 -*-
"""그림 3-2 신규: cdr_monitor 행동트리 구조도 (정식 BT 표기).

소스 근거:
  - fs_ws/src/cdr_monitor/behavior_tree/monitor.xml (Sequence/Parallel 구성)
  - fs_ws/src/cdr_monitor/include/cdr_monitor/publish_scores.hpp (capability 합성)
  - 센서 구성: config/sensors_awcl.yaml (LIDAR_front/rear, CAMERA_front, IMU, GNSS)

표기: Sequence(→), Parallel(⇉), 리프(Action)는 모서리 둥근 사각.
흑백 인쇄 대비: 채도 낮은 면색 + 명도 차 + 실선 계층.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_bt_structure.png'

INK = figstyle.INK


def box(ax, x, y, w, h, title, sub=None, kind='leaf', fs=8.6, sub_fs=7.6):
    """kind: 'seq'(→), 'par'(⇉), 'leaf', 'note'"""
    fill = {'seq': '#dde7f2', 'par': '#e9e2f0', 'leaf': 'white',
            'note': '#f6f1e0'}[kind]
    bp = FancyBboxPatch((x, y), w, h,
                        boxstyle='round,pad=0.012,rounding_size=0.012',
                        fc=fill, ec=INK, lw=figstyle.LW_BOX,
                        mutation_aspect=1.0)
    ax.add_patch(bp)
    if kind == 'seq':
        ax.text(x + 0.010, y + h - 0.010, '→', ha='left', va='top',
                fontsize=fs + 2, color=INK, fontweight='bold')
    elif kind == 'par':   # ⇉ 는 나눔명조에 없어 → 두 개를 겹쳐 그린다
        ax.text(x + 0.010, y + h - 0.004, '→', ha='left', va='top',
                fontsize=fs, color=INK, fontweight='bold')
        ax.text(x + 0.010, y + h - 0.022, '→', ha='left', va='top',
                fontsize=fs, color=INK, fontweight='bold')
    cy = y + h / 2 + (0.014 if sub else 0)
    tx = x + w / 2 + (0.012 if kind in ('seq', 'par') else 0)
    ax.text(tx, cy, title, ha='center', va='center',
            fontsize=fs, color=INK, fontweight='bold' if kind != 'leaf' else 'normal')
    if sub:
        ax.text(x + w / 2, cy - 0.036, sub, ha='center', va='center',
                fontsize=sub_fs, color='#4a5262')
    return (x + w / 2, y + h, x + w / 2, y, x, y + h / 2, x + w, y + h / 2)


def edge(ax, p_from, p_to):
    """부모 하단 → 자식 상단 직교 연결선."""
    x0, y0 = p_from
    x1, y1 = p_to
    ym = (y0 + y1) / 2
    ax.plot([x0, x0, x1, x1], [y0, ym, ym, y1], color=INK,
            lw=figstyle.LW_ARROW * 0.85, solid_joinstyle='miter', zorder=1)


def main():
    figstyle.apply()
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.grid(False)

    # ---- 계층 y 좌표 ----
    yR = 0.90   # 루트
    y1 = 0.72   # 1단계 (5개 자식)
    y2 = 0.50   # 2단계 (센서 그룹)
    y3 = 0.30   # 3단계 (센서 리프)
    h = 0.085

    # 루트 Sequence
    r = box(ax, 0.36, yR, 0.28, h, 'MainLoop', '10 Hz tick', kind='seq')
    root_bot = (0.36 + 0.14, yR)

    # 1단계 자식 (좌→우 실행 순서)
    w1 = 0.165
    xs1 = [0.015, 0.195, 0.375, 0.555, 0.80]
    c1 = box(ax, xs1[0], y1, w1, h, 'Subscribers', '속도·헤딩·최근접 장애물',
             kind='par')
    c2 = box(ax, xs1[1], y1, w1, h, 'UpdateSystemState', '주행 상태 갱신', kind='leaf')
    c3 = box(ax, xs1[2], y1, w1, h, 'CalculateFtti',
             'τ_detect 산출 (식 3-6)', kind='leaf')
    c4 = box(ax, xs1[3], y1, w1, h, 'SensorChecks', '센서별 병렬 점검', kind='par')
    c5 = box(ax, xs1[4], y1, 0.185, h, 'PublishScores',
             '섹터·능력 합성 후 발행', kind='leaf')
    for c in (c1, c2, c3, c4, c5):
        edge(ax, root_bot, (c[0], c[1]))

    # 실행 순서 표기
    ax.annotate('', xy=(0.79, y1 - 0.035), xytext=(0.03, y1 - 0.035),
                arrowprops=dict(arrowstyle='-|>', color='#8a92a0', lw=1.0))
    ax.text(0.41, y1 - 0.055, '틱마다 좌 → 우 순차 실행 (Sequence)',
            ha='center', fontsize=7.6, color='#5a6270')

    # 2단계: SensorChecks의 자식
    par_bot = (c4[0], c4[1] - h)
    w2 = 0.155
    g1 = box(ax, 0.13, y2, w2, h, 'LidarChecks', 'Parallel', kind='par')
    g2 = box(ax, 0.315, y2, w2, h, 'CameraChecks', 'Parallel', kind='par')
    g3 = box(ax, 0.50, y2, w2, h, 'ImuChecker', '바이어스·노이즈', kind='leaf')
    g4 = box(ax, 0.685, y2, w2, h, 'GpsChecker', '잔차·점프·침묵', kind='leaf')
    for g in (g1, g2, g3, g4):
        edge(ax, par_bot, (g[0], g[1]))

    # 3단계: 센서 리프 (신선도×품질)
    w3 = 0.135
    l1 = box(ax, 0.055, y3, w3, h, 'LIDAR_front', '신선도×품질·CUSUM',
             kind='leaf', fs=8.0)
    l2 = box(ax, 0.21, y3, w3, h, 'LIDAR_rear', '신선도×품질·CUSUM',
             kind='leaf', fs=8.0)
    l3 = box(ax, 0.375, y3, w3, h, 'CAMERA_front', '신선도×품질·화소차분',
             kind='leaf', fs=8.0)
    edge(ax, (g1[0], g1[1] - h), (l1[0], l1[1]))
    edge(ax, (g1[0], g1[1] - h), (l2[0], l2[1]))
    edge(ax, (g2[0], g2[1] - h), (l3[0], l3[1]))

    # ---- PublishScores 내부 합성 흐름 (주석 패널) ----
    px, py, pw, ph = 0.575, 0.045, 0.41, 0.195
    bp = FancyBboxPatch((px, py), pw, ph,
                        boxstyle='round,pad=0.012,rounding_size=0.012',
                        fc='#f6f1e0', ec=INK, lw=figstyle.LW_BOX)
    ax.add_patch(bp)
    ax.text(px + pw / 2, py + ph - 0.026, 'PublishScores: 3계층 합성 (식 3-3, 3-4)',
            ha='center', fontsize=8.4, fontweight='bold', color=INK)
    lines = [
        '① 센서 점수  $s_i$ = 신선도 × 품질',
        '② 8방향 섹터  $\\mathrm{sector}_k = 1 - \\Pi(1 - s_i)$   (F, FL, …, B)',
        '③ 능력  obstacle = $\\Sigma\\, w_k \\cdot \\mathrm{sector}_k$,'
        '  perception = 0.6·obs+0.4·tl',
        '발행: /monitor/scores (감독자) · /diagnostics (진단 그래프)',
    ]
    for i, s in enumerate(lines):
        ax.text(px + 0.018, py + ph - 0.06 - i * 0.036, s, ha='left',
                fontsize=7.7, color='#3a4252')
    # PublishScores 리프에서 주석 패널로 연결
    ax.plot([c5[0], c5[0], px + pw / 2, px + pw / 2],
            [y1, y1 - 0.06, py + ph + 0.05, py + ph],
            color='#8a92a0', lw=1.0, ls=(0, (3, 2)))

    # ---- 표기 범례 ----
    lx, ly = 0.015, 0.055
    ax.text(lx, ly + 0.12, '표기', fontsize=8.4, fontweight='bold', color=INK)
    for i, (kind, desc) in enumerate([
            ('seq', 'Sequence(→) — 자식을 순서대로 실행'),
            ('par', 'Parallel(→→) — 자식을 병렬 실행'),
            ('leaf', '리프(Action) — 감시·산출 노드')]):
        yy = ly + 0.075 - i * 0.042
        bp = FancyBboxPatch((lx, yy), 0.030, 0.030,
                            boxstyle='round,pad=0.006,rounding_size=0.008',
                            fc={'seq': '#dde7f2', 'par': '#e9e2f0',
                                'leaf': 'white'}[kind],
                            ec=INK, lw=1.0)
        ax.add_patch(bp)
        if kind == 'seq':
            ax.text(lx + 0.015, yy + 0.015, '→', ha='center', va='center',
                    fontsize=9, fontweight='bold', color=INK)
        elif kind == 'par':
            ax.text(lx + 0.015, yy + 0.022, '→', ha='center', va='center',
                    fontsize=6.5, fontweight='bold', color=INK)
            ax.text(lx + 0.015, yy + 0.008, '→', ha='center', va='center',
                    fontsize=6.5, fontweight='bold', color=INK)
        ax.text(lx + 0.042, yy + 0.015, desc, ha='left', va='center',
                fontsize=7.7, color='#3a4252')

    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
