# 실험 종료 후 작업 큐 (0817 새벽, 사용자 지시 0816 자정)

## 0. 실험 마감 (자동 진행 중)
- [ ] S05 A2 CARLA_DIED 동일시드 재실행 (ablation_failures.txt)
- [ ] S11 4팔, 저속 사다리 {7,6,5} 확인
- [ ] 집계: 원장 시간창 귀속 → 4팔 표 (S02~S11, S01 제외) + Wilson CI
      + exact McNemar (A1↔A4, A3↔A4) + E_H(20s) + T_safe-clear(중도절단)
      + s/v 분해 (s_detect/s_spawn, v_detect/v_spawn/v_collision)
- [ ] 그림 갱신: 4팔 절제, 4.2 vs 3.0 사다리 경계 이동(프로토콜 차이 명기)

## 1. Git push (전부)
- [ ] autoware_carla_leaderboard 레포: experiments/(러너·인젝터·배터리·시드),
      doc/(계획서·보고서), analysis, results CSV·원장·대조표.
      대용량 제외 규칙: mp4/png 프레임 없음(이미 삭제), pvid 제외
- [ ] scenario_runner 패치(atomic_criteria RAW-HIT) 포함 확인
- [ ] fs_ws (cdr_monitor/mrm_supervisor SUP_SHADOW 등) — 별도 레포면 같이 푸시
- [ ] 커밋 메시지에 v4.9v 판정 재구축 + v5 절제 프로토콜 요약

## 2. 석사논문 작성 (서식 완벽 준수, docx + pdf 둘 다)
입력물:
- 서식: 1750d3b5-...Word_Masters_Template.docx (성균관대 일반대학원)
- 옛 초안: 7802ffe0-...pdf (63p) — 구조·관련연구·참고문헌 재활용
- 본심 요약 양식: a123db70-...pdf (제목/요약/기여도/실적 페이지)

작성 원칙:
- 표지/속표지/제출서/인준지 한자 양식 그대로 (碩士學位 請求論文, 2026년 4월
  제출 / 6월 인준, 審査委員長 서명란 3인)
- 제목 유지(국문+영문): "행동트리 기반 센서 건강도 감시와 위험·잔여능력
  기반 최소위험기동 감독을 통한 자율주행 시스템의 단계적 고장 대응" /
  "Graded Fault Response for Autonomous Driving via Behavior-Tree-based
  Sensor Health Monitoring and Risk/Capability-aware MRM Supervision"
- 관련연구·참고문헌([1] Tang 2026 MRM, [2] Xue MPC fallback 등)과 고장모델
  문헌(Trierweiler/Goodin/LISA/Langel/Bhatti), AWCL(TUMFTM), UNECE R157,
  Reschka — 옛 초안에서 최대 재활용, IEEE Trans. 형식
- **수치 전면 교체 (옛 초안은 구버전 실험)**:
  구: 1,313케이스 / 갓길 84% / 점유 54%→21% / McNemar 4.6e-33 / 오경보 0/146
  신: v4.8 재실험 매트릭스 + 재실험 50 + 절제 40+ (S02~S11) + 사다리 n=4
  + 저속 사다리 + 노출 E_H + T_safe-clear + 판정 3중 오라클 방법론
- 새로 추가할 장/절: 충돌 판정 시스템(원장·물리 오라클·육안 대조 프로토콜),
  절제 실험(과도구간 응답), 정지거리 모델과 경계 검증, 한계(과도구간 위험창,
  단일 맵). 구버전 수치 기반 서술은 전부 탐지·교체
- 본심 요약본(a123db70 양식)도 갱신: 요약·기여도표·정량/정성 기여
- 산출: docx (서식 스타일 사용) → LibreOffice로 pdf 변환, 둘 다 전달

주의: 이름/학번/지도교수 칸은 공란 유지 (사용자 기입)
