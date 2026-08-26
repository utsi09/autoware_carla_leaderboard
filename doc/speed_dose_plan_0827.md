# Speed-Dose 인과 실험 계획서 (사전등록, 2026-08-27)

## 배경 및 목적
외부 심사(0827)의 핵심 지적: 절제 A3(무캡 대피 10/20) ↔ A4(3.0 m/s 캡 대피 11/20,
McNemar p=1.0)는 속도 상한의 증분 효과를 입증하지 못했고, 그 원인은 조우 발사가
t_detect+3 s(감속 과도구간)라서 **캡의 목표 상태가 조우 순간 아직 성립하지 않았기
때문**이다. 본 실험은 "같은 대피 정책·같은 고장·같은 주입기에서, 상한이 실제로
성립한(정착) 상태의 실주행 속도만 달리했을 때 회피/충돌 경계가 체계적으로
이동하는가"(dose–response)를 검증한다.

## 설계 (사전 고정)
- **매트릭스**: 3 속도 캡 × 4 스폰거리 × 10 시드 = **120 런** (paired, 시드 내 비교).
- **속도 캡** (전 팔 동일 인터페이스 — supervisor `mrm_move_speed_limit`,
  env `MRM_MOVE_SPEED`; VelocityLimit 발행 경로 동일, 값만 상이):
  - S1 = 4.2 m/s (도로 제한 15 km/h≈4.17과 사실상 동치인 고캡 대조 — 절제 A3의
    기본값과 동일 값·동일 경로)
  - S2 = 3.6 m/s
  - S3 = 3.0 m/s (논문 정책값 — 절제 A4와 동일)
- **스폰거리**: 6 / 7 / 8 / 9 m (에고 전방, waypoint 기준 차선 우측 끝 스폰,
  기존 spawn_ped_xy 기하 그대로).
- **고장/조건**: gn-mid, --t 25(고정), npc none, FREEZE_TL=1,
  DETECT_CAP=capability/localization — 절제 v4 프로토콜과 동일.
- **시드**: seeds_speed_dose.csv의 S12~S21 10종(절제 v4와 동일한
  walk_speed/jitter/fault_seed/walker_seed — 조우 이질성 재사용, FT만 25로 통일).
- **트리거 (정착 발사)**: hazard_injector `s<lo>x<hi>` 토큰 —
  supervisor 상태가 **MRM_MOVE**이고 실측 속도가 아래 밴드에 **1.0 s 연속**
  머무는 순간, 에고 현 위치 전방 D m에 발사. 시간 기반(t3.0) 발사 금지.
  - S1: [3.90, 4.45] / S2: [3.50, 3.70] / S3: [2.90, 3.10] m/s
- **조작 점검(채택 규칙)**: ① 420 s 내 미발사(밴드 미도달·MRM 미진입 포함) 또는
  ② 스폰 직후 첫 틱 속도가 밴드±0.15 밖이면 **MANIPULATION_FAIL** — 해당 런은
  기각하고 동일 조건 재실행(런당 최대 총 3회 시도). 이는 결과(충돌 여부)와 무관한
  전조건 검증이므로 optional stopping이 아니다.
- **실행 순서(사전 고정, 1차 종결점 선충전)**: P1: 8 m×{4.2,3.0}×10시드(교차 순서)
  → P2: 8 m×3.6 → P3: 7 m×3속도(시드별 회전) → P4: 9 m → P5: 6 m.
- **개발 시드**: D00 (ws 3.0, jit 0.0, fseed 999, wseed 1999) — 정착 트리거·회랑
  검증용 스모크 전용, **본 분석에서 제외** (절제의 S01 제외와 동일 규약).
  FT=25에서 4.2 팔의 정착(≥3.9 유지)이 대피 회랑 안에서 성립하지 않으면 FT를
  개발 단계에서 조정해 **본 캠페인 전체에 동결**한다(조정 사실은 본 문서에 추기).

## 종결점 (사전 지정)
- **1차**: 8 m에서 S1(4.2) vs S3(3.0)의 paired 충돌 차이 — exact McNemar
  (n=10 시드). 방향 가설: S3 충돌 ≤ S1.
- **2차**: 속도×거리 경계표의 단조성(용량-반응) — 각 속도의 회피/충돌 경계 거리가
  4.2 → 3.6 → 3.0 순으로 안쪽 이동하는가. 기술통계 + Wilson 95% CI.
- **탐색적**: 3.6 관련 나머지 대비, 첫 틱 속도 분포(조작 점검 보고).

## 판정 프로토콜 (v4.9v 원장 규약 승계)
러너 outcome 라벨은 **불신**(HAZARD_COLLISION 라벨 버그 기지) — 진실원은
① encounter_metrics.csv의 CONTACT-SENSOR/CONTACT-PHYSICS/CONTACT-GAP(≤0.30 m),
② tick_*.csv min_gap 궤적, ③ 런별 자가녹화 영상(videos_sd/, 경계 사례 전수 확인).
충돌 = CONTACT-* 중 하나라도 성립. 회피 = CLEAR + min_gap 기록 존재.
NO-ENCOUNTER는 채택 불가(재실행).

## 정지 규칙
120 런(채택 기준) 고정 — 결과를 보고 표본을 늘리거나 줄이지 않는다.
재실행은 MANIPULATION_FAIL/인프라 실패(CARLA_DIED·SETUP_FAIL)의 동일 조건
대체만 허용된다.

## 자료 산출물
speed_dose_progress.csv(런 장부), tick_sd-*.csv, encounter_metrics.csv(태그 sd-*),
ftrace_sd-*.csv, videos_sd/*.mp4, speed_dose.log.
