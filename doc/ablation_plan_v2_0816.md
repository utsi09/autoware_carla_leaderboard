# 절제 실험 계획서 v2 — 전문가 피드백 전면 반영 (2026-08-16 밤)

## 0. 재정의된 목적 (프레이밍 수정)

"각 요소의 순수 인과 분해"가 아니라 **단계적 정책 절제**:
`native continuation → detection-triggered stop → uncapped evacuation →
capped evacuation` 순으로 각 설계 요소가 **최종 안전성과 노출(exposure)에
주는 incremental effect**를 검증한다.

## 1. 4팔 구성 (명칭 수정)

| 팔 | 정책 | 명칭 |
|----|------|------|
| A1 | 감지 없음, 계속 주행 (4.2) | native continuation |
| A2 | 우리 감지 → 차선 내 정지 | detection-triggered stop |
| A3 | 우리 감지 → 갓길 대피, **캡 없음** | **uncapped evacuation** |
| A4 | 우리 감지 → 갓길 대피 + 3.0 상한 | **speed-constrained evacuation** |

- A3↔A4 비교의 질문: "명시적 속도 상한이 **추가 효과**를 내는가"
  (대피 기동의 순수 인과 아님 — 명칭·해석 모두 이 표현으로 통일)
- "guarantee" 표현 금지 → 실측 상한 준수 확인 시 "enforced upper bound"

## 2. 발사 프로토콜 — **행동 독립 트리거** (핵심 수정)

- **발사 시각 고정**: t_h = t_detect + 3.0 s (시나리오 시드에 고정).
  **에고 속도·상태와 무관하게** 그 순간 에고 현재 위치 기준 전방 8 m
  차선 우측 끝에 보행자 발사. 정지해 있어도 발사.
- v≥2.6 게이트 **삭제**. 무조우 제외 규칙 **삭제** — 각 팔의 정지/감속으로
  생기는 무조우·원거리 조우는 **treatment의 결과**로 그대로 표본에 포함.
- 분석 제외는 진짜 실험 실패만: CARLA 크래시, 스폰 API 실패, 로거 실패,
  초기화 실패 (사유 로그와 함께 동일 시드 재실행으로 대체).
- A1은 감지가 없으므로 t_detect 대신 **동일 시드의 고장 주입 시각 +
  (A2~A4의 중앙값 감지 지연 + 3.0 s)** 를 사용해 벽시계 동등성 확보
  (감지 지연은 cdr 로그에서 시드별 실측 — 계획서 검토 포인트 ①).

## 3. 시나리오 블로킹 (교대 → 블록 랜덤화)

- 시드 S01~S10 사전 생성, 각 시드에 고정:
  {고장 주입 시각(11~44 s 균등 추출), 보행 명령 속도, 스폰 횡방향 섭동
  (±0.3 m), CARLA 랜덤 시드}
- 보행 속도: {2.5 ×5, 3.0 ×5}를 시드에 **블록 랜덤 배치** (순서 교대 금지)
- **같은 시드를 4팔 모두에 실행**: S01:A1,A2,A3,A4 … S10:… = 40케이스
- 기존 A1(0/10)·A4(8/10) 데이터는 **본 캠페인 지지 데이터**로 강등,
  최종 절제표는 동일 시드 40케이스로 작성
- 실행 순서: 시드 내 팔 순서도 랜덤화 (시뮬레이터 상태 드리프트 대비)

## 4. 판정·계측 (표현 및 해상도 수정)

- **Primary ground truth**: 에고 충돌센서 실시간 원장 (RAW-HIT walker)
- **Consistency audits** (독립 오라클이라 부르지 않음 — 동일 물리엔진):
  워커 운동학 이상(속도>4.5 / 점프>5 m), 최소간격, 영상 육안 (ID 프로토콜)
- 간격 샘플링 10 Hz → **20 Hz 이상**으로 상향 (4.2 m/s에서 샘플당 0.42 m
  → 0.21 m; 구현: 인젝터 관찰 루프 주기 축소)
- A3 필수 로그 (팔 공통 적용): v(t_fault), v(t_detect), v(t_walker),
  MRM 후 최고 v, 최소간격 시점 v, planner 참조속도 v_ref(t) vs 실측 v(t)

## 5. 통계 계획 (오류 수정)

- 1차: 팔별 충돌률 + Wilson 95% CI 제시 (n=10: 0/10→0–27.8%,
  8/10→49.0–94.3%, 10/10→72.2–100% — CI 폭을 본문에 정직하게)
- 쌍대 비교: 동일 시드 쌍이므로 **McNemar** (A1↔A4, A3↔A4 등)
- **금지 문장**: "CI가 0을 포함 → 동등/캡=보장". 대체 문장:
  "No additional collisions were prevented by the explicit cap in the
  tested sample" / "comparable observed rates, sample insufficient to
  establish equivalence"
- 결과 해석 매트릭스 사전 등록 (전문가 표 그대로 채택): A2가 좋게 나와도
  실패 아님 — stop=immediate safety vs shoulder=safety+exposure 트레이드오프
  서사로 전환

## 6. 속도 캡 수식 (수치·기호 정정)

- d(v) = v·τ + v²/(2a) + d_m, τ=1.5 s, a=3.5 m/s²
  → d(4.2)=**8.82 m**, d(3.0)=**5.79 m** (d_m=0); d_m=0.8 시 9.62/6.59 m
- D=8 m 역산 최대속도: d_m=0 → **v_max≈3.89**, d_m=0.8 → ≈3.58
  → **3.0은 최대가 아니라 보수적 캡**: "analytically estimated recoverable
  velocity 아래로 보수적으로 선정, ~1.4 m nominal reserve (d_m=0.8 기준)"
- 기호: D_h(감지 지평) 사용 금지 — 자이로 고장은 지각 지평을 줄이지 않음.
  **D_avail (available longitudinal safety distance)** 로 정의: "주어진
  hazard clearance에서 degraded MRM이 유지 가능한 velocity envelope"

## 7. 구현 변경 목록 (실행 전 코드 작업)

1. 인젝터: `dist:<m>:t<arm지연>[:w<보행속도>]` 신규 스펙 — **시간 트리거**
   (속도 게이트 없음), 보행 속도 파라미터화, 스폰 시 에고 속도 로그
2. 인젝터: 간격 루프 20 Hz 상향, v_ref/v_actual 기록 추가
3. 러너: 시드 파일(seeds.csv: fault_t, walk_speed, jitter, carla_seed)
   읽어 케이스별 적용 (env 주입); 시드·팔 라벨을 CSV에 기록
4. A1용 t_h 산출: A2~A4 감지 지연 실측 후 시드별 상수 확정 (§2)
5. 검증 스모크: 시드 S01로 4팔 1회씩 드라이런 → 발사 시각·조우 기하가
   팔 간 동일한지 로그로 확인 후 본 실행

## 8. 규모·일정

- 본 캠페인 40케이스 (+실패 재실행 여유 ~5) ≈ 6시간
- 스모크 4케이스 + 감지 지연 측정 ≈ 1시간
- 산출물: ablation CSV(시드×팔), collision_live.log, 영상 40건(ID 프로토콜),
  4팔 결과 그림 + v(t) 프로파일 그림 (A3 자연감속 vs A4 캡)

## 9. 검토 요청 포인트 (v2)

① A1의 발사 시각 동등화 방법 (중앙값 감지 지연 사용) 타당한가
② 시드 내 팔 순서 랜덤화로 충분한가, 아니면 팔 순서도 라틴방격이 필요한가
③ 스폰 횡방향 섭동 ±0.3 m 폭 적절한가
④ 20 Hz 간격 샘플링으로 충분한가 (물리 틱 동기 필요 여부)
