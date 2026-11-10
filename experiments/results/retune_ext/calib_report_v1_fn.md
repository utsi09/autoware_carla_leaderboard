# lcl 세기 보정 보고 (63 학습 / 35 시험 검증 케이스, 8월 323건)

계수: a=2.2714, b=0.4573, c=0.0194  (학습 표본 3717개)

| 강우 mm/h | 시험 n | q 중앙값(3 s) | 정답률 | 장거리 오상향 | 결정 분포 |
|---|---|---|---|---|---|
| 1 | 5 | 0.86 | 1.00 | 1.00 | {'continue': 5} |
| 2 | 5 | 0.67 | 1.00 | 1.00 | {'continue': 5} |
| 5 | 5 | 0.51 | 0.00 | 1.00 | {'evacuate': 5} |
| 10 | 5 | 0.42 | 1.00 | nan | {'evacuate': 5} |
| 15 | 5 | 0.34 | 1.00 | nan | {'stop': 5} |
| 25 | 5 | 0.34 | 1.00 | nan | {'stop': 5} |
| 40 | 5 | 0.34 | 1.00 | nan | {'stop': 5} |

8월 폐루프: 5 mm/h 주행 유지 0.09 (n=91), 25 mm/h MRM 1.00 (n=108); nf 초과 0/124, lso 초과 0/237
Spearman = -1.000
하네스 실패로 제외(고장 미주입·차량 미출발, GT 기준): 7건 ['lclraw_10_2100_r2', 'lclraw_15_2750_r9', 'lclraw_1_1000_r2', 'lclraw_25_4000_r0', 'lclraw_25_4000_r8', 'lclraw_40_5900_r9', 'lclraw_5_1500_r7']

- PASS G1 Spearman(R, q med) <= -0.9
- PASS G2a balanced acc >= 0.8
- FAIL G2b 5 mm/h continue >= 0.8
- PASS G2c 15/25/40 MRM >= 0.9
- FAIL G3 long-drive false escalation <= 0.2 (1,2,5)
- PASS G4 nf/lso CUSUM trips == 0

판정: 실패 — 설정 파일 없음, 재실험 보류
