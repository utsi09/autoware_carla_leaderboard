# -*- coding: utf-8 -*-
"""v20 edits (0826): figure set -> slide-15+ paper set (10 figs), pincer replaces.
Removed: 3-3 state machine(->policy matrix), 4-1 setup, 4-4 encounter, 5-1 traces,
5-2 heatmap, 5-3 exposure, 5-4 final campaign, 5-5 ablation, 5-7 hardfail(->5-1 latency).
Every replace asserts count==1 before applying (편집 규약)."""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PB = '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs'

def load(f):
    return io.open(os.path.join(HERE, f), encoding='utf-8').read()

def save(f, s):
    io.open(os.path.join(HERE, f), 'w', encoding='utf-8').write(s)

def rep(s, old, new, f):
    n = s.count(old)
    assert n == 1, f'{f}: count={n} for {old[:60]!r}'
    return s.replace(old, new)

def del_fig_line(s, prefix, f):
    lines = s.split('\n')
    hits = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
    assert len(hits) == 1, f'{f}: {len(hits)} lines start with {prefix[:40]!r}'
    del lines[hits[0]]
    return '\n'.join(lines)

# ---------------- content1: 그림 1-1 problem scenario ----------------
s = load('content1.py')
s = rep(s, '세 판단이 선행되어야 한다:', '세 판단이 선행되어야 한다(그림 1-1):', 'c1')
s = rep(s, "속도 상한(고정 3.0 m/s)으로 구현한다.'),\n",
        "속도 상한(고정 3.0 m/s)으로 구현한다.'),\n"
        "('fig', '그림 1-1. 문제 설정. (a) 센서 고장 시의 단계적 대피 선택지 — ① 여유 공간(free space), ② 주차장, ③ 전방 갓길, ④ 차선 내 정지 — 는 비용함수로 서열화된다. (b) 대피 중 보행자 돌발 조우 엣지케이스.', 'fig1_1', '"
        + PB + "/fig1_problem.png', None, 12.5),\n", 'c1')
save('content1.py', s)

# ---------------- content2: ch3/ch4 ----------------
s = load('content2.py')
# 3-1 arch
s = rep(s, "('fig', '그림 3-1. 제안 시스템의 구조. 감시 모듈(cdr_monitor)이 센서별 신선도·품질·물리 채널을 점수화해 발행하면, 감독자(mrm_supervisor)가 상태기계와 비용함수로 대응을 선택해 속도 상한과 함께 Autoware 실행 계층에 전달한다.', 'fig3_1', '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_system_arch.png', None, 10.5),",
        "('fig', '그림 3-1. 제안 시스템의 구조. CARLA-브리지-Autoware 폐루프의 상류(브리지)에서 센서 고장이 주입되고, 감독 계층(그림 표기 CDR Monitor = cdr_monitor, MRM Supervisor = mrm_supervisor)이 부가(add-on)로 부착된다. 감시 모듈이 센서 토픽을 읽기 전용 구독해 건강 점수를 발행하면, 감독자가 경로 재설정·속도 상한(대피) 또는 진단 ERROR 주입(위임)으로 실행 계층에 개입한다.', 'fig3_1', '" + PB + "/fig2_arch.png', None, 11.5),", 'c2')
# 3-2 bt path swap
s = rep(s, "'fig3_bt', '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_bt_structure.png', None, 11.0),",
        "'fig3_bt', '" + PB + "/fig3_bt.png', None, 14.5),", 'c2')
# 3-3 state machine -> policy matrix
s = rep(s, "('fig', '그림 3-3. 감독자 상태기계. 건강도 점수 밴드(0.3 < health ≤ 0.7)에서 갓길·주차장 대피(MRM_MOVE→MRM_PARKED)를, 바닥 이하(health ≤ 0.3) 또는 위치 신뢰 붕괴에서 순정 정차 위임(MRM_DEFER)을 선택한다.', 'fig3_2', '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_state_machine.png', None, 10.0),",
        "('fig', '그림 3-3. 감시 상태별 MRM 선택 정책 행렬. 이중 임계(상단 0.7, 하단 0.3)가 정상(NORMAL)·열화(DEGRADED)·위기(CRITICAL)를 구분하고, ●는 비용 서열에 따른 선택, ○는 이동 실패 시 폴백, ×는 미선택을 뜻한다. 죽은 센서는 임계와 무관하게 열화 단계로 직행하고, 도달 가능한 후보가 없으면 위기 단계로 격하되어 순정 정지에 위임된다.', 'fig3_2', '" + PB + "/tab1_policy.png', None, 15.0),", 'c2')
s = rep(s, '감독자의 상태기계(그림 3-3)는 건강도 점수의 이중 임계(상단 0.7, 하단 0.3)로 전이한다:',
        '감독자는 건강도 점수의 이중 임계(상단 0.7, 하단 0.3)로 대응을 전환한다(그림 3-3):', 'c2')
# 3-4 candidates
s = rep(s, "('fig', '그림 3-4. Town07 대피 후보 지도 — 벡터맵에서 추출한 갓길 후보 16개소(원), 주차장 후보(사각·다각형), 신호 교차로(삼각) 및 기준 경로(파선). 신호 교차로는 관측성 게이트의 대상이며, 후보의 경로 비용은 자체 도로망 그래프에서 산출한다.', 'fig3_4', '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_candidates_map.png', None, 9.5),",
        "('fig', '그림 3-4. Town07 대피 후보 지도 — 벡터맵에서 추출한 갓길 후보 16개소(레인렛 형상)와 주차장 후보 4개소(폴리곤), 기준 경로(파선). 후보의 경로 비용은 자체 도로망 그래프에서 산출하며, 신호 교차로는 관측성 게이트의 대상이다.', 'fig3_4', '" + PB + "/fig4_candidates.png', None, 10.0),", 'c2')
# 4-1 setup 삭제, 4-2 scenes -> 4-1, 4-3 faults -> 4-2
s = del_fig_line(s, "('fig', '그림 4-1. 실험 환경:", 'c2')
s = rep(s, "('fig', '그림 4-2. 대표 실행 화면(실제 실행 캡처): (a) Town07 주행, (b) RViz 인식, (c) 후보 주석 벡터맵, (d) 갓길 대피 MRC 도달, (e) 주차장 대피 상공 뷰, (f) 보행자 돌발 조우(제4장 4절).', 'fig4_2', '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_scene_panels.png', None, 12.0),",
        "('fig', '그림 4-1. 대표 실행 화면(실제 실행 캡처): (a) Town07 주행, (b) RViz 인식, (c) 후보 주석 벡터맵, (d) 갓길 대피 MRC 도달(후속 교통 통과), (e) 주차장 대피 MRC 상공 뷰, (f) 보행자 돌발 조우(제4장 4절).', 'fig4_2', '" + PB + "/fig5_scenes.png', None, 15.5),", 'c2')
s = rep(s, "('fig', '그림 4-3. 고장 주입의 센서 수준 효과", "('fig', '그림 4-2. 고장 주입의 센서 수준 효과", 'c2')
s = rep(s, "'fig4_faults', '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_sensor_fault_effects.png', None, 11.5),",
        "'fig4_faults', '" + PB + "/fig6_faults.png', None, 11.5),", 'c2')
s = rep(s, '보행자를 발사한다(그림 4-4).', '보행자를 발사한다.', 'c2')
s = del_fig_line(s, "('fig', '그림 4-4. 보행자 돌발 조우 주입 구조.", 'c2')
save('content2.py', s)

# ---------------- content3: ch5 ----------------
s = load('content3.py')
# 새 그림 5-1 (감지 지연) — 표 5-1 뒤, 연속신호 문단 앞에 삽입
s = rep(s, "('p', '표의 이진 검출률 이면의 연속 신호를",
        "('fig', '그림 5-1. 고장 조건별 감지 지연 분포(제안 팔, 주입 시점 기준). 상단은 본 캠페인, 하단은 보조 캠페인(항법 확장, 표 4-2 †)이며, 카메라·라이다 사망(†)은 하드 페일 고속경로의 원장 기반 시뮬레이션 시간 재계측이다(제5장 8절). 굵은 가로 막대는 중앙값이고, GNSS 두절(gf)의 우측 꼬리는 적신호 정차 중 주입되어 재출발 후 감지된 케이스이다.', 'fig5_1dl', '" + PB + "/fig7_latency.png', None, 12.0),\n"
        "('p', '표의 이진 검출률 이면의 연속 신호를", 'c3')
# 연속 궤적 문단 — 그림 의존 제거 (그림 5-1 삭제)
s = rep(s, '표의 이진 검출률 이면의 연속 신호를 그림 5-1이 보인다. 그림의 실선은 감독자 상태 전이(0.7/0.3)에 실제 입력되는 perception 채널이다',
        '표의 이진 검출률 이면에는 연속 건강도 신호가 있다. 감독자 상태 전이(0.7/0.3)에 실제 입력되는 것은 perception 채널이다', 'c3')
s = rep(s, '(lso-mid의 의도된 무개입이 이 그림에서 직접 읽힌다)', '(lso-mid의 의도된 무개입이 여기에 근거한다)', 'c3')
s = rep(s, '본 그림은 /monitor/scores로 관측되는 라이다 열화 채널로 예시한다.',
        '본 관측은 /monitor/scores의 라이다 열화 채널 기준이다.', 'c3')
s = del_fig_line(s, "('fig', '그림 5-1. 연속 건강도 궤적", 'c3')
# 히트맵 삭제
s = rep(s, '을 표 5-2에 요약하고, 전 조합(고장-심각도 × 방법)의 조망은 그림 5-2의 히트맵을 참조한다.',
        '(전 조합: 고장-심각도 × 방법)을 표 5-2에 요약한다.', 'c3')
s = del_fig_line(s, "('fig', '그림 5-2. 본 캠페인 MRM 결과:", 'c3')
# 노출 그림 삭제
s = rep(s, '각각 11~12 m와 8~9 m였다(그림 5-3).', '각각 11~12 m와 8~9 m였다.', 'c3')
s = del_fig_line(s, "('fig', '그림 5-3. 고장 유형별 고장 상태 주행 노출(평균).", 'c3')
# 사다리: 그림 5-4(a) -> 새 그림 5-2 (정지거리), 표 5-3 블록 뒤 삽입
s = rep(s, '(표 5-3, 그림 5-4(a))', '(표 5-3, 그림 5-2)', 'c3')
s = rep(s, "('p', '라이다 완전 열화(lso-high) 순정의 같은 사다리는",
        "('fig', '그림 5-2. 정지거리 모델 d = vτ + v²/2a(τ=1.5 s, a=3.5 m/s²)와 거리 사다리 실측 회피/충돌 경계(음영 밴드). 4.2 m/s의 실측 경계(8~11 m)는 모델 예측 8.8 m와 일치하고, 3.0 m/s의 경계(7~8 m)는 예측 5.79 m 대비 보수적이다(플래너 반응 분산). 점선은 이후 실험의 돌발 스폰 거리 8 m이다.', 'fig5_2sd', '" + PB + "/fig8_stopdist.png', None, 11.5),\n"
        "('p', '라이다 완전 열화(lso-high) 순정의 같은 사다리는", 'c3')
s = rep(s, '비교 결과이다(그림 5-4(b)).', '비교 결과이다.', 'c3')
s = del_fig_line(s, "('fig', '그림 5-4. (a) 무고장 순정의 거리 사다리와", 'c3')
# 절제 그림 삭제
s = rep(s, '대비가 선명하다(그림 5-5(b)):', '대비가 선명하다:', 'c3')
s = del_fig_line(s, "('fig', '그림 5-5. 절제 실험 결과.", 'c3')
# KM 5-6 -> 5-3
s = rep(s, "('fig', '그림 5-6. 무충돌 대피 케이스의 차선 반환 Kaplan–Meier 곡선",
        "('fig', '그림 5-3. 무충돌 대피 케이스의 차선 반환 Kaplan–Meier 곡선", 'c3')
s = rep(s, "'fig5_6km', '/home/taewook/autoware_carla_leaderboard/doc/figs/fig_lane_clear_km.png', None, 9.0),",
        "'fig5_6km', '" + PB + "/fig9_km.png', None, 11.0),", 'c3')
# 하드페일: 그림 5-7 -> 그림 5-1 참조, 그림 삭제
s = rep(s, '(표 5-8, 그림 5-7)', '(표 5-8, 그림 5-1)', 'c3')
s = del_fig_line(s, "('fig', '그림 5-7. 하드 페일 감지·판정 지연 분포", 'c3')
save('content3.py', s)

# ---------------- build.py / map_pages.py 출력 경로 ----------------
for f in ('build.py', 'map_pages.py', 'finalize_v19.py'):
    p = os.path.join(HERE, f)
    if os.path.exists(p):
        t = io.open(p, encoding='utf-8').read()
        t2 = t.replace('thesis_v19_0822', 'thesis_v20_0826')
        io.open(p, 'w', encoding='utf-8').write(t2)

print('all edits applied')
# 최종 그림 인벤토리 출력
import importlib.util
figs = []
for f in ('content1.py', 'content2.py', 'content3.py'):
    for ln in load(f).split('\n'):
        if ln.startswith("('fig'"):
            figs.append(ln.split("'")[3][:28])
print(len(figs), 'figures:', figs)
