# -*- coding: utf-8 -*-
"""그림 5-2 2패널(lso+cn)판 반영: 캡션 교체 + 본문 반문장 수정 (KO+EN, 멱등)."""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(HERE, '..', 'thesis_build_en')

def rep(s, old, new, tag):
    n = s.count(old)
    assert n == 1, f'{tag}: count={n} for {old[:60]!r}'
    return s.replace(old, new)

CAP_KO_OLD = '그림 5-2. 연속 건강도 궤적 — 상태 전이 입력 채널(실선 perception)의 점수 대역 분리(이중 임계 0.7/0.3 병기). 점선은 MRM 이동 게이트용 obstacle 채널이며, 조건당 대표 단일 런에서 워밍업·종료 stale 아티팩트를 절단했다.'
CAP_KO_NEW = '그림 5-2. 연속 건강도 궤적 — 상태 전이 입력(perception 능력) 점수의 대역 분리: (a) 라이다 희박화(lso), (b) 카메라 화소 노이즈(cn), 이중 임계 0.7/0.3 병기. 조건당 대표 단일 런이며 워밍업·종료 stale 아티팩트는 절단했다. 항법 계열(gn·imn)의 결정 변수는 /monitor/scores가 아닌 감독자 내부 잔차 감지기에서 산출되므로 본 그림의 대상이 아니다.'

p3 = os.path.join(HERE, 'content3.py')
s = io.open(p3, encoding='utf-8').read()
if CAP_KO_NEW not in s:
    s = rep(s, CAP_KO_OLD, CAP_KO_NEW, 'ko-cap')
    s = rep(s, '점선의 obstacle 채널은', 'obstacle 채널은', 'ko-dash')
    s = rep(s, '단, GNSS 계열(gn)의 건강도는', '단, 항법 계열(gn·imn)의 건강도는', 'ko-nav')
    io.open(p3, 'w', encoding='utf-8').write(s)
    print('KO patched')
else:
    print('KO already patched')

CAP_EN_OLD = 'Figure 5-2. Continuous health traces — band separation of the state-transition input channel (solid: perception) against the dual thresholds (0.7/0.3). Dashed lines show the MRM move-gate obstacle channel; one representative run per condition, with warm-up and end-of-run stale artifacts trimmed.'
CAP_EN_NEW = 'Figure 5-2. Continuous health traces — band separation of the state-transition input (perception capability) score: (a) LiDAR soiling (lso), (b) camera pixel noise (cn), with the dual thresholds 0.7/0.3. One representative run per condition; warm-up and end-of-run stale artifacts are trimmed. The navigation family (gn, imn) is out of scope here by design — its decision variables come from residual detectors inside the supervisor, not from /monitor/scores.'

tp = os.path.join(EN, 'translated.json')
tr = json.load(open(tp))
items = tr['ch5a']['items']
done = any(it['kind'] == 'fig' and it['fields'][0] == CAP_EN_NEW for it in items)
if done:
    print('EN already patched')
else:
    hit = [i for i, it in enumerate(items) if it['kind'] == 'fig' and it['fields'][0] == CAP_EN_OLD]
    assert len(hit) == 1, f'EN cap: {len(hit)}'
    items[hit[0]]['fields'][0] = CAP_EN_NEW
    band = [i for i, it in enumerate(items) if it['kind'] == 'p'
            and 'dashed obstacle channel' in it['fields'][0].lower()
            or (it['kind'] == 'p' and 'obstacle channel' in it['fields'][0]
                and 'move gate' in it['fields'][0].lower().replace('-', ' '))]
    assert len(band) >= 1, 'EN band paragraph not found'
    f = items[band[0]]['fields']
    t = f[0]
    for old, new in [('The dashed obstacle channel', 'The obstacle channel'),
                     ('dashed obstacle channel', 'obstacle channel')]:
        if old in t:
            t = t.replace(old, new, 1)
            break
    for old, new in [('the GNSS family (gn)', 'the navigation family (gn, imn)'),
                     ('GNSS family (gn)', 'navigation family (gn, imn)')]:
        if old in t:
            t = t.replace(old, new, 1)
            break
    f[0] = t
    json.dump(tr, open(tp, 'w'), ensure_ascii=False, indent=1)
    print('EN patched')
