# -*- coding: utf-8 -*-
"""그림 5-3 재제작(v17): 고장 유형별 고장 상태 주행 노출 — 3팔 묶음 막대.

데이터 근거 (exposure.py 재산출, 2026-08-17):
  - 무감시 순정(mrm-off 프로브, results_0815_08*/09*.csv, fault×severity 평균의 유형 평균):
      cf 238 / cn 240 / gn 251 / lso 264 / lcl 275 / imn 71 m  — 본문 수치와 일치.
  - 제안 ours (merged_final.csv deg_dist_m, method=ours 평균):
      cf 33.5 / cn 32.4 / gn 57.6 / lcl 11.2 / imn 12.4 m.
      lso는 lso-mid의 의도적 무개입(감내) 255 m — 막대에 명시 주석.
  - baseline (감지+차로 내 정지): cf 16.9 / cn 17.6 / gn 9.4 / lcl 8.1 / imn 8.6 m.
      lso의 baseline 막대는 표시하지 않는다(동일 감지 공유 — lso-mid는
      설계상 미검출·계속 주행이므로 정지 팔이 성립하지 않음, 캡션에 명시).

x축 라벨은 논문 용어(표 4-2) 그대로.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt

OUT = '/home/taewook/autoware_carla_leaderboard/experiments/results/fig_exposure.png'

C_STOCK = '#6e7480'          # 무감시 순정: 중립 회색(기준선 팔)
C_OURS = figstyle.C_NF       # 제안: 청
C_BASE = figstyle.C_MID      # 정지: 주황

faults = ['카메라 사망\n(cf)', '카메라 노이즈\n(cn)', 'GNSS 위치 노이즈\n(gn)',
          '라이다 희박화\n(lso)', '라이다 클러터\n(lcl)', 'IMU 노이즈\n(imn)']
stock = [238, 240, 251, 264, 275, 71]
ours = [33.5, 32.4, 57.6, 255.3, 11.2, 12.4]     # lso = lso-mid 의도적 계속 주행
base = [16.9, 17.6, 9.4, None, 8.1, 8.6]         # lso: 정지 팔 성립하지 않음


def main():
    figstyle.apply()
    fig, ax = plt.subplots(figsize=(7.8, 3.9))
    w = 0.27
    x = range(len(faults))

    def bars(offs, vals, color, label):
        xs = [i + offs for i, v in zip(x, vals) if v is not None]
        vs = [v for v in vals if v is not None]
        b = ax.bar(xs, vs, w, color=color, label=label, zorder=3)
        for xi, vi in zip(xs, vs):
            ax.text(xi, vi + 4, ('%d' % round(vi)), ha='center', va='bottom',
                    fontsize=7.8, color=figstyle.INK)
        return b

    bars(-w, stock, C_STOCK, '무감시 순정 (mrm-off)')
    bars(0.0, ours, C_OURS, '제안 (감지+대피)')
    bars(w, base, C_BASE, '감지+차로 내 정지 (baseline)')

    # lso ours 막대: 의도적 무개입(감내) 주석 — 막대 안 세로 표기
    ax.text(3.0, 133, '감내 — 무개입 (TOLERATED, no intervention)',
            rotation=90, ha='center', va='center',
            fontsize=7.6, color='white', zorder=4)

    ax.set_xticks(list(x))
    ax.set_xticklabels(faults, fontsize=8.6)
    ax.set_ylabel('고장 상태 주행거리 [m]')
    ax.set_ylim(0, 340)
    ax.grid(axis='x', visible=False)
    ax.legend(fontsize=8.6, frameon=False, loc='upper center', ncol=3,
              bbox_to_anchor=(0.5, 1.03), columnspacing=1.2, handlelength=1.4)
    ax.set_title('고장 유형별 고장 상태 주행 노출 (평균)', fontsize=11, pad=16)
    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
