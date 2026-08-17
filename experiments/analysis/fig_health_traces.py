# -*- coding: utf-8 -*-
"""그림 5-1 재제작(v6): 실제 결정 변수 기준의 연속 건강도 궤적.

v6 4차 리뷰 반영:
  - 실선 = capability/perception — 감독자 상태 전이(0.7/0.3)에 실제 입력되는
    감시 채널 (health = min(perception, cap_loc); 라이다 열화에서 cap_loc=1).
  - 점선(보조) = capability/obstacle — MRM 이동 게이트 전용 채널.
  - 동일 scoretrace CSV에서 두 채널을 같은 규칙으로 파싱, 워밍업(25 s)·
    종말 아티팩트 절단 유지.
  - nf perception은 워밍업 후 상단 임계 0.7을 하회하지 않는다(실측 최저
    0.71) — 무고장 45케이스 오발동 0건과 정합.

v5 오딧 정정(유지):
  (a) 세그먼트 종료 2 s 절단 + 양옆 정상(>0.3) 고립 stale-0 샘플 제거 —
      0으로의 수직 낙하는 기록 아티팩트임이 원로그 재검증으로 확인됨.

데이터: experiments/results/scoretrace_{nf_mid,lso_mid,lso_high}.csv
파싱: 행에서 채널명('capability/perception' 등) 다음의 'score' 키 값.
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

RES = '/home/taewook/autoware_carla_leaderboard/experiments/results'
OUT = os.path.join(RES, 'fig_health_traces.png')

CH_MAIN = 'capability/perception'   # 실선: 상태 전이 입력 채널
CH_AUX = 'capability/obstacle'      # 점선: MRM 이동 게이트 채널

TAIL_CUT_S = 2.0          # 세그먼트 종료 전 절단폭 (stale 종료 샘플 제거)
STALE_EPS = 0.05          # stale 0 판정
NEIGHBOR_OK = 0.3         # 고립 0 샘플의 양옆 정상 판정
DRIVE_START_S = 25.0      # 기록 시작 → 주행 개시(엔게이지)까지의 워밍업 구간


def parse(path, channel):
    """(t, <channel> score) 시퀀스."""
    out = []
    for r in csv.reader(open(path)):
        try:
            t = float(r[0]) + float(r[1]) * 1e-9
        except (ValueError, IndexError):
            continue
        v = None
        for i, c in enumerate(r):
            if c == channel:
                for j in range(i + 1, min(i + 6, len(r))):
                    if r[j] == 'score':
                        v = float(r[j + 1])
                        break
                break
        if v is not None:
            out.append((t, v))
    return out


def clean(data):
    """세그먼트 분할(시간 역행 지점) → 최장 세그먼트 → 아티팩트 절단."""
    segs, cur = [], [data[0]]
    for a, b in zip(data, data[1:]):
        if b[0] < a[0] - 0.5:
            segs.append(cur)
            cur = []
        cur.append(b)
    segs.append(cur)
    seg = max(segs, key=len)
    # 1) 세그먼트 종료부 절단
    t_end = seg[-1][0]
    seg = [(t, v) for t, v in seg if t <= t_end - TAIL_CUT_S]
    # 2) 고립 stale-0 샘플 제거 (양옆이 정상값이면 기록 아티팩트)
    keep = []
    for i, (t, v) in enumerate(seg):
        if (v < STALE_EPS and 0 < i < len(seg) - 1
                and seg[i - 1][1] > NEIGHBOR_OK and seg[i + 1][1] > NEIGHBOR_OK):
            print('dropped stale-0 artifact at t=%.2f' % t)
            continue
        keep.append((t, v))
    return keep


def series_pts(fname, channel):
    d = clean(parse(os.path.join(RES, fname), channel))
    t0 = d[0][0] + DRIVE_START_S    # 주행 개시를 0으로 정렬(워밍업 절단)
    pts = [(t - t0, v) for t, v in d if t >= t0]
    return [p[0] for p in pts], [p[1] for p in pts]


def main():
    figstyle.apply()
    series = [
        ('scoretrace_nf_mid.csv', '무고장 (nf)', figstyle.C_NF),
        ('scoretrace_lso_mid.csv', '라이다 희박화 중강도 (lso-mid)', figstyle.C_MID),
        ('scoretrace_lso_high.csv', '라이다 희박화 고강도 (lso-high)', figstyle.C_HIGH),
    ]
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    handles = []
    label_dy = {'nf': 8, 'lso-mid': -8, 'lso-high': 0}   # 직접 라벨 충돌 회피
    for fname, label, color in reversed(series):         # 건강 구간은 nf가 위로
        # 점선(보조): obstacle — MRM 이동 게이트 채널
        xa, ya = series_pts(fname, CH_AUX)
        ax.plot(xa, ya, color=color, lw=figstyle.LW_LINE * 0.75,
                ls=(0, (2.5, 2.5)), alpha=0.45, solid_joinstyle='round')
        # 실선(주): perception — 상태 전이 입력 채널
        xs, ys = series_pts(fname, CH_MAIN)
        h, = ax.plot(xs, ys, color=color, lw=figstyle.LW_LINE, ls='-',
                     label=label, solid_joinstyle='round')
        handles.append(h)
        short = label.split(' (')[1].rstrip(')')
        ax.annotate(short, (xs[-1], ys[-1]),
                    xytext=(5, label_dy.get(short, 0)),
                    textcoords='offset points',
                    color=color, fontsize=8.5, va='center')
    handles.reverse()

    ax.axhline(0.7, color='#7a8291', lw=1.0, ls=(0, (6, 3)))
    ax.axhline(0.3, color='#7a8291', lw=1.0, ls=(0, (1, 2.5)))
    ax.text(0.995, 0.715, '상단 임계 0.7', transform=ax.get_yaxis_transform(),
            ha='right', va='bottom', fontsize=8.5, color='#5a6270')
    ax.text(0.995, 0.315, '하단 임계 0.3 (위임 경계)', transform=ax.get_yaxis_transform(),
            ha='right', va='bottom', fontsize=8.5, color='#5a6270')

    ax.axvline(25.0, color='#9aa1ac', lw=0.9, ls=(0, (2, 2)))
    ax.text(25.0, 0.03, ' 고장 주입 (25 s)', fontsize=8.5, color='#5a6270',
            ha='left', va='bottom')
    ax.set_xlabel('주행 개시 후 시간 [s]')
    ax.set_ylabel('능력 점수')
    ax.set_ylim(0.0, 1.06)
    ax.set_xlim(left=0)
    style_handles = [
        Line2D([], [], color='#4a5160', lw=figstyle.LW_LINE, ls='-',
               label='perception (상태 전이 입력)'),
        Line2D([], [], color='#4a5160', lw=figstyle.LW_LINE * 0.75,
               ls=(0, (2.5, 2.5)), alpha=0.55,
               label='obstacle (이동 게이트, 보조)'),
    ]
    leg1 = ax.legend(handles=handles, loc='lower right', frameon=False,
                     fontsize=9)
    ax.add_artist(leg1)
    ax.legend(handles=style_handles, loc='lower left', frameon=False,
              fontsize=8.5, bbox_to_anchor=(0.0, 0.10))
    ax.set_title('연속 건강도 궤적 — 상태 전이 입력 채널의 점수 대역 분리',
                 fontsize=11)
    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
