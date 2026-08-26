# -*- coding: utf-8 -*-
"""심사 3차 반영(0826): FTTI 용어, 모델 설계용 근사식 강등, 조우 시점 한정,
'안전한 최종 위치' 강등, 표 4-5 케이스 회계, 표 4-4 재현성 행."""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

def rep(s, old, new, tag, n=1):
    c = s.count(old)
    if c == 0 and new in s:
        return s
    assert c == n, f'{tag}: count={c} (expect {n})'
    return s.replace(old, new)

# ================= content1 =================
p = os.path.join(HERE, 'content1.py'); s = io.open(p, encoding='utf-8').read()
s = rep(s, '고장 감내 시간 간격(FTTI) 단축 필요성에 대한 조우 수준의 정량적 근거',
        '고장 감내 시간 간격(FTTI) 이내의 안전 여유를 넓히는 감지·대응 시간 단축 필요성에 대한 조우 수준의 정량적 근거', 'f1')
s = rep(s, 'FTTI 단축 필요성을 뒷받침하는 정량적 관찰',
        '감지·대응 시간 단축(FTTI 내 여유 확보) 필요성을 뒷받침하는 정량적 관찰', 'f2')
s = rep(s, '차선 반환·더 안전한 최종 위치 확보 가능성(대피 측 이점)',
        '차선 반환·주행차선 밖 대피 위치 확보 가능성(대피 측 이점)', 'p4-1')
s = rep(s, '집중된다(11/20), 동일 정책이 정속 구간에서 만난 조우는 전부 회피되었다(0/8)',
        '집중되고(11/20; 감지+3 s 단일 발사 시점 기준), 동일 정책이 정속 구간에서 만난 조우는 전부 회피되었다(0/8)', 'p3-sum', 1) if '집중된다(11/20), 동일' in s else s
s = rep(s, '즉시 충돌 위험과 차선 반환·최종 안전 위치 사이의 트레이드오프',
        '즉시 충돌 위험과 차선 반환·주행차선 밖 최종 위치 사이의 트레이드오프', 'p4-rq2')
io.open(p, 'w', encoding='utf-8').write(s); print('content1 ok')

# ================= content2 =================
p = os.path.join(HERE, 'content2.py'); s = io.open(p, encoding='utf-8').read()
# ② 모델 강등: 보정 출처 명시 + 순환 검증 표현 제거
s = rep(s, '여기서 τ≈1.5 s와 a≈3.5 m/s²는 정밀 동정값이 아니라 근경계 체제를 재현하도록 선택한 공칭 집중(lumped) 파라미터이며, 본 모델의 산출은 가정 공칭 파라미터에 따른 모델 유도 상한(model-derived bound)으로 읽어야 한다.',
        '여기서 τ≈1.5 s와 a≈3.5 m/s²는 독립 실측치가 아니라 거리 사다리의 실측 경계(8~11 m)를 재현하도록 보정한 공칭 집중(lumped) 값이며, 따라서 본 식은 안전 경계의 예측 모델이 아니라 속도 상한 정책값 선정을 위한 설계용 근사식이다.', 'm1')
s = rep(s, '근경계 체제에서의 타당성은 거리 사다리의 실측 회피/충돌 경계(8~11 m)와 계산값(8.8 m)의 일치로 별도 확인된다(제5장 3절) — 동정 데이터(제동 틱 로그)와 검증 데이터(사다리 경계)는 독립이다.',
        '사다리 경계와 계산값(8.8 m)의 일치는 보정의 자기일관성 확인이지 독립 검증이 아니며, 별도 제동 실험은 (τ, a)가 체제 의존적임을 보여주는 독립 관측이다(제5장 3절).', 'm2')
# ⑥ 표 4-4: 정지거리 행 비고 수정 + 재현성 2행 추가
s = rep(s, "['정지거리 모델', 'τ=1.5 s, a=3.5 m/s²', 'd = vτ + v²/2a (식 3-9); τ는 실효 위험 대응 지연 (제3장 6절)'],",
        "['정지거리 모델', 'τ=1.5 s, a=3.5 m/s²', 'd = vτ + v²/2a (식 3-9); 사다리 경계에 보정한 공칭값 — 설계용 근사식 (제3장 6절)'],\n"
        "  ['비용함수 가중치', 'w_t=7.0/s · w_tl=200 · w_sec=500 · w_loc=14/s', '식 (3-8); 신호등당 대기 기대 15 s, 갓길 MRC 벌점 175(저하 주행 약 25 s 상당)'],\n"
        "  ['대피 후보 하드 제약', '최소 접근거리 25 m · 갓길 최소 길이 7.0 m', '미달 후보는 비용 무한대(제3장 5절)'],", 'r1')
io.open(p, 'w', encoding='utf-8').write(s); print('content2 ok')

# ================= content3 =================
p = os.path.join(HERE, 'content3.py'); s = io.open(p, encoding='utf-8').read()
# ② 5장 3절 순환 표현 완화
s = rep(s, '(ii) 속도→경계의 물리 모델이 본 환경에서 검증되었으므로 속도 상한의 효과를 같은 모델로 해석할 수 있다.',
        '(ii) 속도→경계의 설계용 근사식이 근경계 체제에서 자기일관됨이 확인되었으므로(보정 출처와 동일 데이터 — 독립 검증은 아니다, 제3장 6절) 속도 상한의 효과를 같은 근사식의 틀로 해석할 수 있다.', 'm3')
# ③ 시점 한정 (절제 결과 절)
s = rep(s, '이 감소는 과도구간 발사라는 최악 시간창에서 관찰된 것이다.',
        '이 감소는 과도구간 발사라는 최악 시간창에서 관찰된 것이다. 본 절제의 조우 시점은 감지+3 s 단일 시점으로 고정했으므로, 이 비교는 위험 발생 시점 분포 전반에 대한 정지/대피의 일반 비교가 아니라 해당 과도구간에 한정된 진술이다 — 정착 순항 0/8은 다른 시점의 보완 관측이나 표본이 작다.', 'g1')
# ④ 위치 표현 강등 + 2차 위험 미비교 명시
s = rep(s, '성공 시 차선을 반환하고 더 안전한 최종 위치로 이동한다.',
        '성공 시 차선을 반환하고 주행차선 밖 대피 위치로 이동한다. 차선 반환은 차로 점유 해소의 지표이지 최종 위치의 안전성 입증이 아니며, 갓길 위치의 2차 위험(후방 접근 차량 등)은 본 연구에서 직접 비교하지 않았다.', 'p4-2')
s = rep(s, '차선 반환과 안전 위치 확보의 가능성을 제공한다',
        '차선 반환과 차선 외 정차 위치 확보의 가능성을 제공한다', 'p4-3')
s = rep(s, '정지와 대피는 즉시 충돌 위험과 차선 반환·안전 위치의 시간적 트레이드오프이며',
        '정지와 대피는 즉시 충돌 위험과 차선 반환·차선 외 위치의 시간적 트레이드오프이며', 'p4-4')
# ③ 결론 한정 문구
s = rep(s, '둘째, 대피의 잔존 위험은 감지 후 과도구간(감지~정착 속도 도달)에 집중된다',
        '둘째, 대피의 잔존 위험은 감지 후 과도구간(감지~정착 속도 도달)에 집중된다 — 감지+3 s 단일 발사 시점 실험에 한정된 진술이다', 'g2')
# ① ABSTRACT_EN FTTI
s = rep(s, 'in shortening the fault-tolerant time interval (FTTI)',
        'in widening the safety margin within the fault-tolerant time interval (FTTI)', 'f3')
# ③ ABSTRACT_EN 시점 한정
s = rep(s, 'the residual risk of evacuation\nconcentrates in the detection-to-deceleration transient (11/20 transient vs\n0/8 settled)',
        'the residual risk of evacuation concentrates in the detection-to-deceleration transient (11/20 transient vs 0/8 settled; a single launch instant at detection + 3 s)', 'g3', 1) if 'detection-to-deceleration transient (11/20' in s and '11/20 transient vs\n0/8' in s else s
s = rep(s, 'concentrates in the detection-to-deceleration transient (11/20 transient vs 0/8 settled)',
        'concentrates in the detection-to-deceleration transient (11/20 transient vs 0/8 settled; a single launch instant at detection + 3 s)', 'g3b', 1) if 'transient (11/20 transient vs 0/8 settled)' in s else s
# ⑤ 회계 표 + 본문 문장
s = rep(s, '총 유효 케이스는 1,131이다.',
        '총 유효 케이스는 1,131이다(계획 1,170 대비 부족 39는 전량 lcl-high — 표 4-5).', 'a1', 1) if '총 유효 케이스는 1,131이다.' in s else s
io.open(p, 'w', encoding='utf-8').write(s); print('content3 ok')

print('KO round3 done')
