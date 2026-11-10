#!/usr/bin/env python3
"""lcl 점수 0.2 뒤에 숨은 연속 성분을 8월 캠페인 cdr.log.gz 에서 복원한다 (lidar_quality_check.hpp 식 그대로).
입력: results/case_logs/<MMDD_HHMM>_<idx>_<method>_<fault>/cdr.log.gz + results/results_08*.csv (세기·결말 매핑)
출력: results/lcl_components.csv (케이스당 한 줄) + 조건별 표(stdout)
윈도: CUSUM 이 h=0.5 를 처음 넘은 프레임부터 200 프레임(고장 조건), nf 는 프레임 100 이후 전체."""
import csv, glob, gzip, math, os, re, statistics as st, collections, sys
R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
LN = re.compile(r"LIDAR_front quality: ([\d.e+-]+) \(sigma ([\d.e+-]+)m, base ([\d.e+-]+)m, pts (\d+)/(\d+), cusum ([\d.e+-]+), near (\d+)/(\d+), far (\d+)/(\d+), worst_sect ([\d.e+-]+)\)")
WIN = 200; FAILS = {"CARLA_DIED", "INTERRUPTED", "DRY", ""}
rows_by = {}
for f in sorted(glob.glob(f"{R}/results_08*.csv")):
    stamp = os.path.basename(f)[8:17]
    try: rs = list(csv.DictReader(open(f)))
    except Exception: continue
    for r in rs: rows_by.setdefault((r["idx"], r["method"], r["fault"]), []).append((stamp, r))
def lookup(stamp, idx, method, fault):
    c = [x for x in rows_by.get((idx, method, fault), []) if x[0] <= stamp]
    return c[-1][1] if c else None
out = []; mismatch = [0, 0]
for d in sorted(glob.glob(f"{R}/case_logs/*_*_*_*_*")):
    m = re.match(r"(\d{4}_\d{4})_(\d+)_(\w+?)_(lcl|nf)$", os.path.basename(d))
    if not m or m[1] < "0812_0221": continue
    r = lookup(m[1], m[2], m[3], m[4])
    if not r or r["outcome"] in FAILS: continue
    p = os.path.join(d, "cdr.log.gz")
    if not os.path.exists(p): continue
    fr = []
    try:
        with gzip.open(p, "rt", errors="replace") as fh:
            for ln in fh:
                g = LN.search(ln)
                if g: fr.append([float(x) for x in g.groups()])
    except Exception: continue
    if len(fr) < 150: continue
    # count_baseline_ 재귀 (hpp 그대로): 첫 30프레임 EMA, 이후 0.95x 초과일 때만 1% 추종
    cbs = []; cb = 0.0
    for i, x in enumerate(fr):
        nv = x[3]
        if i < 30: cb = nv if cb == 0.0 else 0.8 * cb + 0.2 * nv
        elif nv > cb * 0.95: cb = 0.99 * cb + 0.01 * nv
        cbs.append(cb)
    trip = next((i for i, x in enumerate(fr) if x[5] > 0.5), None)
    if m[4] == "nf": i0, i1 = 100, len(fr)
    else:
        if trip is None: continue
        i0, i1 = trip, trip + WIN
    w = fr[i0:i1]; w_cb = cbs[i0:i1]
    if len(w) < 50: continue
    on = None
    if trip is not None:
        on = trip
        while on > 0 and fr[on - 1][5] > 0: on -= 1
    N, C, U, F, NR, S = [], [], [], [], [], []
    for (q, sig, base, nv, n, cus, near, nb, far, fb, ws), cb in zip(w, w_cb):
        noise = math.exp(-max(0, sig - base) / 0.1)
        cr = min(max((min(nv / cb, 1) - 0.7) / 0.3, 0), 1); count = cr * cr
        clut = math.exp(-max(0, near / nb - 1.3) / 0.5) if nb > 50 else 1.0
        u = min(min(max(noise * count, 0), 1), clut)
        cap = min(u, 0.2) if cus > 0.5 else u
        mismatch[0] += 1; mismatch[1] += abs(cap - q) > 0.05
        N.append(noise); C.append(clut); U.append(u); S.append(sig - base)
        NR.append(near / nb if nb else 1); F.append(far / fb if fb else 1)
    sev = "nf" if m[4] == "nf" else r["severity"]
    out.append(dict(tag=os.path.basename(d), method=m[3], sev=sev, npc=r["npc"], outcome=r["outcome"],
        q=st.median(x[0] for x in w), uncapped=st.median(U), noise=st.median(N), clutter=st.median(C),
        sig_excess=st.median(S), near_ratio=st.median(NR), far_ratio=st.median(F),
        trip_delay_f=(trip - on) if trip is not None and on is not None else "",
        q_all=st.median(x[0] for x in fr[(trip or 100):])))
with open(f"{R}/lcl_components.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(f"cases={len(out)}  frames checked={mismatch[0]}  |recalc-logged|>0.05: {mismatch[1]} ({100*mismatch[1]/max(mismatch[0],1):.1f}%)")
print("| sev | n | 기록 점수 q | 고장 뒤 전체 q | 바닥 제거 점수 | noise항 | clutter항 | σ초과 m | 근거리비 | 원거리 잔존 | CUSUM 지연 frame |")
for s in ("nf", "mid", "high"):
    x = [r for r in out if r["sev"] == s]
    if not x: continue
    def v(k):
        a = [float(r[k]) for r in x if r[k] != ""]
        return "-" if not a else f"{st.median(a):.3f} [{sorted(a)[len(a)//4]:.3f},{sorted(a)[3*len(a)//4]:.3f}]"
    print(f"| {s} | {len(x)} | {v('q')} | {v('q_all')} | {v('uncapped')} | {v('noise')} | {v('clutter')} | {v('sig_excess')} | {v('near_ratio')} | {v('far_ratio')} | {v('trip_delay_f')} |")
