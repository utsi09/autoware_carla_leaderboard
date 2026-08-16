# 전체 실험 캠페인 종합 문서 — 전문가 검토용
(2026-08-16 밤 기준. 기획 의도 / 방법론 / 주요 코드 / 결과 / 알려진 문제를
실험 블록별로 기술. 목적: 외부 전문가가 설계 결함을 지적하면 해당 블록을
수정 재실험할 수 있게 하는 완전한 기록)

---

## 0. 연구 목적과 시스템

**질문**: 자율주행 센서 고장 시, "고장 감지 → 위험 최소화 기동(MRM)으로
갓길/주차장 대피"가 순정 대비 안전성·임무성에 주는 효과는?

**시스템 구성** (fs_ws 워크스페이스):
- `cdr_monitor` (BT 기반 동적 FTTI 감시): 센서별 건강 점수(0~1)를
  `/monitor/scores`(DiagnosticArray)로 발행. 감지기 3종(타임아웃/품질/물리).
- `mrm_supervisor`: 점수 구독, 임계(upper 0.7/lower 0.3)로 상태 전이
  NORMAL→MRM_MOVE(갓길/주차 후보 비용 선택)→MRM_PARKED/DEFER.
  v4.9k+: MRM 이동 중 속도 상한 발행
  (`/planning/scenario_planning/max_velocity_candidates`, sender 병합).
- Autoware 연결: diagnostic_graph_aggregator 그래프에 유닛 주입.

**무대**: CARLA 0.9.16 (호스트) + AWCL(TUMFTM) 브리지/리더보드/오토웨어
0.39.0 (rocker 컨테이너, 레포는 동일 경로 마운트). Town07,
제한속도 15 km/h(4.2 m/s). 케이스마다 CARLA 완전 재기동
(CARLA_RESTART_EVERY=1) — 케이스 간 상태 독립.

**고장 모델 v4.6** (`aw_e2e.py` 에이전트 내 주입, 코드 라인은 grep 기준):
- cf 카메라 사망 / cn 카메라 노이즈(가우시안 픽셀) / lf 라이다 사망
- lso 라이다 희박화(물리 모델: 포인트 드롭) / lcl 라이다 클러터
- gn GNSS/자이로 노이즈(np.random.normal, v5에서 전용 RNG로 교체)
- gm 1차 Gauss-Markov 상관 편향(멀티패스형) / imn IMU 노이즈 / gb 블랙아웃
- 트리거: 주행 시작 후 t초 (케이스별 `random.Random(f"{fault}/{sev}/{npc}/{rep}")`
  로 결정적 — 재현 가능), `--t`로 명시 고정 가능
- 심각도 low/mid/high (cf/lf/nf 등은 무심각도)

**공통 러너** (`experiments/experiment_runner.py`, ~1100줄):
- 케이스 = {method, fault, sev, npc, rep, t}. method: ours(슈퍼바이저) /
  baseline(같은 감지, Autoware 정지 MRM) / mrm-off(관찰: cdr 수동 기동,
  supervisor 더미 — 진단 그래프 STALE 잠금 방지)
- 저지: ROS 구독으로 결과 판정 — SHOULDER_SUCCESS / PARKED_SUCCESS /
  AW_COMFORTABLE_STOP_DONE / AW_EMERGENCY_STOP_DONE / HAZARD_COLLISION /
  HAZARD_STOPPED(정지 60 s+) / HAZARD_SURVIVED(고장 후 360 s 무사고) /
  CARLA_DIED / TIMEOUT
- CSV 기록: 결과, 정지 좌표, 차선 점유(lane_overlap_m, lane_block_pct),
  감지 지연(det_latency_s), 고장 상태 주행거리(deg_dist_m), 공식 충돌
  (collisions, collision_types — **자연 종료 시에만** 기록됨: 함정 §7)

---

## 1. 본 캠페인 매트릭스 (v3~v4.8, 총 ~1,131 유효 케이스)

**기획**: 고장 8종 × 심각도 × 교통밀도(none/def/agg) × 방법(ours/baseline)
× 반복 → 대피 성공률·감지 지연·정지 위치 분포.

**방법**: 위 러너로 배터리 스크립트(launch_v*_chain.sh) 직렬 실행.
크래시 케이스는 재시도 체인으로 재수집(33행 대체).

**결과 요약** (merged_final.csv):
- cf: ours 갓길 16/45, baseline 전량 차선 내 정지
- cn: ours 갓길 25/90 / gn: ours 갓길 41+주차 1/90 (gn-mid가 갓길 주력:
  40/45, gn-high는 42/45 컴포트 정지 — 심각도가 행동 결정)
- lso-mid: 의도적 계속 주행(위험 아님 판단) — deg_dist 140 m
- 노출 지표: 고장 상태 주행거리 순정 240~275 m vs ours 33~58 m vs
  차선정지 9~18 m

**알려진 문제/교훈**:
- (해결) **신호등 카운팅 버그**: 맵 주석이 병렬 차선에 regelem 미부착 →
  경로 신호등 수 오계산 → 비용함수가 원거리 주차장 선택. 수정: 정지선
  regelem 클러스터링(35 m)→교차로 중심, 경로 25 m 근접 카운트
  (`map_model.py`). **오염된 cn/cf/gn 450케이스 전량 재실험 완료**.
- (미해결) 이 매트릭스의 "충돌 0" 주장은 §7 원장 도입 이전 데이터 —
  보행자 주입이 없는 케이스라 위험은 낮지만 원장 기준 재검증은 안 됨.

## 2. 순정(무감시) 프로브

**기획**: 감시 없는 순정이 고장 상태로 얼마나 오래/멀리 달리는가.
**방법**: mrm-off 모드(개입 없이 관찰), 고장 7종 각 2~4케이스.
**결과**: cf 238 m / cn 240 m / gn 251 m / lso 264 m / lcl 275 m 주행
(사실상 완주) — "무감시=전 구간 노출"의 근거. imn만 71 m(자체 이상).

## 3. 엣지케이스 주입기 진화 (hazard_injector.py, v4.9a→v5)

**기획**(사용자 설계): 보행자 돌발/정지 장애물/갓길 점유 3종을
LB 컨테이너 독립 프로세스로 주입 (에이전트/러너 무수정, tl_v2x_relay 패턴).

**실패와 수정의 연대기** (모두 실측·사용자 적발 기반):
1. 보도 스폰 → 가드레일 밖 풀밭 허수아비 → 차선 우측 끝(+0.5 m) 스폰
2. 워커 컨트롤 씹힘(12 s 마네킹) → 1 s 재명령 + 걷기 시작 검증(>1 m/s)
3. 타이밍 스폰 조우 실패 → 경로 길목 고정 트리거(리더보드 XML 방식)
4. argparse가 음수 좌표 삼킴 → `--spec=` 등호형 (갓길 블로커 전멸 원인)
5. CARLA get_actors()가 외부 클라이언트에 빈 목록(**미해결 근본 원인**)
   → 에고 위치를 ROS `/localization/kinematic_state`로 (y부호 반전)
6. 측면 충돌 불공정("옆구리 박기") → 걷기 검증 + 리드 보정
7. 저속 MRM 비교용: 게이트 속도 파라미터화, 무장(arm) 발사,
   횡단 12 m 후 정지(늦은 접촉 오염 방지)
8. v5(절제실험): **시간 트리거**(t_detect+3 s, 속도 불문), 지터 고정값,
   물리 틱 간격 CSV, cdr 점수 구독 섀도 감지

## 4. 거리 사다리 (한계 거리 곡선)

**기획**(사용자 설계): "거리를 조절해가며" — 몇 m 앞 돌발까지 회피 가능한가.
**방법**: 무고장 순정, 스폰거리 {14,11,8,6,5} m × 반복(최종 n=4/거리),
공정 기하, 판정은 §7 원장.
**결과**: 14·11 m 회피 100% / 8·6·5 m 충돌 100%. 정지거리 모델
d=vτ+v²/2a (τ≈1.5 s, a≈3.5) → d(4.2)=8.8 m — 실측 경계(8~11 m)와 일치.
**의미**: 8 m 선택이 자의적이지 않음을 증명 + 속도→경계 물리의 검증.

## 5. 실명(lso-high) 사다리

**방법**: 라이다 완전 열화 순정, 같은 사다리.
**결과**: 14·11 m — 조우 전 도로 한복판 동결(빈 포인트클라우드 프리즈),
8 m 이하 — 충돌. "실명차는 서 있거나 친다".

## 6. 8 m 경계 × MRM 비교 (구판 — §8 재실험으로 대체됨)

**기획**: 고장 상태에서 8 m 돌발 시 저속 MRM vs 순정.
**시행착오 기록** (재현 방지용):
- cf(카메라 사망) 선정 실패: 순정이 신호등을 못 읽어 교차로 영구 대기
  → 조우 불성립 → gn으로 교체
- gn-high 선정 실패: 42/45가 컴포트 정지(이동 없음) → gn-mid로
- 속도 캡 2.5/3.0 발행이 재출발 차단: 원인 = `max_velocity` **출력** 토픽
  직접 발행이 셀렉터와 경합 → **candidates 입력** 토픽으로 수정(해결)
- MRM 정지 직후 인젝터 ROS 리스너 사망 → 무근거 '회피' 오판(§7) →
  워치독 재시작

## 7. 충돌 판정 시스템 재구축 (v4.9v) — 본 캠페인 최대 사건

**사고**: 워커 부착 충돌 센서가 CARLA에서 **한 번도 발화하지 않음**
(공식 충돌 확정 케이스에서도 침묵 — 하루치 데이터로 입증). 여기에
리스너 사망으로 간격 기록까지 소실 → 순정 팔 "회피" 대량 오판.
**사용자가 영상으로 적발** → 해당 데이터 전량 폐기.

**재구축** (현행):
1. **Primary ground truth**: 리더보드 판정기(CollisionTest)의 에고 부착
   `sensor.other.collision` 콜백에 실시간 파일 기록 패치
   (`atomic_criteria.py` → `collision_live.log`, "RAW-HIT <actor>" 즉시).
   조기종료·강제킬 무관. 종점 기둥(static.pole) 스침은 별도 분류.
2. Consistency audits(독립 아님 — 동일 물리엔진): 워커 운동학 이상
   (속도>4.5 또는 1 s 점프>5 m; 실측 임팩트 12~28 m 튕김. 초기 임계
   2 m는 보행 정상속도 3 m/s 오탐 — 상향 이력 있음), 간격 스트림, 영상.
3. **사람 육안 대조 프로토콜**: 영상마다 [A]~[BA] ID + 기계 판정 세트
   전달 → 사용자 판정과 대조(verdict_review.csv). 전 케이스 일치 확인.

**러너 라벨의 함정** (분석 시 필수 주의):
- `HAZARD_COLLISION` 라벨은 종점 구조물(layout) 접촉 포함 — 원장으로 구분
- `HAZARD_STOPPED`는 충돌 후 정지를 포함할 수 있음 — 라벨만으로 판정 금지
- 공식 인프랙션은 자연 종료 시에만 저장 — 조기종료 케이스 공백≠무충돌

## 8. 재실험 캠페인 (50케이스, 원장 기준 — 현행 확정 수치)

**기획**: 판정 시스템 검증 후 보행자 조우 전 실험 재실행 (사용자 지시).
**방법**: §4·§5 사다리 + 8 m A/B팔, 전 케이스 RAW-HIT 원장 + 물리 오라클
+ 영상 육안. **결과**:
- 무고장 사다리(n=4/거리): 14·11 m 회피 4/4 / 8·6·5 m 충돌 4/4·4/4·4/4
- 실명 사다리: 동결 4/4 / 충돌 6/6
- 8 m 조우: **우리 저속 MRM(3.0) 순항 8/8 회피**(+갓길 완수),
  감속 과도구간(고장 직후 3.5~3.8 m/s) 2/2 충돌 — 잔존 위험창 발견,
  **순정(gn-mid, 4.2) 0/10 (10/10 충돌)**

## 9. 절제 실험 v3 (전문가 2회 검토 반영, 실행 중)

문서: `doc/ablation_plan_v3_0816.md` (+1·2차 피드백 전문 반영 이력).
핵심: 4팔(A1 native / A2 detection-stop / A3 uncapped evac / A4 capped)
× 동일 시드 10개(고장 파형까지 FAULT_SEED 고정), 행동 독립 시간 트리거
(t_detect+3 s, 섀도 감지), 자리 균형 순서, E_H(고정 지평 20 s)+T_clear
(우측중도절단), exact McNemar primary 2개(A1↔A4, A3↔A4).
시드 테이블: `experiments/seeds_ablation.csv` (freeze 완료).
현재: S01 스모크 4케이스 진행 중 → 통과 기준(파형 체크섬 일치,
Δt_detect≤2틱, 기하 8±0.2 m, A1 sanity) 확인 후 본 40케이스.

## 10. 주요 코드 포인터

| 파일 | 역할 |
|---|---|
| `experiments/experiment_runner.py` | 케이스 기계·저지·CSV·프로세스 수명 |
| `experiments/hazard_injector.py` | 위험 주입기 v5 (시간 트리거·오라클·틱 로그) |
| `src/tum_agents/autoware_agent/aw_e2e.py` | 센서 파이프+고장 주입(전용 RNG) |
| `src/external/scenario_runner/.../atomic_criteria.py` | RAW-HIT 원장 패치 |
| `~/fs_ws/src/cdr_monitor/` | 감지기 (점수 발행 /monitor/scores) |
| `~/fs_ws/src/mrm_supervisor/supervisor.py` | 상태기계·후보 비용·속도 캡 |
| `experiments/seeds_ablation.csv` | 절제 시드 freeze |
| `experiments/results/collision_live.log` | 충돌 원장 (원시) |
| `experiments/results/verdict_review.csv` | 사람-기계 판정 대조 |

## 11. 미해결·한계 (정직 목록)

1. CARLA 외부 클라이언트 actor 목록 공백 — 근본 원인 미상 (우회 중)
2. 단일 맵·단일 제한속도·발사 회랑 2곳 — 일반화 한계
3. §1 매트릭스의 무충돌 주장은 원장 도입 이전 (보행자 없음이라 저위험)
4. 감속 과도구간 위험창 — 시스템 한계이자 FTTI 논거
5. 임시 설정 원복 미완: CDR_DEMO_NO_ERROR 등 (논문 전 freeze 커밋 필요)
6. min-gap 상수 1.25 m는 횡 접근 기준 — 종방향 접근 시 과대평가
   (v5 틱 로그로 재계산 가능)
7. 워커 명령 3.0 vs 실측 1.1~1.3 m/s 괴리(스폰 직후 측정) — v5에서
   시드별 명령 속도 고정으로 통제, 실측 속도는 틱 로그로 보고 예정
