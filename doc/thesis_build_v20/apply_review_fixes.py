# -*- coding: utf-8 -*-
"""0826 전면 검수 반영: 5개 리뷰 에이전트 발견사항 일괄 핀셋 수정 (KO+EN).
strict: 검증된 앵커는 assert, 불확실 앵커는 warn 리스트로 보고."""
import io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(HERE, '..', 'thesis_build_en')
WARN = []

def rep(s, old, new, tag, n=1):
    c = s.count(old)
    if c == 0 and new in s:
        return s  # already applied (idempotent)
    assert c == n, f'{tag}: count={c} (expect {n}) for {old[:50]!r}'
    return s.replace(old, new)

def rep_opt(s, old, new, tag):
    c = s.count(old)
    if c == 1:
        return s.replace(old, new)
    WARN.append(f'{tag}: count={c}, skipped')
    return s

# ================= content1 =================
p = os.path.join(HERE, 'content1.py')
s = io.open(p, encoding='utf-8').read()
s = rep(s, '○(9종 주입 실증)', '○(11종 주입 실증)', 'c1-t21')
s = rep(s, '대응 전략(갓길·주차장 대피 vs 즉시 정차 위임)을 차등 선택할',
        '대응 전략(갓길·주차장 대피 vs 순정 정차 위임)을 구분 선택할', 'c1-rq1')
s = rep(s, '본 연구는 이를 각각 연속 건강도 점수, 위험·잔여능력 기반 상태 전이, 잔여능력 기반 보수적 속도 상한',
        '본 연구는 이를 각각 위험·잔여능력 기반 상태 전이, 연속 건강도 점수, 잔여능력 기반 보수적 속도 상한', 'c1-each')
s = rep(s, '표 2-1이 보이듯', '표 2-1이 보여주듯', 'c1-tbl21')
s = rep(s, '차로 내 정차가 항상 안전하지 않음을', '차로 내 정차가 항상 안전한 것은 아님을', 'c1-neg')
s = rep(s, '(FDTI·FRTI·안전 여유 분해 프레임 포함', '(감지 시간 FDTI·대응 시간 FRTI·안전 여유의 분해 프레임 포함', 'c1-fdti')
s = rep(s, '본 연구의 cn·cf 주입의 준거이고', '본 연구의 카메라 노이즈(cn)·사망(cf) 주입의 준거이고', 'c1-cncf')
s = rep(s, '④ 차선 내 정지', '④ 차로 내 정지', 'c1-lane')
s = rep(s, '단축의 필요성을 뒷받침하는 조우 수준의 정량적 관찰을 제공한다',
        '단축 필요성에 대한 조우 수준의 정량적 근거를 제공한다', 'c1-dup')
s = rep(s, '11회 충돌하였다(exact McNemar, A1↔A4 p=0.375)',
        '11회 충돌하였다(exact McNemar, 순정 지속(A1)↔상한 대피(A4) p=0.375)', 'c1-a1a4')
io.open(p, 'w', encoding='utf-8').write(s)
print('content1 ok')

# ================= content2 =================
p = os.path.join(HERE, 'content2.py')
s = io.open(p, encoding='utf-8').read()
s = rep(s, '식 (3-6)의 τ_fresh와 min(·, TTC_cons)는 식 (3-1)의 신선도 감쇠 시간상수이며',
        '식 (3-6)의 결과 τ_detect(t)가 식 (3-1)의 신선도 감쇠 시간상수로 쓰이며(τ_fresh는 평시 기본 시간상수)', 'c2-tau')
s = rep(s, '에 장애물 지각과 신호등 관측성을 0.6:0.4로 결합한다',
        '으로 각각 산출한 장애물 지각과 신호등 관측성을 0.6:0.4로 결합한다', 'c2-0604')
s = rep(s, '차이가 임계를 3초 이상 지속하면 감점한다', '차이가 임계를 초과한 상태로 3초 이상 지속되면 감점한다', 'c2-imu')
s = rep(s, '가중치 절대값은 정밀 튜닝을 주장하지 않는다', '가중치 절댓값에 대해 정밀 튜닝을 주장하지는 않는다', 'c2-abs')
s = rep(s, '전방 거리 D에서 장애물이 출현했을 때', '전방 거리 D_avail에서 장애물이 출현했을 때', 'c2-davail')
s = rep(s, '(i) 스폰은 보도가 아닌 주행 차선 우측 끝(+0.5 m)에서 횡단을 시작해',
        '(i) 보행자는 보도가 아닌 주행 차선 우측 끝(+0.5 m)에서 스폰되어 횡단을 시작해', 'c2-spawn')
s = rep(s, '전 케이스 판정은 5절의 원장 기준이다',
        '판정은 5절의 원장 기준이며, 원장 도입 전 실행분의 예외는 제5장 3절에 명시한다', 'c2-ledger')
s = rep(s, '갓길 후보 16개소(레인렛 형상)', '갓길 후보 16개소(lanelet 형상)', 'c2-lanelet')
s = rep(s, '순정 차선 내 정지로 귀결된다', '순정 차로 내 정지로 귀결된다', 'c2-lane31')
s = rep(s, '대피지 선택은 비용 최소화로 한다:', '대피지 선택은 비용 최소화로 한다(후보 배치는 그림 3-4):', 'c2-fig34ref')
s = rep(s, 'η(c)는 열화 상태 노출시간(경로시간 + 신호등당 대기 기대치)',
        'η(c)는 열화 상태 노출시간(경로시간 + 신호등당 대기 기대치), g(tl)은 신호등 관측성 저하 벌점(1/cap_tl − 1), sector_req는 후보 접근에 요구되는 섹터 점수, loc은 측위 신뢰, w∗는 각 항의 가중치', 'c2-eq38')
s = rep(s, '백색 노이즈(gn)·상관 편향(gb)·신호 상실(gf)', '백색 노이즈(gn)·상관 편향(gb)·두절(gf)', 'c2-gf')
s = rep(s, '전 패널의 파라미터는 표 4-2의 mid/high 원값이다.',
        '패널 파라미터는 표 4-2의 심각도 정의에 대응하는 주입기 원값이며(대표값은 표 4-4), 두절(gf)·사망형에는 심각도 구분이 없다.', 'c2-fig42cap')
s2, nsub = re.subn(r"\.'\),\n\('fig', '그림 4-2\.",
                   ". 각 고장의 센서 수준 효과는 그림 4-2에 예시한다.'),\n('fig', '그림 4-2.", s)
assert nsub == 1, f'c2-fig42ref: {nsub}'
s = s2
s = rep(s, '재실행했다(본 캠페인에서 S05 2회)', '재실행했다(절제 1차 회차에서 S05 2회)', 'c2-s05')
io.open(p, 'w', encoding='utf-8').write(s)
print('content2 ok')

# ================= content3 =================
p = os.path.join(HERE, 'content3.py')
s = io.open(p, encoding='utf-8').read()
s = rep(s, '96~100%의 검출률과 2.1~5.0 s의 중앙 감지 지연을 보였고, 무고장(nf) 대조 45케이스에서',
        '96~100%의 검출률을 보였고, 중앙 감지 지연은 하드 페일(cf·lf) 약 1.0 s(원장 재계측)·열화형 2.1~5.0 s였다. 무고장(nf) 대조 45케이스에서', 'c3-range1')
s = rep(s, '96~100%의 검출률과 2.1~5.0 s의 중앙 감지 지연을 보였고 무고장 45케이스에서',
        '96~100%의 검출률을 보였고(중앙 감지 지연: 하드 페일 약 1.0 s·열화형 2.1~5.0 s) 무고장 45케이스에서', 'c3-range2')
s = rep_opt(s, "96-100% detection rates with 2.1-5.0 s median detection latency in 11 of 12 fault conditions",
        "96-100% detection rates in 11 of 12 fault conditions, with median detection latencies of about 1.0 s for hard fails (ledger re-measurement) and 2.1-5.0 s for degradation faults", 'abs-range-flat')
s = rep_opt(s, 'a by-design tolerated mild lidar sparsification',
        'mild LiDAR sparsification that is tolerated by design', 'abs-lidar')
s = rep(s, 'avoided all encounters (0/8)', 'avoided collision in all encounters (0/8)', 'abs-avoid')
s = rep(s, 'exact McNemar, A1 vs A4: p=0.375',
        'exact McNemar, native continuation (A1) vs capped evacuation (A4): p=0.375', 'abs-a1a4')
s = rep(s, "['cf 카메라 사망', 'mid', '45', '1.00', '0.98*']", "['cf 카메라 사망', '-', '45', '1.00', '0.98*']", 'c3-t51cf')
s = rep(s, "['lf 라이다 사망', 'mid', '45', '1.00', '1.00*']", "['lf 라이다 사망', '-', '45', '1.00', '1.00*']", 'c3-t51lf')
s = rep(s, '보조 캠페인(항법 확장, 표 4-2 †)', '보조 캠페인(항법 확장, 표 5-1 †)', 'c3-fig51a')
s = rep(s, '카메라·라이다 사망(†)은', '카메라·라이다 사망(*)은', 'c3-fig51b')
s = rep(s, '표 5-3. 거리 사다리 결과 (원장 판정)', '표 5-3. 거리 사다리 결과 (원장·영상 판정)', 'c3-t53')
s = rep(s, '대피 거동(전 조합: 고장-심각도 × 방법)을 표 5-2에 요약한다.',
        '대피 거동을 표 5-2에 요약한다(고장·심각도 전 조합, 제안 방식 기준).', 'c3-t52')
s = rep(s, '설계상 차선 내 정지 정책의 정의상 결과이다', '설계상 차로 내 정지 정책의 정의에 따른 결과이다', 'c3-lane')
s = rep(s, '45케이스 중 40건이 갓길 대피의 주력이었던 반면', '45케이스 중 40건이 갓길 대피로 이어져 대피가 주력이었던 반면', 'c3-40')
s = rep(s, 'GNSS 계열은 완만 정지, IMU 계열은 전량 급정지 — 완만 정지도',
        'GNSS 계열은 컴포트 정지, IMU 계열은 전량 급정지 — 컴포트 정지도', 'c3-comfort')
s = rep(s, '위임 정지의 방식이 고장 유형을 따라 갈렸다', '위임 정지의 방식이 고장 유형에 따라 갈렸다', 'c3-ttara')
s = rep(s, '유효 611/630 케이스 전 조건에서', '유효 611/630 케이스의 전 조건에서', 'c3-611')
s = rep(s, 'S05·S12·S13·S15·S19·S20·S21은 A2(정지)를 제외한',
        'S05·S07·S08·S12·S13·S15·S19·S20·S21은 A2(정지)를 제외한', 'c3-seeds')
s = rep(s, '충돌 7건은 표 5-5의 팔별 충돌 계(A3 3건+A4 4건)와 산술적으로 일치한다',
        '충돌 7건은 표 5-5 중 1차 회차(S02~S11)의 팔별 충돌 수(A3 3건+A4 4건)와 산술적으로 일치한다', 'c3-a33')
s = rep(s, 'cf·lf 전 매트릭스(각 90케이스, 본 캠페인과 동일 구조)에서 원장 기반',
        'cf·lf 전 매트릭스(각 90케이스 실행분, 본 캠페인과 동일 구조; 지연 n은 원장 지연 파싱 가능분, MRM 분모는 원장 도입 후 판정 가능분으로 시뮬레이터 실패 제외에 따라 90 미만이다)에서 원장 기반', 'c3-90')
s = rep(s, '정상 대피에서 상한은 거의 구속되지 않으며', '정상 대피에서 속도가 상한에 거의 도달하지 않으며', 'c3-bind')
s = rep(s, '실행 계층 의존도 명시한다', '실행 계층 의존성도 명시한다', 'c3-dep')
s = rep(s, '(v) 최소 간격 지표의 임계(1.25 m)는',
        '(v) 조우 근접도 보조 지표로 기록한 최소 간격(min-gap)의 임계(1.25 m)는', 'c3-mingap')
s = rep(s, '무충돌 13케이스에 조건부로 산출한 시간분포에서',
        '무충돌 13케이스에 조건부로 산출한 시간분포(그림 5-4)에서', 'c3-fig54ref')
s = rep_opt(s, '단축의 필요성을 뒷받침하는 조우 수준의 정량적 관찰을 제공한다',
        '단축 필요성에 대한 조우 수준의 정량적 근거를 제공한다', 'c3-dup')
s = rep_opt(s, '축소할 것으로 실험적으로 뒷받침된다', '축소할 것임이 실험적으로 뒷받침된다', 'c3-support')
io.open(p, 'w', encoding='utf-8').write(s)
print('content3 ok')

# ================= EN translated.json =================
tp = os.path.join(EN, 'translated.json')
tr = json.load(open(tp))

def en_rep(old, new, tag, n=1, chunks=None):
    hits = 0
    for c in (chunks or tr.keys()):
        for it in tr[c]['items']:
            f = it['fields']
            if isinstance(f[0], str) and old in f[0]:
                f[0] = f[0].replace(old, new)
                hits += f[0].count(new) - 0  # count occurrences replaced
                hits = hits if hits else 1
            # table rows
            if it['kind'] == 'tbl' and len(f) > 2 and isinstance(f[2], list):
                for row in f[2]:
                    for i, cell in enumerate(row):
                        if isinstance(cell, str) and old in cell:
                            row[i] = cell.replace(old, new)
                            hits += 1
    if hits == 0:
        WARN.append(f'EN {tag}: not found')

def en_rep_strict(old, new, tag):
    found = False
    for c in tr:
        for it in tr[c]['items']:
            f = it['fields']
            if isinstance(f[0], str) and old in f[0]:
                f[0] = f[0].replace(old, new, 1)
                found = True
    if not found:
        WARN.append(f'EN {tag}: MISSING')

# --- factual mirrors ---
en_rep_strict('9 injected types', '11 injected types', 't21')
en_rep_strict('96-100% detection rates with 2.1-5.0 s median detection latency in 11 of 12 fault conditions',
              '96-100% detection rates in 11 of 12 fault conditions, with median detection latencies of about 1.0 s for hard fails (ledger re-measurement) and 2.1-5.0 s for degradation faults', 'range51')
en_rep_strict('with 2.1-5.0 s median detection latency', 'with median detection latencies of about 1.0 s (hard fails) and 2.1-5.0 s (degradation faults)', 'range-concl')
en_rep_strict('S05, S12, S13, S15, S19, S20, and S21 were harsh realizations',
              'S05, S07, S08, S12, S13, S15, S19, S20, and S21 were harsh realizations', 'seeds')
def en_tbl_cell(chunk, key, old, new, tag):
    for it in tr[chunk]['items']:
        if it['kind'] == 'tbl' and it['fields'][1] == key:
            for row in it['fields'][2]:
                for i, cell in enumerate(row):
                    if isinstance(cell, str) and old in cell:
                        row[i] = new
                        return
    WARN.append(f'EN {tag}: MISSING')
# 표 5-1 cf/lf severity
for it in tr['ch5a']['items']:
    if it['kind'] == 'tbl' and it['fields'][1] == 'tbl5_0':
        for row in it['fields'][2]:
            if row and isinstance(row[0], str) and ('cf ' in row[0] or 'lf ' in row[0]) and 'death' in row[0]:
                if row[1] == 'mid':
                    row[1] = '-'
# fig5-1 caption symbols
en_rep_strict('Table 4-2 †', 'Table 5-1 †', 'fig51a')
en_rep_strict('camera and LiDAR death (†)', 'camera and LiDAR death (*)', 'fig51b')
# 표 5-3 caption
en_rep_strict('distance ladder results (ledger', 'distance ladder results (ledger and video', 't53')
en_rep_strict('Table 5-3. Distance ladder results (ledger verdicts)', 'Table 5-3. Distance ladder results (ledger and video verdicts)', 't53b')
# fig4-2 caption claim + gf naming
en_rep_strict('Parameters in all panels are the raw mid/high values of Table 4-2.',
              "Panel parameters are the injector's raw values corresponding to the severity definitions of Table 4-2 (representative values in Table 4-4); outage (gf) and death-type faults have no severity grades.", 'fig42cap')
en_rep_strict('signal outage (gf)', 'outage (gf)', 'gfname')
# fig citations
en_rep_strict('minimizes a cost', 'minimizes a cost (the candidate layout is shown in Figure 3-4)', 'fig34ref')
# fig4-2 in-text ref: append to paragraph preceding fig4_faults
items4 = tr['ch4']['items']
for i, it in enumerate(items4):
    if it['kind'] == 'fig' and it['fields'][1] == 'fig4_faults':
        prev = items4[i-1]
        if prev['kind'] == 'p':
            prev['fields'][0] = prev['fields'][0].rstrip() + ' The sensor-level effect of each fault is illustrated in Figure 4-2.'
        break
en_rep_strict('conditionally on the 13 collision-free cases', 'conditionally on the 13 collision-free cases (Figure 5-4)', 'fig54ref')
# ledger exception (ch4)
en_rep_strict('All cases are judged by the ledger criteria of Section 5',
              'Judgments follow the ledger criteria of Section 5; the exception for runs predating the ledger is stated in Chapter 5, Section 3', 'ledgerX')
# 각 90케이스
en_rep_strict('(90 cases each, the same structure as the main campaign)',
              '(90 executed cases each, the same structure as the main campaign; the latency n counts runs with parsable ledger latencies, and the MRM denominators count runs judgeable after the ledger introduction, so both fall below 90 after simulator-failure exclusion)', 'n90')
# --- EN language fixes (agent items) ---
en_rep_strict('rests on data predating the ledger introduced in Section 5', 'rests on data predating the ledger introduced in Chapter 4, Section 5', 'e2')
en_rep_strict('the formalization of the FRTI and margin explicitly reserved in Chapter 3, Section 4', 'the explicit FRTI-and-margin reservation deferred as future work in Chapter 3, Section 4', 'e3')
en_rep_strict('in settled cruise after deceleration avoided all encounters (0/8)', 'in settled cruise after deceleration avoided collision in all encounters (0/8)', 'e4a')
en_rep_strict('avoided all 8 runs and subsequently completed shoulder evacuation', 'avoided the pedestrian in all 8 runs and subsequently completed shoulder evacuation', 'e4b')
en_rep_strict('while 7, 6, and 5 m each collided in 2/2', 'while at 7, 6, and 5 m the vehicle collided in 2/2 runs at each distance', 'e5a')
en_rep_strict('as opposed to whether maneuvers succeed', 'rather than checking whether maneuvers succeed', 'e6')
en_rep_strict('are experimentally supported to shrink the overall fault-response risk window', 'are experimentally supported as means of shrinking the overall fault-response risk window', 'e7')
en_rep_strict('Hard fail (signal loss) is detected and adjudicated', 'Hard fails (signal loss) are detected and adjudicated', 'e8')
en_rep_strict('Dead sensors are decided through the hard-fail fast path', 'Dead-sensor cases are decided through the hard-fail fast path', 'e9')
en_rep_strict('only IMU noise stopped on its own due to the anomaly, at 71 m', 'only under IMU noise did the stack stop on its own, at 71 m', 'e10')
en_rep_strict('unreturned within the observation horizon', 'unobserved within the observation horizon', 'e11')
en_rep_strict('with only end of observation right-censored', 'with right-censoring applied only at the end of observation', 'e12')
en_rep_strict('To ablate the effect of the proposed system into four arms', 'To isolate the contributions of non-intervention, stop, evacuation, and the speed cap', 'e13')
en_rep_strict('deadline compliance with this deadline', 'compliance with this deadline', 'e14')
en_rep_strict('the actual maneuver incompletions number 2', 'the actual maneuver incompletions being the 2 cases above', 'e15')
en_rep_strict('both of its 2 runs', 'both of its runs', 'e16')
en_rep_strict('can check that map annotation quality is a hidden confounding variable', 'can treat map annotation quality as a hidden confounding variable', 'e17')
en_rep_strict('reflecting degraded exposure time', 'reflecting degraded-state exposure time', 'e18')
en_rep_strict('because signal reading is impossible', 'because traffic-signal reading is impossible', 'e19')
en_rep_strict('refuge-candidate search', 'evacuation-candidate search', 'e20')
en_rep_strict('DEFER (delegate — inject a diagnostic ERROR)', 'DEFER (defer to the stock stop — inject a diagnostic ERROR)', 'e21')
en_rep_strict('produced gentle stops', 'produced comfortable stops', 'e22a')
en_rep_strict('gentle stops also track a trajectory', 'comfortable stops also track a trajectory', 'e22b')
en_rep('deciding variable', 'decision variable', 'e23', chunks=['ch5a', 'ch5b'])
en_rep('graduated', 'graded', 'e24')
en_rep('Graduated', 'Graded', 'e24b')
en_rep_strict('manner rules', 'courtesy rules', 'e28')
en_rep('reexperiment', 're-run experiment', 'e29a')
en_rep('re-experiment', 're-run', 'e29b')
en_rep_strict('problem awareness', 'concern', 'e30')
en_rep_strict('The threshold of the minimum-separation metric (1.25 m)', 'The threshold of the minimum-separation (min-gap) metric recorded as an auxiliary encounter-proximity measure (1.25 m)', 'e1')
# 그림 5-2 caption term
en_rep_strict('(a) LiDAR soiling (lso), (b) camera pixel noise (cn). Time zero', '(a) LiDAR sparsification (lso), (b) camera pixel noise (cn). Time zero', 'e52term')
# --- typography sweeps: tilde ranges & interpunct (EN fields only) ---
tilde = re.compile(r'(?<=[0-9A-Za-z])\s*~\s*(?=[0-9A-Za-z])')
inter = re.compile(r'(?<=[A-Za-z0-9])·(?=[A-Za-z0-9])')
for c in tr:
    for it in tr[c]['items']:
        f = it['fields']
        if isinstance(f[0], str):
            f[0] = tilde.sub('–', f[0])
            f[0] = inter.sub('/', f[0])
        if it['kind'] == 'tbl' and len(f) > 2 and isinstance(f[2], list):
            for row in f[2]:
                for i, cell in enumerate(row):
                    if isinstance(cell, str):
                        row[i] = inter.sub('/', tilde.sub('–', cell))
            if isinstance(f[3], str):
                f[3] = inter.sub('/', tilde.sub('–', f[3]))

json.dump(tr, open(tp, 'w'), ensure_ascii=False, indent=1)
print('translated ok')
print('WARNINGS:', len(WARN))
for w in WARN:
    print('  -', w)
