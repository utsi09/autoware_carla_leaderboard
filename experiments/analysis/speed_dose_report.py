# -*- coding: utf-8 -*-
"""speed-dose 집계 (사전등록 doc/speed_dose_plan_0827.md).

판정: 러너 outcome 불신(라벨 버그 기지) — encounter_metrics.csv의 태그별
'마지막 시도' 행이 진실원 (재시도는 비채택 후에만 발생하므로 마지막 행 = 채택 시도).
충돌 = CONTACT-*, 회피 = CLEAR(+min_gap 존재), NO-ENCOUNTER = 무효.

1차 종결점: 8 m에서 4.2 vs 3.0 paired exact McNemar (n=10 시드, 사전 지정).
2차: 속도x거리 경계표 + Wilson 95% CI. 용법: python3 speed_dose_report.py
"""
import csv, math, os
from collections import OrderedDict

R = '/home/taewook/autoware_carla_leaderboard/experiments/results'
CAPS = ['4.2', '3.6', '3.0']
DISTS = ['8', '7', '9', '6']

def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.959964, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def mcnemar_exact(b, c):
    """불일치쌍 b, c의 양측 exact 이항 p."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    cum = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * cum)

def load():
    # 태그별 마지막 원장 행
    led = OrderedDict()
    with open(f'{R}/encounter_metrics.csv') as f:
        for row in csv.reader(f):
            if len(row) >= 4 and row[1].startswith('sd-'):
                led[row[1]] = row
    # progress: 채택 여부·첫 틱 속도
    prog = {}
    with open(f'{R}/speed_dose_progress.csv') as f:
        for r in csv.DictReader(f):
            prog[r['tag']] = r      # 마지막 시도 행이 남음
    out = {}
    for tag, row in led.items():
        _, _, mg, contact = row[0], row[1], row[2], row[3]
        p = tag.split('-')          # sd,S12,c42,d8
        seed, cap, dist = p[1], p[2][1:], p[3][1:]
        cap = f'{cap[0]}.{cap[1]}'
        if seed.startswith('D'):
            continue                # 개발 시드 제외 (사전등록)
        pr = prog.get(tag, {})
        adopted = pr.get('adopted') == '1'
        if contact == 'NO-ENCOUNTER' or not adopted:
            verdict = 'INVALID'
        elif contact.startswith('CONTACT'):
            verdict = 'COLLIDE'
        else:
            verdict = 'AVOID'
        out[(seed, cap, dist)] = dict(verdict=verdict, min_gap=mg,
                                      first_v=pr.get('first_v', ''),
                                      contact=contact)
    return out

def main():
    d = load()
    seeds = sorted({k[0] for k in d})
    print(f'세포 채움: {len(d)}/120  시드 {len(seeds)}종')
    # 경계표
    print('\n=== 속도 x 거리 충돌표 (충돌/유효 [Wilson95]) ===')
    hdr = '        ' + ''.join(f'{dd:>16}m' for dd in sorted(DISTS))
    print(hdr)
    for cap in CAPS:
        cells = []
        for dist in sorted(DISTS):
            vs = [v['verdict'] for k, v in d.items()
                  if k[1] == cap and k[2] == dist and v['verdict'] != 'INVALID']
            n, k = len(vs), sum(1 for v in vs if v == 'COLLIDE')
            lo, hi = wilson(k, n)
            cells.append(f'{k}/{n} [{lo:.2f},{hi:.2f}]' if n else '-')
        print(f'{cap:>6}  ' + ''.join(f'{c:>17}' for c in cells))
    # 1차 종결점
    print('\n=== 1차 종결점: 8m 4.2 vs 3.0 paired ===')
    b = c = n11 = n00 = 0
    for s in seeds:
        v1 = d.get((s, '4.2', '8'), {}).get('verdict')
        v3 = d.get((s, '3.0', '8'), {}).get('verdict')
        if v1 in (None, 'INVALID') or v3 in (None, 'INVALID'):
            continue
        if v1 == 'COLLIDE' and v3 == 'AVOID':
            b += 1
        elif v1 == 'AVOID' and v3 == 'COLLIDE':
            c += 1
        elif v1 == 'COLLIDE':
            n11 += 1
        else:
            n00 += 1
        print(f'  {s}: 4.2={v1:8s} 3.0={v3}')
    print(f'불일치 4.2충돌/3.0회피 b={b}, 4.2회피/3.0충돌 c={c}, '
          f'둘다충돌 {n11}, 둘다회피 {n00}')
    print(f'exact McNemar 양측 p = {mcnemar_exact(b, c):.4g}')
    # 조작 점검
    print('\n=== 조작 점검: 첫 틱 속도 분포 ===')
    for cap in CAPS:
        vs = [float(v['first_v']) for k, v in d.items()
              if k[1] == cap and v['first_v'] not in ('', None)]
        if vs:
            vs.sort()
            print(f'  cap {cap}: n={len(vs)} min={vs[0]:.2f} '
                  f'med={vs[len(vs)//2]:.2f} max={vs[-1]:.2f}')
    inv = [(k, v['contact']) for k, v in d.items() if v['verdict'] == 'INVALID']
    if inv:
        print(f'\n무효(재실행 소진 포함) {len(inv)}건: {inv}')

if __name__ == '__main__':
    main()
