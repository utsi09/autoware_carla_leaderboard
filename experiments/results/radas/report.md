# RADAS ROS2 대조군 (이식) — 센서별 1런, 5런 (2026-11-09 16:04–16:27, def 교통, rep 50, MRM off)

원본: autonomymobilitylab/radas_ros2 `firmware/src/webUI/{lidar,camera,imu,gps}_diagnostics.py` — 1 s 주기 평가, 2 s 창 메시지 수 → Hz, 마지막 메시지 >2 s(GNSS 5 s) STALE, Hz/기대 ≤0.70 ERROR, <0.90 WARN. 내용(점군·픽셀·IMU 값·위치) 검사 없음. GNSS 는 Septentrio 수신기 상태(위치 모드·간섭·스푸핑 플래그) 추가 — 시뮬 GNSS 에는 없음.
이식(`experiments/radas_diag_port.py`): 토픽 /sensor/lidar/front, /sensing/camera/traffic_light/image_raw, /sensing/imu/imu_data, /sensing/gnss/pose_with_covariance; Hz 는 /clock(시뮬 시간) 기준; 기대 Hz 는 주입 전 20 s 중앙값(전부 20.0 Hz). 판정 = ERROR 또는 STALE.

| 고장 | 센서 | RADAS 판정 | 첫 경보(주입 후, 시뮬 s) | 비고 |
|---|---|---|---|---|
| LiDAR death (lf) | lidar | **STALE** | 3.8 | 토픽 침묵 → 2 s 타임아웃 (+1 s 평가 주기) |
| Camera death (cf) | camera | **STALE** | 2.4 | 토픽 침묵 |
| LiDAR sparsification high (lso) | lidar | OK 240/240 s | – | 점이 사라져도 메시지 주기는 그대로 |
| GNSS position noise high (gn) | gnss | OK 195/195 s | – | 위치 값만 흔들림, 주기 불변 |
| IMU gyro noise mid (imn) | imu | OK 236/236 s | – | 값만 흔들림, 주기 불변 |

오탐: 5런 주입 전 구간(22–23 s × 4센서) 전부 OK. 제안 모니터(같은 조건, 8월/11월): lf·cf 1.0–1.4 s, lso-high 1.2 s, gn-high 1.2 s, imn-mid 3–5 s 검출.
결론: RADAS 류 스트림 진단은 "끊김" 2종만 잡고 "값은 오지만 틀린" 열화 3종은 구조상 못 본다. 비교 표에 B0(Autoware 진단) 옆 열로 추가 가능. n=1/조건이므로 경향 확인용.
