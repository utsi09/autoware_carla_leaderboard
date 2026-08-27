# -*- coding: utf-8 -*-
"""v24 (0827): 4차 외부검수 11건 — 노출 주장 강도(유형별 1런 명시), 지연 시계 병기,
lso-mid 검출/감내 분리, 용량-반응 적용범위 초록·결론 유지, 1.5 s=설계 마감 명시,
재현성 행(τ_fresh·CUSUM·실행환경), 동적 예산 한계, KM 조건부 명시, 육안 비맹검 명시,
ref[15] 서지 정정."""
import io, os
HERE = os.path.dirname(os.path.abspath(__file__))

def make(pth):
    def rep(old, new, tag, exp=1):
        s = io.open(pth, encoding='utf-8').read()
        c = s.count(old)
        if c == 0 and new in s:
            print(tag, 'already'); return
        assert c == exp, f'{tag}: count={c}'
        io.open(pth, 'w', encoding='utf-8').write(s.replace(old, new))
        print(tag, 'ok')
    return rep

# ================= content1 (초록·1장) =================
r = make(os.path.join(HERE, 'content1.py'))
# 1. 노출 강도
r('무감시 순정의 238~251 m에서 감시+대피의 32~58 m(카메라·항법 계열)로 단축함을 보였다(라이다 클러터는 275→11~12 m)',
  '무감시 순정의 대표 관찰(고장 유형별 1런) 238~251 m 대비 감시+대피의 32~58 m(카메라·항법 계열)로 단축함을 보였다(라이다 클러터는 275→11~12 m)', 'n1a')
r('순정 스택은 고장 주입 상태로 238~275 m를 사실상 완주하였다(IMU 노이즈만 71 m 자체 이상 정지 — 제5장 2절)',
  '유형별 1런의 무개입 관찰에서 순정 스택은 고장 주입 상태로 238~275 m를 사실상 완주하였다(IMU 노이즈만 71 m 자체 이상 정지 — 제5장 2절)', 'n1b')
# 4. 용량-반응 적용범위 (초록)
r('쌍대 비교는 불일치 10:0(exact McNemar p=0.002)으로 충돌 감소 효과가 검출되었고',
  '쌍대 비교는 불일치 10:0(exact McNemar p=0.002)으로 충돌 감소 효과가 검출되었고(정착 체제·gn-mid 단일 고장 조건)', 'n4a')
# 5. 설계 마감 (초록)
r('1.5 s 마감 안에 완료하며(실측 최대 1.20 s)',
  '1.5 s 설계 마감(내부 요구) 안에 완료하며(실측 최대 1.20 s)', 'n5a')

# ================= content2 (3~4장) =================
r = make(os.path.join(HERE, 'content2.py'))
# 6. 재현성 행 3개 (상태 전이 임계 행 뒤)
r("['상태 전이 임계', 'upper 0.7 / lower 0.3', '이중 임계 — 정상/대피/위임 3구간 (제3장 5절)'],",
  "['상태 전이 임계', 'upper 0.7 / lower 0.3', '이중 임계 — 정상/대피/위임 3구간 (제3장 5절)'],\n"
  "  ['신선도 마감 τ_fresh', '850 ms', '하드 페일 고속경로의 판정 기준 (제3장 4·5절)'],\n"
  "  ['CUSUM 파라미터', 'k = 0.5×무고장 기준선(적응) ·\\nh = 0.5 m(라이다 σ)/30(카메라 σ)', '품질 계열 변화 검정 (제3장 2절)'],\n"
  "  ['실행 환경', 'Autoware 0.39.0 · CARLA 0.9.16 ·\\nROS 2 Humble', '동기 모드·고정 스텝 0.05 s, 단일 워크스테이션'],", 'n6')
# 9. 육안 비맹검 명시
r('검토자에게 전달하여 독립 판정과 대조했다(verdict_review.csv). 본 논문의 조우 실험 전 케이스에서 기계-사람 판정이 일치했다.',
  '검토자에게 전달하여 대조했다(verdict_review.csv). 이 검토는 기계 판정·팔 정보를 가린 맹검(blind)이 아니라 전수 대조 목적의 공개 검토이며, 불일치 시 원장·물리 오라클을 우선하는 규칙을 사전에 두었다. 본 논문의 조우 실험 전 케이스에서 기계-사람 판정이 일치했다.', 'n9')

# ================= content3 (5~7장·초록EN·REFS) =================
r = make(os.path.join(HERE, 'content3.py'))
# 1. 노출 (결론)
r('감시는 고장 상태 노출을 무감시 238~251 m에서 카메라·항법 계열 기준 32~58 m로 단축했고',
  '감시는 고장 상태 노출을 무감시 대표 관찰(유형별 1런) 238~251 m 대비 카메라·항법 계열 기준 32~58 m로 단축했고', 'n1c')
# 2. 지연 시계 병기 (결론)
r('(중앙 감지 지연: 하드 페일 약 1.0 s·열화형 2.1~5.0 s)',
  '(중앙 감지 지연: 하드 페일 약 1.0 s는 시뮬레이션 시간, 열화형 2.1~5.0 s는 벽시계 — 시계 기준이 달라 직접 비교하지 않는다)', 'n2a')
# 3. lso-mid 검출/감내 분리
r('이 수준의 포인트 탈락 후에도 유효 검출거리 약 55 m가 잔존하여 건강도가 개입 조건',
  '이 수준의 포인트 탈락 후에도 유효 검출거리 약 55 m가 잔존하여 건강도가 개입 조건', 'n3-anchor-check')
# 4. 결론 적용범위
r('8 m 쌍대 불일치 10:0(exact McNemar p=0.002)으로 충돌 감소 효과가 검출되었고, 회피/충돌 경계는 상한을 낮출수록 단조로 안쪽 이동했다(9 m 초과→약 7 m).',
  '8 m 쌍대 불일치 10:0(exact McNemar p=0.002)으로 충돌 감소 효과가 검출되었고(정착 체제·gn-mid 단일 고장 조건), 회피/충돌 경계는 상한을 낮출수록 단조로 안쪽 이동했다(9 m 초과→약 7 m).', 'n4b')
# 5. 설계 마감 (결론·5장 9절)
r('고속 판정 경로로 감지·판정을 1.5 s 마감 안에 완료한다(전 매트릭스 실측 최대 1.20 s',
  '고속 판정 경로로 감지·판정을 1.5 s 설계 마감 안에 완료한다(전 매트릭스 실측 최대 1.20 s', 'n5b')
r('하드 페일(신호 두절)의 감지·판정에는 1.5 s 마감을 사양으로 둔다.',
  '하드 페일(신호 두절)의 감지·판정에는 1.5 s 마감을 설계 사양(내부 요구)으로 둔다 — 특정 안전 목표에 대한 FTTI 준수 주장이 아니다(제3장 4절).', 'n5c')
# 7. 동적 예산 한계 (6장 6절 말미 — (iii) 문장 뒤)
r('여전히 primary contrast의 미검출을 동등성으',
  '여전히 primary contrast의 미검출을 동등성으', 'n7-anchor-check')
# 8. KM 조건부 명시
r('정지(A2)와 순정(A1)은 지평 내 차선 이탈이 0건으로, 우측 중도절단("지평 내 미반환")으로 표기하며 평균화하지 않는다.',
  '정지(A2)와 순정(A1)은 지평 내 차선 이탈이 0건으로, 우측 중도절단("지평 내 미반환")으로 표기하며 평균화하지 않는다. 따라서 그림 5-4의 수치는 무충돌 대피에 조건부인 반환 시간으로만 읽어야 하며, 충돌을 경쟁 사건으로 포함하는 정책 수준 비교(누적 발생률 분석)는 수행하지 않았다.', 'n8')
# 10. ref [15] 서지 정정 (파트별 제목·쪽 명기)
r('\'Z. Gao, C. Cecati, and S. X. Ding, "A survey of fault diagnosis and fault-tolerant techniques — Part I/II," IEEE Transactions on Industrial Electronics, vol. 62, no. 6, pp. 3757-3774, 2015.\'',
  '\'Z. Gao, C. Cecati, and S. X. Ding, "A survey of fault diagnosis and fault-tolerant techniques — Part I: fault diagnosis with model-based and signal-based approaches (pp. 3757-3767); Part II: fault diagnosis with knowledge-based and hybrid/active approaches (pp. 3768-3774)," IEEE Transactions on Industrial Electronics, vol. 62, no. 6, 2015.\'', 'n10')
# ABSTRACT_EN 미러
r('reduced degraded-state driving exposure from 238-251 m',
  'reduced degraded-state driving exposure from a representative unmonitored observation (one run per fault type) of 238-251 m', 'en1')
r('gave discordant pairs 10:0 (exact McNemar p=0.002)',
  'gave discordant pairs 10:0 (exact McNemar p=0.002; settled regime, single fault type gn-mid)', 'en4')
r('meeting a 1.5-s detection-to-decision deadline',
  'meeting the internal 1.5-s detection-to-decision design deadline', 'en5')
print('KO v24 done')
