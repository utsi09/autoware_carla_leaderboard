# 비전 베이스라인 비교 (원시 2 Hz 기록, 36런; 생성 2026-11-09 00:38)

검출기: B0 인지진단, B0 MRM, WON 비트맵, ZH 분포, ZH_near(변형), LEE CNN, 제안. 모든 검출기 1 s 지속 확정, 지연 = 확정 시각 − 주입 시각(시뮬 초). 
문턱: nf 짝수 rep 3런 FP 창 최대값 → WON 0.0469, ZH 0.0387 bit, ZH_near 0.2209; LEE 는 argmax. 오탐 평가: nf 홀수 rep 3런 + 고장 런 주입 전 창.

| 고장 | n | B0 인지진단 | B0 MRM | WON 비트맵 | ZH 분포 | ZH_near(변형) | LEE CNN | 제안 |
|---|---|---|---|---|---|---|---|---|
| lso-mid | 5 | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 5/5 (57–100%) 0.8 s | 2/5 (12–77%) 68.2 s | 0/5 (0–43%) | 0/5 (0–43%) |
| lso-high | 5 | 0/5 (0–43%) | 0/5 (0–43%) | 1/5 (4–62%) 130.4 s | 5/5 (57–100%) 0.9 s | 5/5 (57–100%) 81.6 s | 0/5 (0–43%) | 5/5 (57–100%) 1.2 s |
| lcl-mid | 5 | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 5/5 (57–100%) 0.7 s | 5/5 (57–100%) 76.7 s | 0/5 (0–43%) | 5/5 (57–100%) 1.2 s |
| lcl-high | 5 | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 5/5 (57–100%) 0.6 s | 5/5 (57–100%) 39.6 s | 0/5 (0–43%) | 5/5 (57–100%) 1.2 s |
| cn-mid | 5 | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 5/5 (57–100%) 0.7 s | 5/5 (57–100%) 1.3 s |
| cn-high | 5 | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 0/5 (0–43%) | 1/5 (4–62%) 59.5 s | 5/5 (57–100%) 0.9 s | 5/5 (57–100%) 1.3 s |

## 오탐 (경보가 난 런/창 수)

| 구간 | n | B0 인지진단 | B0 MRM | WON 비트맵 | ZH 분포 | ZH_near(변형) | LEE CNN | 제안 |
|---|---|---|---|---|---|---|---|---|
| nf 보정용(짝수 rep) | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| nf 평가용(홀수 rep) | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 고장 런 주입 전 창 | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## McNemar (제안 vs 각 검출기; b=제안만, c=비교만 검출)

| 고장 | B0 인지진단 | B0 MRM | WON 비트맵 | ZH 분포 | ZH_near(변형) | LEE CNN |
|---|---|---|---|---|---|---|
| lso-mid | b=0 c=0 — | b=0 c=0 — | b=0 c=0 — | b=0 c=5 p=0.062 | b=0 c=2 p=0.500 | b=0 c=0 — |
| lso-high | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=4 c=0 p=0.125 | b=0 c=0 — | b=0 c=0 — | b=5 c=0 p=0.062 |
| lcl-mid | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=0 c=0 — | b=0 c=0 — | b=5 c=0 p=0.062 |
| lcl-high | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=0 c=0 — | b=0 c=0 — | b=5 c=0 p=0.062 |
| cn-mid | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=0 c=0 — |
| cn-high | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=5 c=0 p=0.062 | b=4 c=0 p=0.125 | b=0 c=0 — |

## 런별

| 런 | 결과 | 주입(출발+s) | B0 인지진단 | B0 MRM | WON 비트맵 | ZH 분포 | ZH_near(변형) | LEE CNN | 제안 |
|---|---|---|---|---|---|---|---|---|---|
| vb-cn-high-r30 | HAZARD_STOPPED | 19.0 | — | — | — | — | — | 0.7 | 1.2 |
| vb-cn-high-r31 | HAZARD_STOPPED | 22.0 | — | — | — | — | — | 1.0 | 1.3 |
| vb-cn-high-r32 | HAZARD_STOPPED | 17.0 | — | — | — | — | — | 0.9 | 1.3 |
| vb-cn-high-r33 | HAZARD_STOPPED | 34.0 | — | — | — | — | 59.5 | 0.9 | 1.3 |
| vb-cn-high-r34 | HAZARD_STOPPED | 25.0 | — | — | — | — | — | 0.8 | 1.3 |
| vb-cn-mid-r30 | HAZARD_STOPPED | 45.0 | — | — | — | — | — | 0.7 | 1.3 |
| vb-cn-mid-r31 | HAZARD_STOPPED | 35.0 | — | — | — | — | — | 0.6 | 1.3 |
| vb-cn-mid-r32 | HAZARD_STOPPED | 38.0 | — | — | — | — | — | 0.7 | 1.3 |
| vb-cn-mid-r33 | HAZARD_STOPPED | 42.0 | — | — | — | — | — | 0.7 | 1.3 |
| vb-cn-mid-r34 | HAZARD_STOPPED | 42.0 | — | — | — | — | — | 0.9 | 1.3 |
| vb-lcl-high-r30 | HAZARD_STOPPED | 27.0 | — | — | — | 0.6 | 39.6 | — | 1.2 |
| vb-lcl-high-r31 | HAZARD_STOPPED | 44.0 | — | — | — | 0.9 | 19.9 | — | 1.2 |
| vb-lcl-high-r32 | HAZARD_STOPPED | 40.0 | — | — | — | 0.6 | 34.1 | — | 1.2 |
| vb-lcl-high-r33 | HAZARD_STOPPED | 26.0 | — | — | — | 0.6 | 111.1 | — | 1.3 |
| vb-lcl-high-r34 | HAZARD_STOPPED | 24.0 | — | — | — | 0.9 | 93.4 | — | 1.3 |
| vb-lcl-mid-r30 | HAZARD_STOPPED | 36.0 | — | — | — | 0.6 | 61.6 | — | 1.3 |
| vb-lcl-mid-r31 | HAZARD_STOPPED | 20.0 | — | — | — | 0.6 | 47.1 | — | 1.2 |
| vb-lcl-mid-r32 | HAZARD_STOPPED | 11.0 | — | — | — | 0.9 | 108.9 | — | 1.2 |
| vb-lcl-mid-r33 | HAZARD_STOPPED | 42.0 | — | — | — | 0.7 | 76.7 | — | 1.2 |
| vb-lcl-mid-r34 | HAZARD_STOPPED | 33.0 | — | — | — | 1.0 | 85.5 | — | 1.3 |
| vb-lso-high-r30 | HAZARD_STOPPED | 35.0 | — | — | — | 0.6 | 85.6 | — | 1.2 |
| vb-lso-high-r31 | HAZARD_STOPPED | 26.0 | — | — | — | 0.9 | 78.9 | — | 1.2 |
| vb-lso-high-r32 | HAZARD_STOPPED | 39.0 | — | — | — | 0.6 | 81.6 | — | 1.2 |
| vb-lso-high-r33 | HAZARD_STOPPED | 24.0 | — | — | 130.4 | 0.9 | 97.4 | — | 1.2 |
| vb-lso-high-r34 | HAZARD_STOPPED | 43.0 | — | — | — | 1.0 | 78.5 | — | 33.8 |
| vb-lso-mid-r30 | HAZARD_STOPPED | 43.0 | — | — | — | 0.9 | — | — | — |
| vb-lso-mid-r31 | HAZARD_STOPPED | 33.0 | — | — | — | 0.8 | 54.3 | — | — |
| vb-lso-mid-r32 | HAZARD_STOPPED | 14.0 | — | — | — | 0.7 | 82.2 | — | — |
| vb-lso-mid-r33 | HAZARD_STOPPED | 27.0 | — | — | — | 0.9 | — | — | — |
| vb-lso-mid-r34 | HAZARD_STOPPED | 44.0 | — | — | — | 0.7 | — | — | — |
| vb-nf-mid-r30 | HAZARD_COLLISION | nan | — | — | — | — | — | — | — |
| vb-nf-mid-r31 | HAZARD_COLLISION | nan | — | — | — | — | — | — | — |
| vb-nf-mid-r32 | HAZARD_COLLISION | nan | — | — | — | — | — | — | — |
| vb-nf-mid-r33 | HAZARD_COLLISION | nan | — | — | — | — | — | — | — |
| vb-nf-mid-r34 | HAZARD_COLLISION | nan | — | — | — | — | — | — | — |
| vb-nf-mid-r35 | HAZARD_COLLISION | nan | — | — | — | — | — | — | — |
