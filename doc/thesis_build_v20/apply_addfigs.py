# -*- coding: utf-8 -*-
"""v20b: 후보 그림 3장 삽입 (KO content*.py + EN translated.json 동시 패치, 멱등).
② 조우 프로토콜 -> 그림 4-3 / ③ 건강도 궤적 -> 그림 5-2 (정지거리 5-3, KM 5-4로 이동)
① 절제 n=20+2체제 -> 그림 5-5. 전 치환 assert count==1."""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(HERE, '..', 'thesis_build_en')
PB = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs'

def rep(s, old, new, tag):
    n = s.count(old)
    assert n == 1, f'{tag}: count={n} for {old[:60]!r}'
    return s.replace(old, new)

# ================= KO =================
p2 = os.path.join(HERE, 'content2.py')
s = io.open(p2, encoding='utf-8').read()
if 'fig4_3tl' in s:
    print('KO content2 already patched — skip')
else:
    s = rep(s, '보행자를 발사한다.', '보행자를 발사한다(그림 4-3).', 'ko-c2-ref')
    s = rep(s, "케이스별 CSV로 남긴다.'),\n",
            "케이스별 CSV로 남긴다.'),\n"
            "('fig', '그림 4-3. 보행자 돌발 조우 주입 프로토콜. 고장 주입(시드 고정 파형) → 섀도 감지 t_detect(전 팔 공통) → t_detect+3 s 행동 독립 발사가 전방 8 m·차선 우측 끝 +0.5 m(횡 지터 ±0.2 m)의 표준화 상대 기하로 보행자(12 m 횡단 후 정지)를 스폰한다.', 'fig4_3tl', '"
            + PB + "/fig11_encounter.png', None, 14.0),\n", 'ko-c2-fig')
    io.open(p2, 'w', encoding='utf-8').write(s)
    print('KO content2 patched')

p3 = os.path.join(HERE, 'content3.py')
s = io.open(p3, encoding='utf-8').read()
if 'fig5_2ht' in s:
    print('KO content3 already patched — skip')
else:
    s = rep(s, "('fig', '그림 5-3. 무충돌 대피 케이스의", "('fig', '그림 5-4. 무충돌 대피 케이스의", 'ko-km')
    s = rep(s, "('fig', '그림 5-2. 정지거리 모델", "('fig', '그림 5-3. 정지거리 모델", 'ko-sd')
    s = rep(s, '(표 5-3, 그림 5-2)', '(표 5-3, 그림 5-3)', 'ko-sd-ref')
    s = rep(s, '표의 이진 검출률 이면에는 연속 건강도 신호가 있다.',
            '표의 이진 검출률 이면에는 연속 건강도 신호가 있다(그림 5-2).', 'ko-ht-ref')
    s = rep(s, "라이다 열화 채널 기준이다.'),\n",
            "라이다 열화 채널 기준이다.'),\n"
            "('fig', '그림 5-2. 연속 건강도 궤적 — 상태 전이 입력 채널(실선 perception)의 점수 대역 분리(이중 임계 0.7/0.3 병기). 점선은 MRM 이동 게이트용 obstacle 채널이며, 조건당 대표 단일 런에서 워밍업·종료 stale 아티팩트를 절단했다.', 'fig5_2ht', '"
            + PB + "/fig12_health.png', None, 14.5),\n", 'ko-ht-fig')
    s = rep(s, '대비가 선명하다:', '대비가 선명하다(그림 5-5):', 'ko-ab-ref')
    s = rep(s, "발사에서는 0/8 무충돌이었다.'),\n",
            "발사에서는 0/8 무충돌이었다.'),\n"
            "('fig', '그림 5-5. 절제 실험 결과(원장 판정, 합산 n=20). (a) 4팔의 충돌/회피 분해 — 감지+3 s 과도구간 발사. (b) 동일 상한(3.0 m/s) 대피 정책의 2체제 대비 — 과도구간 11/20 대 정착 순항 0/8.', 'fig5_5ab', '"
            + PB + "/fig10_ablation.png', None, 14.5),\n", 'ko-ab-fig')
    io.open(p3, 'w', encoding='utf-8').write(s)
    print('KO content3 patched')

# ================= EN =================
tp = os.path.join(EN, 'translated.json')
tr = json.load(open(tp))

def find_item(chunk, needle, kind=None):
    hits = [k for k, it in enumerate(tr[chunk]['items'])
            if (kind is None or it['kind'] == kind)
            and isinstance(it['fields'][0], str) and needle in it['fields'][0]]
    assert len(hits) == 1, f'{chunk}: {len(hits)} hits for {needle!r}'
    return hits[0]

def patch_text(chunk, idx, old, new):
    f = tr[chunk]['items'][idx]['fields']
    assert f[0].count(old) == 1, f'{chunk}[{idx}]: {old!r} count={f[0].count(old)}'
    f[0] = f[0].replace(old, new)

def insert_fig(chunk, after_idx, caption, key, png, width):
    tr[chunk]['items'].insert(after_idx + 1,
        {'i': -1, 'kind': 'fig', 'fields': [caption, key, f'{PB}/{png}', None, width]})

if any(it['fields'][1] == 'fig4_3tl' for it in tr['ch4']['items'] if it['kind'] == 'fig'):
    print('EN already patched — skip')
else:
    # ch4: 조우 프로토콜
    i = find_item('ch4', 'per-case CSV', kind='p')
    patch_text('ch4', i, 'per-case CSV', 'per-case CSV (the protocol is shown in Figure 4-3)')
    insert_fig('ch4', i,
        'Figure 4-3. Pedestrian dart-out injection protocol. Fault injection (seed-fixed waveform) → shadow detection t_detect (common to all arms) → a behavior-independent launch at t_detect + 3 s spawns the pedestrian (crosses 12 m, then stops) at the standardized relative geometry of 8 m ahead, right lane edge + 0.5 m (lateral jitter ± 0.2 m).',
        'fig4_3tl', 'fig11_encounter.png', 14.0)

    # 재번호 (역순): KM 5-3 -> 5-4, 정지거리 5-2 -> 5-3
    i_km = find_item('ch5b', 'Figure 5-3.', kind='fig')
    patch_text('ch5b', i_km, 'Figure 5-3.', 'Figure 5-4.')
    i_sd = find_item('ch5a', 'Figure 5-2.', kind='fig')
    patch_text('ch5a', i_sd, 'Figure 5-2.', 'Figure 5-3.')
    i_lad = find_item('ch5a', 'Table 5-3, Figure 5-2', kind='p')
    patch_text('ch5a', i_lad, '(Table 5-3, Figure 5-2)', '(Table 5-3, Figure 5-3)')

    # 건강도 궤적 = Figure 5-2
    i_band = find_item('ch5a', 'continuous health-score signal', kind='p')
    patch_text('ch5a', i_band, 'continuous health-score signal.',
               'continuous health-score signal (Figure 5-2).')
    insert_fig('ch5a', i_band,
        'Figure 5-2. Continuous health traces — band separation of the state-transition input channel (solid: perception) against the dual thresholds (0.7/0.3). Dashed lines show the MRM move-gate obstacle channel; one representative run per condition, with warm-up and end-of-run stale artifacts trimmed.',
        'fig5_2ht', 'fig12_health.png', 14.5)

    # 절제 = Figure 5-5 (2체제 문단 뒤)
    i_2r = find_item('ch5b', 'yields a sharp contrast', kind='p')
    f0 = tr['ch5b']['items'][i_2r]['fields'][0]
    assert 'transient' in f0 and ('settled' in f0 or 'cruise' in f0), 'two-regime mismatch'
    if 'yields a sharp contrast' in f0:
        patch_text('ch5b', i_2r, 'yields a sharp contrast', 'yields a sharp contrast (Figure 5-5)')
    else:
        tr['ch5b']['items'][i_2r]['fields'][0] = f0.rstrip().rstrip('.') + ' (Figure 5-5).'
    insert_fig('ch5b', i_2r,
        'Figure 5-5. Ablation results (ledger verdicts, pooled n = 20). (a) Collision/avoidance decomposition of the four arms — launched in the detection + 3 s transient. (b) The same capped (3.0 m/s) evacuation policy in two regimes — 11/20 in the transient versus 0/8 in settled cruise.',
        'fig5_5ab', 'fig10_ablation.png', 14.5)

    json.dump(tr, open(tp, 'w'), ensure_ascii=False, indent=1)
    print('EN patched')
