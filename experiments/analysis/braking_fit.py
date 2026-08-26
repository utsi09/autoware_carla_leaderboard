# -*- coding: utf-8 -*-
"""제동 파라미터 동정(0826): braking_id.sh의 5런 틱 로그에서 τ(제동 개시 지연)와
에너지 정합 유효 감속도 a를 추정. 결과(τ=0.46±0.08 s, a=2.87±0.20 m/s²)는
제3장 6절 모델 파라미터 출처 서술의 근거이며, 사다리 경계(검증)와 데이터 독립.
용법: python3 braking_fit.py"""
import glob, csv, math, statistics as st

R = '/home/taewook/autoware_carla_leaderboard/experiments/results'

def fit(f):
    rows = [r for r in csv.DictReader(open(f))]
    t = [float(r['sim_t']) for r in rows]
    v = [float(r['ego_v']) for r in rows]
    x = [float(r['ego_x']) for r in rows]
    y = [float(r['ego_y']) for r in rows]
    t0 = t[0]
    v0 = st.median([vv for tt, vv in zip(t, v) if tt - t0 <= 0.3])
    tb = next(i for i in range(len(t))
              if v[i] < v0 - 0.3 and all(vv < v0 - 0.2 for vv in v[i:i + 5]))
    tau = t[tb] - t0
    stop_i = next(i for i in range(tb, len(v)) if v[i] < 0.2)
    sd = sum(math.dist((x[i], y[i]), (x[i + 1], y[i + 1])) for i in range(0, stop_i))
    a = v0 * v0 / (2 * (sd - v0 * tau))     # 에너지 정합
    return v0, tau, a, sd

if __name__ == '__main__':
    vals = [fit(f) for f in sorted(glob.glob(f'{R}/tick_nf-mid-ours-off-r*.csv'))]
    for v0, tau, a, sd in vals:
        print(f'v0={v0:.2f} tau={tau:.2f} a={a:.2f} stopdist={sd:.2f}')
    taus = [v[1] for v in vals]; aas = [v[2] for v in vals]
    print(f'tau = {st.mean(taus):.2f} ± {st.pstdev(taus):.2f} s | '
          f'a = {st.mean(aas):.2f} ± {st.pstdev(aas):.2f} m/s² (n={len(vals)})')
