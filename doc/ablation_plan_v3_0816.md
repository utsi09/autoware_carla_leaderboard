# 절제 실험 계획서 v3 — 최종 실행판 (전문가 2차 피드백 7건 반영)

## v2 → v3 변경 요약

| # | 지적 | v3 반영 | 구현 확인 |
|---|------|---------|----------|
| 1 | A1 중앙값 추정 폐기 → 섀도 감지기 | 4팔 모두 t_h = **t_detect + 3.0 s** (A1은 감지기 로그 전용, MRM 미연결) | ✅ 이미 충족: mrm-off 팔도 cdr이 "점수만 내는" 수동 모드로 상시 기동 중 (코드 확인). 발사기는 cdr 점수가 supervisor와 동일 임계를 넘는 순간을 t_detect로 삼음 — 4팔 동일 로직 |
| 2 | fault RNG 미고정 | 시드 항목에 **fault_seed** 추가. 자이로 노이즈는 agent의 np.random(gauss random-walk) — 케이스 시작 시 `FAULT_SEED` env로 np.random.seed 고정 → **동일 고장 파형 재현**. (파형 사전 생성·리플레이는 2단계 옵션 — 시드 고정으로 동일 실현 보장되면 생략) | agent 노이즈 소스 확인 완료 (np.random.normal 3곳) |
| 3 | 라틴방격 불요 → 자리 균형 랜덤 순서 | 10시드 × 4팔, 각 팔이 실행순서 1~4번 자리에 2~3회씩 오도록 제약 랜덤화, 실행 전 freeze (seeds.csv에 순서 포함) | 오케스트레이션 스크립트에서 고정 |
| 4 | jitter ±0.3 → ±0.2 m | 횡방향 섭동 **±0.2 m** (분산 축소; n=10에서 경계 근처 severity 요동 방지) | 인젝터 스폰 함수 파라미터 |
| 5 | 20 Hz 폴링 → CARLA 물리 틱 동기 | `world.on_tick` 콜백으로 **매 물리 프레임** 기록: sim_frame, sim_time, ego/walker 좌표·속도, surface_gap → 케이스별 CSV. 영상·충돌 이벤트와 frame ID로 정렬. 5 cm 정밀도 주장 안 함 | 인젝터 관찰 루프 교체 |
| 6 | 통계 | **사전 지정 primary contrasts 2개만 추론적**: A1↔A4 (전체 정책 효과), A3↔A4 (명시 캡 증분). **exact McNemar** (n=10 discordant 기대치 명시: 8:0→p.0078, 5:0→p.0625). A1↔A2, A2↔A3는 기술적/기전 분석. 본체는 충돌률+Wilson CI+쌍대 불일치표 | 분석 스크립트 |
| 7 | exposure 2축 분리 | **E_d** = ∫v dt (고장~MRC, 열화 이동 노출) + **T_clear** = 차선 점유 해소 시간 (footprint가 주행차선을 벗어난 시각 − t_detect; A2는 "not cleared within horizon"). 기대 결과표: A2 = 충돌↓·이동최소·차선점유 지속 / A3·A4 = 충돌↓·이동중간·차선 반환 — stop vs evacuation 트레이드오프가 논문 척추 | 러너가 이미 lane_overlap_m·lane_block_pct 기록 — T_clear는 물리틱 CSV에서 산출 |

## 고정 설계 (v2에서 유지)

- 4팔: A1 native continuation / A2 detection-triggered stop /
  A3 uncapped evacuation / A4 speed-constrained evacuation (3.0)
- 발사: 행동 독립, t_detect+3.0 s에 에고 전방 8 m 차선 우측 끝 스폰.
  정지 상태여도 발사. 무조우 제외 없음 (시뮬레이터 실패만 동일 시드 재실행)
- 시드 S01~S10: {fault_t(11~44 s), walk_speed(2.5×5/3.0×5 블록 랜덤),
  lateral_jitter(±0.2 m), carla_seed, **fault_seed**, walker_seed}
- 판정: primary = 에고 충돌센서 원장(RAW-HIT), consistency audits =
  워커 운동학·최소간격·영상 육안 (ID 프로토콜)
- 캡 수식: d(4.2)=8.82 m, d(3.0)=5.79 m (d_m=0); 3.0 = v_max(≈3.89) 아래
  **보수적 캡** (enforced upper bound — 실측 준수 확인 후 이 표현만 사용);
  기호 D_avail
- A1 sanity check: 섀도 감지기 CPU 오버헤드가 native 거동에 영향 없음 확인
  (감지기 on/off 각 1케이스 v(t) 프로파일 비교)

## 실행 절차

1. **구현** (~1.5 h): 인젝터 시간 트리거(+cdr 점수 구독) / FAULT_SEED /
   물리틱 CSV / jitter 파라미터 / seeds.csv + 오케스트레이션 스크립트
2. **스모크** (~1 h): S01로 4팔 각 1회 — 발사 시각·고장 파형·조우 기하가
   팔 간 동일한지 로그 대조 + A1 sanity check
3. **본 캠페인** (~6 h): 40케이스, 자리 균형 순서, 케이스별 CARLA 재기동
4. **분석·산출**: 4팔 표 (충돌률+CI, E_d, T_clear) + v(t) 프로파일 그림
   (A3 자연감속 vs A4 캡) + exact McNemar (primary 2개) + 영상 40건 육안 대조

## 스모크 통과 기준 (사전 고정)

- 같은 시드에서 4팔의 고장 파형 첫 20샘플 일치
- 4팔의 t_detect 차이 < 0.3 s (같은 파형이므로 근접해야 정상)
- 발사 시 보행자-에고 상대 기하 기록 확인 (전방 8±0.2 m)
- A1 감지기 on/off v(t) 차이 < 0.05 m/s RMS

## 이 계획으로 답하는 리뷰 공격

- "그냥 느려서 안 박은 것" → A2/A3가 분해 (감지·정지·대피·캡 증분)
- "같은 외란이었나" → 동일 시드 + 동일 고장 파형 + 자리 균형 순서
- "baseline이 실패하게 타이밍을 골랐나" → 행동 독립 시간 트리거
- "n=10 통계 과장" → primary contrast 2개 사전 지정 + exact 검정 + CI 정직 공개
- "왜 3.0인가" → 정지거리 모델 역산 v_max 아래 보수적 캡 + 사다리 경계로 검증
