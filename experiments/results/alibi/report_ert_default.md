# Alibi Detect Online MMD 대조군 (센서별 동일 알고리즘)

기준: 무고장 짝수 rep, 시험: 무고장 홀수 rep(오탐) + 고장 런. 검출 = 주입 후 is_drift 연속 2스텝. 지연 = 시뮬 초.

| 센서 | 고장 | 세기 | n | 검출 | 중앙 지연 (s) | 주입 전 오탐 |
|---|---|---|---|---|---|---|
| camera | cn | high | 5 | 5/5 | 0.3 | 5 |
| camera | cn | mid | 5 | 5/5 | 0.2 | 5 |
| camera | nf | - | 3 | 0/3 | – | 3 |
| gnss | gb | mid | 5 | 0/5 | – | 5 |
| gnss | gm | high | 5 | 5/5 | 0.1 | 5 |
| gnss | gm | mid | 5 | 5/5 | 0.2 | 5 |
| gnss | gn | high | 5 | 5/5 | 0.2 | 5 |
| gnss | gn | mid | 6 | 6/6 | 0.2 | 5 |
| gnss | nf | - | 4 | 0/4 | – | 4 |
| imu | imb | high | 5 | 5/5 | 0.1 | 5 |
| imu | imb | mid | 5 | 5/5 | 2.2 | 5 |
| imu | imd | high | 6 | 6/6 | 1.2 | 5 |
| imu | imd | mid | 5 | 5/5 | 0.1 | 4 |
| imu | imn | high | 5 | 5/5 | 0.1 | 4 |
| imu | imn | mid | 5 | 5/5 | 0.2 | 4 |
| imu | nf | - | 4 | 0/4 | – | 4 |
| lidar | lcl | high | 5 | 5/5 | 0.1 | 5 |
| lidar | lcl | mid | 5 | 5/5 | 0.2 | 4 |
| lidar | lso | high | 5 | 5/5 | 0.3 | 5 |
| lidar | lso | mid | 5 | 5/5 | 0.3 | 5 |
| lidar | nf | - | 3 | 0/3 | – | 3 |
