# -*- coding: utf-8 -*-
"""그림 5-1 재제작: 연속 건강도(capability/obstacle) 궤적 — 대역 분리.

v5 오딧 정정:
  (a) 케이스 종료/기록 아티팩트 절단 — 각 연속 세그먼트의 마지막 2초를 절단하고,
      양옆이 정상값(>0.3)인 고립 stale-0 한 샘플(종료 아티팩트가 기록 스트림에
      끼어든 것, nf t=48.7s 등)을 제거한다. 0으로의 수직 낙하는 데이터가 아니라
      기록 아티팩트임이 원로그 재검증으로 확인되었다.
  (b) 캡션 정정은 본문(content3.py)에서: nf의 0.66~0.70 딥은 obstacle 채널의
      정상 주행 요동(발동 채널 아님)이다.

데이터: experiments/results/scoretrace_{nf_mid,lso_mid,lso_high}.csv
파싱: 행에서 'capability/obstacle' 다음에 나오는 'score' 키의 값.
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
import matplotlib.pyplot as plt

RES = '/home/taewook/autoware_carla_leaderboard/experiments/results'
OUT = os.path.join(RES, 'fig_health_traces.png')

TAIL_CUT_S = 2.0          # 세그먼트 종료 전 절단폭 (stale 종료 샘플 제거)
STALE_EPS = 0.05          # stale 0 판정
NEIGHBOR_OK = 0.3         # 고립 0 샘플의 양옆 정상 판정
DRIVE_START_S = 25.0      # 기록 시작 → 주행 개시(엔게이지)까지의 워밍업 구간


def parse(path):
    """(t, capability/obstacle score) 시퀀스."""
    out = []
    for r in csv.reader(open(path)):
        try:
            t = float(r[0]) + float(r[1]) * 1e-9
        except (ValueError, IndexError):
            continue
        v = None
        for i, c in enumerate(r):
            if c == 'capability/obstacle':
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


def main():
    figstyle.apply()
    series = [
        ('scoretrace_nf_mid.csv', '무고장 (nf)', figstyle.C_NF, '-'),
        ('scoretrace_lso_mid.csv', '라이다 희박화 중강도 (lso-mid)', figstyle.C_MID, '-'),
        ('scoretrace_lso_high.csv', '라이다 희박화 고강도 (lso-high)', figstyle.C_HIGH, '-'),
    ]
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    handles = []
    label_dy = {'nf': 8, 'lso-mid': -8, 'lso-high': 0}   # 직접 라벨 충돌 회피
    for fname, label, color, ls in reversed(series):     # 건강 구간은 nf가 위로
        d = clean(parse(os.path.join(RES, fname)))
        t0 = d[0][0] + DRIVE_START_S    # 주행 개시를 0으로 정렬(워밍업 절단)
        pts = [(t - t0, v) for t, v in d if t >= t0]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        h, = ax.plot(xs, ys, color=color, lw=figstyle.LW_LINE, ls=ls,
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
    ax.set_ylabel('capability/obstacle 점수')
    ax.set_ylim(0.0, 1.06)
    ax.set_xlim(left=0)
    ax.legend(handles=handles, loc='lower right', frameon=False, fontsize=9)
    ax.set_title('연속 건강도 궤적 — 고장 강도에 따른 점수 대역 분리', fontsize=11)
    fig.savefig(OUT)
    print('saved', OUT)


if __name__ == '__main__':
    main()
