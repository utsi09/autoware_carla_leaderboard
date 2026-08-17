# -*- coding: utf-8 -*-
"""T_lat-clear 표본 오딧 (v6 확정 산술의 재현 스크립트).

표본 정의 (사전 지정 포함 기준):
  - 절제 본 캠페인 시드 S02~S11 × 대피 팔 A3·A4 = 정확히 20케이스.
  - S01은 개발용 시드로 사전 제외(제4장 7절), 거리 사다리 케이스는 절제
    표본이 아니므로 제외.
  - S05의 A4는 시뮬레이터 실패로 동일 시드 재실행분(S05R)으로 대체.

3분류 (조작적 정의, 제4장 8절과 동일):
  1) collision      : 원장(RAW-HIT) 충돌 — 차선 반환의 경쟁(실패) 사건.
                      시간분포에 포함하지 않고 별도 보고.
  2) cleared        : 무충돌이고, 조우 시점(보행자 스폰 = 물리 틱 로그 시작)
                      기준 관찰 지평 H=20 s(E20과 동일 지평) 안에서 주행차선
                      중심선으로부터의 횡방향 이탈이 1.8 m를 최초로 초과.
                      t = 초과가 관측된 최초 물리 틱의 상대 시각.
  3) not-cleared    : 무충돌이나 지평 내 이탈 관측 없음(우측 중도절단).
                      로그 종료가 지평보다 이르면 로그 종료 시각에서 절단.
                      조우 시점에 이미 횡오프셋>1.8 m인 케이스(선행 정차로
                      이탈 시각의 관측이 불가능)는 이탈 '관측'이 아니므로
                      본 범주로 분류한다.

데이터 소스 (전부 원로그):
  - experiments/results/ablation_v3.log        : 케이스 실행 순서·타임라인
  - experiments/results/ablation_final_table.csv : 시드×팔 원장 판정
  - experiments/results/tick_*.csv             : 조우 물리 틱 (frame, sim_t,
                                                 ego_x, ego_y, ped_x, ped_y,
                                                 gap, ego_v)
  - lb_route.csv                               : 주행차선 중심선 폴리라인

출력: experiments/results/tclear_audit.csv + 콘솔 표 + assert 검산.
"""
import csv
import datetime
import glob
import math
import os
import re
import statistics as st

ROOT = '/home/taewook/autoware_carla_leaderboard'
RES = os.path.join(ROOT, 'experiments', 'results')
OUT_CSV = os.path.join(RES, 'tclear_audit.csv')
HORIZON_S = 20.0     # 관찰 지평 (E20과 동일)
LAT_THR_M = 1.8      # 횡이탈 임계 (제4장 8절)
YEAR = 2026

# ---------- 1) 주행차선 중심선 ----------
route = [(float(r['x']), float(r['y']))
         for r in csv.DictReader(open(os.path.join(ROOT, 'lb_route.csv')))]


def lat_offset(x, y):
    """중심선 폴리라인까지의 최단 수직거리 [m]."""
    best = 1e9
    for (x1, y1), (x2, y2) in zip(route, route[1:]):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 == 0:
            continue
        u = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        best = min(best, math.hypot(x - (x1 + u * dx), y - (y1 + u * dy)))
    return best


# ---------- 2) 케이스 타임라인 (ablation_v3.log) ----------
log = open(os.path.join(RES, 'ablation_v3.log'), errors='ignore').read()
cases = re.findall(r'===== (S\d+R?) (A\d) \([^)]*\) =====\n'
                   r'\[runner\] 1 cases -> \S*results_(\d{4}_\d{4})\.csv', log)


def case_ts(mmdd_hhmm):
    mm, dd = int(mmdd_hhmm[:2]), int(mmdd_hhmm[2:4])
    hh, mi = int(mmdd_hhmm[5:7]), int(mmdd_hhmm[7:9])
    return datetime.datetime(YEAR, mm, dd, hh, mi).timestamp()


timeline = [(s, a, case_ts(t)) for s, a, t in cases]

# ---------- 3) 틱 파일 → 케이스 귀속 ----------
# 틱 파일명의 epoch = 조우 기록 시작 시각. 각 케이스의 조우는 케이스 시작
# (results CSV 생성, 분 해상도) 후 1~6분 안에 발생하므로, epoch-60 s 이전의
# 마지막 케이스 시작에 귀속시킨다 (분 해상도 경계의 오귀속 방지).
ticks = sorted((int(re.match(r'tick_(.+)_(\d+)\.csv', os.path.basename(f))
                    .group(2)), f)
               for f in glob.glob(os.path.join(RES, 'tick_*.csv')))
tick_of = {}
for ep, f in ticks:
    owner = None
    for s, a, t0 in timeline:
        if t0 <= ep - 60:
            owner = (s, a, t0)
    if owner and owner[:2] not in tick_of and ep - owner[2] < 360:
        tick_of[owner[:2]] = f

# ---------- 4) 원장 판정 ----------
verdict = {(r['seed'], r['arm']): r['verdict']
           for r in csv.DictReader(
               open(os.path.join(RES, 'ablation_final_table.csv')))}

# ---------- 5) 표본 구성: S02~S11 × A3·A4 (S05 A4 → S05R A4 대체) ----------
SEEDS = ['S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09', 'S10', 'S11']
sample = []
for s in SEEDS:
    for a in ('A3', 'A4'):
        key = (s, a)
        if key not in verdict:           # S05 A4 → 동일 시드 재실행 S05R
            key = (s + 'R', a)
        assert key in verdict, f'verdict missing for {key}'
        sample.append(key)
assert len(sample) == 20

# ---------- 6) 케이스별 분류 ----------
rows = []
for (s, a) in sample:
    v = verdict[(s, a)]
    f = tick_of.get((s, a))
    assert f is not None, f'tick log missing for {(s, a)}'
    pts = [(float(r[1]), float(r[2]), float(r[3]))
           for r in csv.reader(open(f)) if r and r[0] != 'frame']
    t0 = pts[0][0]
    d0 = lat_offset(pts[0][1], pts[0][2])
    t_clear = None
    for t, x, y in pts:
        if t - t0 > HORIZON_S:
            break
        if lat_offset(x, y) > LAT_THR_M:
            t_clear = round(t - t0, 1)
            break
    log_dur = round(pts[-1][0] - t0, 1)
    if v == 'COLLISION':
        outcome, t_rep = 'collision-failed-clearance', ''
    elif t_clear is not None and d0 <= LAT_THR_M:
        outcome, t_rep = 'cleared-observed', t_clear
    else:
        outcome = 'not-cleared-censored'
        t_rep = round(min(log_dur, HORIZON_S), 1)   # 절단 시각
    rows.append({'seed': s, 'arm': a, 'verdict': v, 'outcome': outcome,
                 't_s': t_rep, 'log_dur_s': log_dur,
                 'lat_off_at_encounter_m': round(d0, 2),
                 'tick_file': os.path.basename(f)})

# ---------- 7) 집계·검산 ----------
coll = [r for r in rows if r['outcome'] == 'collision-failed-clearance']
ev = [r for r in rows if r['outcome'] == 'cleared-observed']
cen = [r for r in rows if r['outcome'] == 'not-cleared-censored']

hdr = f"{'seed':6s}{'arm':5s}{'verdict':11s}{'outcome':28s}{'t[s]':>7s}" \
      f"{'logdur':>8s}{'d0[m]':>7s}"
print(hdr)
print('-' * len(hdr))
for r in rows:
    print(f"{r['seed']:6s}{r['arm']:5s}{r['verdict']:11s}{r['outcome']:28s}"
          f"{str(r['t_s']):>7s}{r['log_dur_s']:>8.1f}"
          f"{r['lat_off_at_encounter_m']:>7.2f}")
print('-' * len(hdr))

total = len(rows)
n_coll, n_ev, n_cen = len(coll), len(ev), len(cen)
coll_a3 = sum(1 for r in coll if r['arm'] == 'A3')
coll_a4 = sum(1 for r in coll if r['arm'] == 'A4')
ev_times = sorted(r['t_s'] for r in ev)
med_obs = st.median(ev_times)

# Kaplan-Meier (무충돌 13케이스 조건부; 이벤트=이탈 관측, 절단=지평/로그 종료)
km_pts = sorted([(t, 1) for t in ev_times] +
                [(r['t_s'], 0) for r in cen])
n_at_risk, surv, km_median = n_ev + n_cen, 1.0, None
for t, is_ev in km_pts:
    if is_ev:
        surv *= (n_at_risk - 1) / n_at_risk
        if km_median is None and surv < 0.5:
            km_median = t
    n_at_risk -= 1

print(f'총계 {total} = 충돌 {n_coll} (A3 {coll_a3} + A4 {coll_a4}) '
      f'+ 이탈 관측 {n_ev} + 지평 내 미이탈(절단) {n_cen}')
print(f'이탈 관측값 [s]: {ev_times}  → 관측 중앙값 {med_obs:.2f} (≈11.0)')
print(f'KM: 이벤트 {n_ev}/{n_ev + n_cen}, 최종 생존율 {surv:.3f} '
      f'→ 중앙값 {"미도달 (not reached)" if km_median is None else km_median}')

# ---------- 검산 (4차 리뷰 확정 산술) ----------
assert total == 20, f'총계 {total} != 20'
assert n_coll == 7, f'충돌 {n_coll} != 7'
assert (coll_a3, coll_a4) == (3, 4), f'충돌 팔별 {coll_a3}+{coll_a4} != 3+4'
assert n_ev == 6, f'이탈 관측 {n_ev} != 6'
assert n_cen == 7, f'미이탈 절단 {n_cen} != 7'
assert n_coll + n_ev + n_cen == total
assert 10.9 <= med_obs <= 11.0, f'관측 중앙값 {med_obs} 이탈'
assert km_median is None and surv > 0.5, 'KM 중앙값이 미도달이어야 함'
assert all(r['t_s'] > 11.8 for r in cen), '절단 시각이 최종 이벤트보다 짧음'
print('ASSERTS OK: 총계 20, 충돌 7(3+4), 이탈 6, 절단 7, '
      '관측 중앙값 ≈11.0 s, KM 미도달(생존율 %.3f > 0.5)' % surv)

# ---------- 8) CSV ----------
with open(OUT_CSV, 'w', newline='') as fo:
    w = csv.DictWriter(fo, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print('saved', OUT_CSV)
