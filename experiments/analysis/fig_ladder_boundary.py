# -*- coding: utf-8 -*-
"""그림 5-4 재제작(v17): (a) 거리 사다리 충돌률 + (b) 8 m 조우 3조건.

v17 정정:
  - (a) lso-high(라이다 완전 열화) 순정의 14·11 m는 "회피"가 아니라 조우 전
    도로 한복판 동결(FREEZE, 빈 포인트클라우드로 정지·도로 점거)이다.
    이전 판은 이 두 점을 충돌률 0으로 무고장 곡선 위에 겹쳐 그려 안전 회피로
    오독되었다 → 선에서 분리해 X 마커 + «동결(FREEZE)» 주석으로 표기하고,
    lso-high 선은 8 m 이하(충돌 구간)만 그린다.
  - (b) 구제목 "gyro fault"는 본문(제5장 4절)과 불일치 — 실제 고장은
    gn-mid(GNSS 위치 노이즈)이다. 제목·라벨을 본문 용어로 정정.

데이터 (표 5-3, 제5장 4절, 원장 판정):
  무고장 순정 4.2 m/s: 14 m 0/4, 11 m 0/4, 8 m 4/4, 6 m 4/4, 5 m 4/4 충돌.
  lso-high 순정: 14·11 m 동결(n=2/거리, 계 4/4), 8·6·5 m 전량 충돌(6/6).
  (b) gn-mid 8 m 돌발: 제안 순항 3.0 m/s 회피 8/8, 제안 감속 과도구간 회피 0/2,
      순정 4.2 m/s 회피 0/10.

출력: 논문 fig 엔트리 경로 유지 → experiments/results/fig_final_campaign.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt

OUT = '/home/taewook/autoware_carla_leaderboard/experiments/results/fig_final_campaign.png'

C_NF = figstyle.C_NF        # 무고장 순정: 청
C_LSO = figstyle.C_HIGH     # lso-high: 암적


def main():
    figstyle.apply()
    fig, ax = plt.subplots(1, 2, figsize=(10.6, 4.0))

    # ---------- (a) 거리 사다리 ----------
    a = ax[0]
    a.axvspan(8, 11, color='#e8eaee', zorder=0)
    a.text(9.5, 0.52, '정지거리 경계\n8~11 m', ha='center', va='center',
           fontsize=8.4, color='#5a6270')

    # 무고장 순정: 전 구간 곡선
    nf_d = [14, 11, 8, 6, 5]
    nf_r = [0, 0, 1, 1, 1]
    a.plot(nf_d, nf_r, '-o', color=C_NF, lw=figstyle.LW_LINE, ms=7,
           label='무고장 순정 (n=4/거리)', zorder=3)

    # lso-high: 충돌 구간(8 m 이하)만 선으로, 14·11 m는 동결(FREEZE) 마커
    lso_d = [8, 6, 5]
    lso_r = [1, 1, 1]
    a.plot(lso_d, lso_r, '--s', color=C_LSO, lw=figstyle.LW_LINE, ms=6.5,
           mfc='white', label='실명(lso-high) 순정 (n=2/거리)', zorder=4)
    frz_y = -0.085             # 충돌률 축 밖: "율(rate)이 아님"을 시각적으로 분리
    frz_d = [14, 11]
    a.scatter(frz_d, [frz_y, frz_y], marker='x', s=90, color=C_LSO, lw=2.2,
              label='동결(FREEZE) — 조우 전 도로 점거', zorder=5, clip_on=False)
    a.annotate('동결(FREEZE): 조우 전 도로 한복판 정지\n(회피 아님 — 빈 포인트클라우드로 도로 점거)',
               xy=(11.35, frz_y - 0.005), xytext=(12.6, 0.20), ha='center',
               fontsize=8.2, color=C_LSO,
               arrowprops=dict(arrowstyle='-', color=C_LSO, lw=0.9,
                               shrinkB=8))

    a.set_xlim(15, 4)          # 먼 거리 → 가까운 거리
    a.set_ylim(-0.14, 1.10)
    a.spines['bottom'].set_position(('data', -0.14))
    a.set_xticks([14, 12, 10, 8, 6, 5])
    a.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    a.set_xlabel('보행자 스폰 거리 [m]')
    a.set_ylabel('충돌률')
    a.set_title('(a) 거리 사다리 @4.2 m/s (원장 판정)', fontsize=10.5)
    a.legend(fontsize=7.8, frameon=False, loc='center left',
             bbox_to_anchor=(0.02, 0.80))

    # ---------- (b) 동일 8 m 돌발, gn-mid 3조건 ----------
    b = ax[1]
    conds = ['제안 저속 MRM\n정착 순항 3.0 m/s\n(n=8)',
             '제안 감속\n과도구간\n(n=2)',
             '순정 4.2 m/s\n유지\n(n=10)']
    avoided = [8, 0, 0]
    collided = [0, 2, 10]
    xs = range(3)
    b.bar(xs, avoided, 0.5, color=C_NF, label='회피', zorder=3)
    b.bar(xs, collided, 0.5, bottom=avoided, color=C_LSO, label='충돌', zorder=3)
    for i, (av, co) in enumerate(zip(avoided, collided)):
        b.text(i, av + co + 0.25, '회피 %d/%d' % (av, av + co),
               ha='center', va='bottom', fontsize=9, color=figstyle.INK)
    b.set_xticks(list(xs))
    b.set_xticklabels(conds, fontsize=8.4)
    b.set_ylabel('조우 횟수')
    b.set_ylim(0, 11.6)
    b.grid(axis='x', visible=False)
    b.set_title('(b) 동일 8 m 돌발 — gn-mid(GNSS 위치 노이즈)', fontsize=10.5)
    b.legend(fontsize=8.4, frameon=False, loc='upper left')

    fig.tight_layout()
    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
