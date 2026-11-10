# final_fig — 최종 논문 반영용 그림·표·데이터 (2026-11-10 22:40 기준)

다른 세션/다른 작업자가 **이 폴더와 `experiments/analysis/`만 보고** 논문 결과장을 쓸 수 있도록 정리했다.
원자료(bag·GT·live csv, 56 GB)는 이 PC `experiments/results/`에만 있고 깃허브에는 **파생표·그림·보고서만** 올라간다.
모든 그림 스타일: IEEE/MATLAB 고전(Times 세리프, 박스 축, 안쪽 눈금, 격자 없음, MATLAB 팔레트, 검은 마커 테두리). 그림 안 글자는 영어.

## 1. 그림 목록

| # | 파일 | 내용 | 자료·표본 | 생성 스크립트 | 비고 |
|---|---|---|---|---|---|
| F1 | `fig_noise_sweep_v5b_en.{png,pdf}` | **고장 세기 ↔ 감시 점수 ↔ 실제 성능** 4열: (a) LiDAR 성김 T, (b) LiDAR 강우 감쇠 R(동등 시정 m), (c) IMU 자이로 잡음 σ, (d) 카메라 가우시안 잡음 σ. 위 행 = 감시기 점수 중앙값, 아래 행 = Autoware 인식 재현율(0–26/26–50 m)·EKF 오차·신호등 인식 성공률 | 순정(감시기만, MRM off) 세기 사다리. 채우기 B 완료 후 **수준당 10런**(lso 7수준, lcl 7수준 rep 40–49, imn 4수준, cn 4수준) + 캠페인 운영점(mid/high, 1런 = 흰 마커) | `analysis/fig_noise_sweep_v5b_en.py` (국문판 `fig_noise_sweep_v5b.py`) | 핵심 기여 그림. (d) 아래 행 = 런 단위 "초록 신호에 출발 성공" 비율(`stock_outcomes.csv` missed_green==0), **def 교통·t=10 주입 사다리 런만**(캠페인 mid/high 는 27 s 주입·교통 3종이라 섞지 않음). σ 5/10/20/30/45 각 10런 → 0.9/0.3/0.0/0.0/0.0; **σ 15·7 각 10런 추가 중**(`cn_fill_15_7.sh`, 11/11 새벽 자동 재생성·푸시) |
| F2 | `fig_noise_sweep_rest_sensor.{png,pdf}` | F1과 같은 형식, 나머지 센서 고장(라이다/카메라 사망, 클러터 mid/high 등) | 11월 순정 매트릭스 수준당 ≈45런 | `analysis/fig_noise_sweep_rest.py` | 보조 |
| F3 | `fig_noise_sweep_rest_nav.{png,pdf}` | F1과 같은 형식, 항법 고장(GNSS 위치 잡음·상관 바이어스·단절, IMU 바이어스·램프) | 동일 | 동일 | 보조 |
| F4 | `fig_outcomes_3panel.{png,pdf}` | **대응 결과 분포** (a)(b) 논문 본 실험(제안: 계속 주행/대피/정지), (c) 순정 Autoware(정지·정체·충돌; 빗금 = 순정에만 있는 범주) | 조건당 45런 짝 맞춤 (교통 3종 × rep 0–14) | `analysis/fig_outcomes_3panel.py` | 행 값은 사용자 확정(아래 4절 ③) |
| F5 | `fig_detector_matrix.{png,pdf}` + `reports/detector_matrix.md` | **검출기 비교 행렬** 19 고장조건 × 9 검출기(Autoware 진단, Won 2023, Zhang 2024, Lee 2022, Yu 2021, Huang&Su, RADAS, Alibi Online MMD, 제안). 셀 = 검출 k/n (중앙 지연 s) | 항법·사망 열 셀당 45런(bag 재생), 비전 열 5런(원시 2 Hz 기록), Alibi 5–6, RADAS 1 | `analysis/fig_detector_matrix.py` | 무고장 오탐: 표시된 모든 검출기 0 |
| F6 | `fig_vision_fdi.{png,pdf}` | 비전 검출기 상세(Won/Zhang/Lee vs 제안): 조건별 검출률·지연 | 셀당 5런 | `analysis/fig_vision_fdi.py` | F5의 비전 부분 확대 |
| F7 | `fig_baseline_fdi.{png,pdf}` | 항법 검출기 상세(Yu/Huang&Su/Autoware 진단 vs 제안) | 셀당 45런 | `analysis/fig_baseline_fdi.py` | F5의 항법 부분 확대 |
| F8 | `fig_encounter.png` | 조우 블록: 제동·정지시간·차체 간격·보행자 접촉(고장 × 팔) | 조우 실험 | `analysis/fig_encounter.py` | 이전 커밋에 설명 |
| V1 | `video/demo_final_cn_imn_4x_small.mp4` | **본심 데모 영상** 1:28, 4배속, 좌 Proposed / 우 Baseline(stock). ① 카메라 잡음 high 같은 시드 r13: 제안 교차로 앞 갓길 대피, 순정 빨간불 무한 대기 ② IMU 자이로 잡음 mid r2: 제안 자기 차로 비상정지, 순정 차선에 굳음. 먼저 끝난 쪽은 회색 정지화면 | 원본 67 MB는 PC `results/videos/demo_final_cn_imn_4x.mp4` | `experiments/case_video.sh`, `stock_case_video.sh`, 합성 `scratchpad/vid/compose_demo3.sh`(PC) | ⚠ 카메라 구간 제안 쪽은 **데모 전용 런타임 파라미터 완화**(`tl_visible_min_score` 0.5→0, `tl_wait_s` 15→0). 논문 수치에는 미사용. 질문 시 "시연을 위해 신호등 배제 규칙만 풀었다" |

폐기/대체된 그림(참고만): `results/figs/fig_lcl_graded*.png`(폐루프 등급 그림, 사용자 지시로 제외), `fig_outcomes_with_stock.png`·`fig_outcomes_stock_panel.png`(F4로 대체), `fig_noise_sweep.png`(F1 이전 판, lcl 열이 구 모델).

## 2. 보고서 (`reports/`)

| 파일 | 내용 |
|---|---|
| `detector_matrix.md` | F5의 표 형태 + 각주 |
| `nav_baselines_report.md` | 항법 베이스라인(Yu 2021 상태 χ², Huang&Su EKF 잔차, Autoware 진단) 재구현·평가 상세, 45런/셀 |
| `vision_baselines_report.md` | 비전 베이스라인(Won 2023 비트맵, Zhang 2024 분포, Lee 2022 CNN) 재구현·평가, 5런/셀, 문턱(nf 짝수 rep 최대) |
| `radas_report.md` | RADAS ROS2(autonomymobilitylab) 이식: 토픽 주기/타임아웃만 봄 → 스트림 소실(라이다·카메라 사망)만 검출(3.8/2.4 s), 성김·GNSS·IMU 잡음 미검출, 오탐 0 |
| `alibi_online_mmd_report.md` | Alibi Detect Online MMD(pytorch) 3 보정: 기본 ERT 문턱 = 전 런 경보(사용 불가), nf 최대값 문턱(a)·창×4/99.5 %(c) = cn·lso-high·imb만 검출 |
| `lcl_severity_calibration_report.md` | LiDAR 강우 세기 추정(v5b): α̂ 감쇠 기울기 → R̂ = exp(a + b·ln α̂), a=7.6573 b=1.6627; 폐루프 재생 대조 max|Δq| 0.0000 |

## 3. 데이터 (`data/`) 와 원자료 위치

| 파일 | 내용 |
|---|---|
| `stock_outcomes.csv` | 순정 매트릭스 케이스별 결말 분류(충돌/순정 MRM/완주/정체/빨간불 대기/굳음 …) + missed_green 등 플래그. 생성 `analysis/stock_freeze.py` |
| `cam_scores.csv` | bag에서 뽑은 감시기 점수 요약(런당 카메라/신호등/위치/라이다/인식/장애물 점수 중앙값). F1(d)·F2가 사용. 저장소 사본 `results/derived/` |
| `tl_acc.csv` | (탐색용, 논문 미사용) 틱 단위 신호등 인식 일치율. GT 'tl' 열은 정지선 트리거 볼륨 안에서만 기록돼 **정차 시간에 좌우**(σ5 는 통과 2 s, σ10 은 적신호 대기 100 s) → 지표로 부적합. `results/derived/tl_approach_acc.csv`(접근 60 m 거리대 판)도 Autoware 가 주행 중 접근 구간에서는 거의 UNKNOWN 만 내고 정지선 도달 후에야 색을 내서(시간 필터) 무고장과 구분 불가, 그리고 무고장 bag 의 traffic_signals 메시지는 역직렬화 실패. 둘 다 `analysis/tl_recog_acc.py`, `analysis/tl_approach_acc.py` 에 남김 |
| `lcl_sev_cfg.txt` | v5b 세기 모델 계수(a, b) — 러너 환경변수 `CDR_LCL_SEV_CFG` 로 주입 |
| `ladder_fill_done.txt` | 채우기 B 완료 셀 목록(154/147; 7셀은 재실행 중복) |

PC 원자료: `experiments/results/live/<tag>.csv`(런당 감시기 요약), `results/gt/<tag>.csv`(20 Hz 정답 궤적+신호색), `results/bags/<tag>/`(mcap, 일부 zstd 압축), `results/results_*.csv`(러너 판정), `results/noise_sweep_batch.log`(사다리 `[live]` 행), `results/stock_matrix.log`(체인 로그), `results/supervisor.log`(감독기 결정).
태그 규칙: `<arm>-<fault>-<sev>-<npc>-r<rep>-<MMDD_HHMM>`; arm ∈ {ours, baseline(같은 감시기+순정 차선 내 MRM), stock(감시기만, MRM off)}; sev ∈ {mid, high, 사다리 값(lso `T:90`, lcl `R:pts`, imn σ, cn σ)}; npc ∈ {def, none, agg}; rep K → TM_SEED=100+K(짝 시드).

## 4. 논문 서술에 반드시 지킬 사용자 결정

1. **핵심 기여 = 고장 세기를 재는 연속 모델**(F1). "이진 검출기로 낮추자"는 제안 금지.
2. **강우 라벨은 물리 강우가 아님**: 브리지 α = 0.01·R^0.6 은 실제 비의 30–40배. 실험 조건명은 "Goodin R = 5 / 25"로 두고, 현실 대응은 **안개 시정(WMO MOR = 3/α)으로 mid ≈ 110 m, high ≈ 45 m, "안개 수준의 감쇠"**. 실제 안개 재현 주장 금지, "1,000/4,000 mm/h" 숫자 쓰지 않음.
3. **F4 행 값은 확정**: lso-high = 대피 44 / 정지 1 (로그 재해석으로 바꾸지 말 것), Camera noise는 mid/high 한 행(0/25/65). 세부 분류 안 된 "Other"는 정지로 계산.
4. 라이다 성김 mid에서 제안이 안 울리는 것은 **설계**(능력 손실 없음 → 개입 없음). IMU σ 0.1도 같은 서술.
5. 그림에 런 수·"→ 나쁨"·패널 안 텍스트 넣지 않기, 범례는 한 박스, x축 라벨은 물리 이름만. 쉬운 말로 설명(사다리/스윕 같은 은어 자제).
6. 검출 지연은 시뮬 시간(det_latency_sim_s). 하드 고장(사망)은 벽시계 1초대라도 시뮬 시간으로 보고.
7. 총 실험 건수(2026-11-09 기준) 3,262런, 채우기 B 완료 후 ≈ 3,416.

## 5. 수치 요약(본문 인용용)

- 감시 점수 ↔ 강우 R: R 1/2/5/10/15/25/40 → 건강도 .931/.865/.772/.697/.652/.583/.538, 장애물 점수 .889/.778/.624/.499/.424/.328/.235. 건강도 0.7 ↔ R ≈ 9.7(시정 ≈ 75 m), 장애물 0.4 ↔ R ≈ 17.
- 감독기 규칙: health = min(perception, loc); 대역 < 0.7 × 10틱, 바닥 ≤ 0.3 × 20틱; 이동 게이트 loc ≥ 0.5, 장애물 ≥ 0.4(5 s 유지 실패 → MRM_DEFER = 차선 내 정지); 후보 비용에 접근거리 25 m, 신호등 경로는 건강한 전방 카메라가 있을 때만.
- 검출기 비교(F5): 제안은 lso-mid(설계) 빼고 전 조건 5/5 또는 45/45, 중앙 1.2–10 s. Zhang은 라이다만, Lee는 카메라만, Yu/Huang&Su는 GNSS·IMU만(GNSS 단절 0/45), Autoware 진단은 IMU·라이다 사망만, RADAS는 스트림 소실만, Alibi(nf 보정)는 cn·lso-high·imb만.

## 6. 남은 일(2026-11-10 22:40)

- [x] 채우기 B 신규 런 반영(cam_scores·stock_outcomes 갱신, lcl glob r4[0-9]) → F1 수준당 10런(11/10 23:30).
- [ ] cn σ15·σ7 각 10런(`cn_fill_15_7.sh`, 약 2 h) → F1 자동 재생성·푸시. 끝나면 (d) 아래 행이 5/7/10/15/20/30/45 7점.
- [ ] 선택: 단계당 15런(C안, +110런 ≈ 9 h)은 사용자 결정 대기.
