# RA-L 골격 초안 (0816 밤 기준, 확정 수치 반영)

**가제(리뷰 반영)**: Fault-Adaptive Minimal Risk Maneuvers with
Capability-Aware Speed Limiting for Degraded Automated Driving
(구제목의 'Prevent Collisions'는 과대주장 — 완화)

## 1. Introduction (0.75p)
- 고장 시 AD 대응의 공백: **평가한 Autoware 0.39.0 구성에서는** 주입 고장
  대부분을 자체 진단이 못 잡았고, 가용 fallback은 정지형 MRM에 한정
  (일반 Autoware 주장 금지 — 해당 버전·런치 설정 한정, commit/config 증빙)
- 기여 3: ① BT 기반 동적 FTTI 감시(cdr) ② 건강도 인지 갓길 대피 계획
  ③ **고장 비례 저속 MRM 이동** — 조우 수준 정량 검증 (에고 센서 원장 기반)

## 2. Related Work (0.5p)
- MRM/MRC 표준: UNECE R157(traffic risk 최소화 자동 절차 — background 인용).
  ISO 3691-4(2023)는 산업차량 표준 — '유사 도메인의 설계 원리'로 강등 인용
- Reschka capability graphs (건강도→행동 제한), AWCL(TUMFTM) 인용 필수
- CARLA 고장 주입 선행연구 + 비-라이다 강우 영향 문헌 (paper.md에 확보됨)

## 3. System (1.5p)
- cdr_monitor(감지기 3종) + mrm_supervisor(후보 선정·대피·속도 캡)
- 속도 캡 경로: `/planning/scenario_planning/max_velocity_candidates`
  (selector 입력 — 출력 토픽 직접 발행 시 재출발 불능, 실측 교훈 각주감)
- 고장 모델 v4.6 (ln 퇴출, lso/lcl 물리 모델)

## 4. Experimental Setup (1p)
- CARLA 0.9.16 + AWCL, Town07, 제한속도 15km/h(4.2m/s)
- 보행자 돌발 주입기: 공정 기하(차선끝 스폰·걷기 검증·횡단 후 정지),
  거리 파라미터화, MRM-무장 발사
- **충돌 진실 3중 오라클**: 에고 충돌센서 실시간 원장(RAW-HIT) / 물리(워커
  튕김) / 간격 스트림 — 사람 육안 교차검증 A~BA 전 케이스 일치
- 한계 명기: 단일 맵·단일 제한속도·발사 지점 2곳

## 5. Results (2.5p)
### 5.1 거리 사다리 (그림 a): 무고장 순정, 거리당 n=4
14·11m 회피 100% / 8·6·5m 충돌 100% → 정지거리 경계 8–11m (물리 모델과 일치:
반응 ~1.5s + 제동, v=4.2)
### 5.2 8m 조우 3조건 (그림 b): 자이로 고장, 지각계 동일
- 우리 순항 3.0: 8/8 회피 + 대피 완수 / 순정 4.2: 0/10 (p≈4e-4)
- 감속 과도구간 2/2 충돌 → 잔존 위험창 = FTTI 단축 논거 (5.4)
### 5.3 고장 스펙트럼 거동
- 실명(lso-high): 순정 8m 이하 충돌·원거리 동결(도로 점거)
- 카메라 사망: 순정 신호교차로 영구 대기 (부산물 관찰)
- 노출 지표: 고장 상태 주행거리 순정 240–275m vs 우리 33–58m (그림 c)
### 5.4 Discussion: 과도구간, 저속의 비용(대피 시간), C팔 발견
  ("캡 없어도 대피 기동은 자연 저속" → 캡은 보장 장치)

## 6. Conclusion (0.25p)

## 그림 목록
1. fig_final_campaign.png (a 사다리 곡선 + b 8m 3조건)
2. fig_exposure.png (노출 지표) — cf 240m 등 v4.8 데이터
3. 시스템 다이어그램 (그릴 것)
4. 대피 지도 (route + 갓길, 그릴 것)

## 데이터 부속
- verdict_review.csv (사람-기계 판정 대조 A~BA)
- collision_live.log (원시 원장), boundary_8m_summary.csv, merged_final.csv
- 남은 정리: v4.7+ 코드 freeze 커밋, CDR_DEMO_NO_ERROR 등 임시설정 원복


## 리뷰 반영 추가 절 (0816 밤)
- **4팔 절제실험** (ablation_plan_0816.md, 전문가 검토 대기): 감지/대피/캡 분해
- **캡 도출식**: d_safe = v·τ + v²/2a + margin ≤ D_h; τ≈1.5s, a≈3.5 대입 시
  4.2→9.6m, 3.0→5.8m — 사다리 실측 경계(8~11m)와 일치 = 모델 검증
- **통계**: 충돌률 + Wilson 95% CI 전면, Fisher는 보조 (8/8 vs 0/10 = 2.3e-5)
- **페이지 압축안**: Intro 0.6 / RW 0.35 / Method 1.4 / Setup 0.8 /
  Results 2.3 / Concl 0.2 / Refs 0.8 ≈ 6.5 → 7p (1p 초과비 각오)
- 카메라 사망→신호 대기 관찰은 본문에서 각주/부록으로 강등
- Exposure 적분 정의: E_f = ∫ v(t)dt (고장~MRC 도달), 275m→58m
