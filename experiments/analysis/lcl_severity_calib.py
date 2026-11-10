#!/usr/bin/env python3
"""[2026-11-09 v5b] lcl 2단계 세기 추정 — 보정(사전 지정 규칙) + 관문 판정 + 폐루프 일치 검사.

모니터(lidar_quality_check.hpp, CDR_LCL_SEV_CFG 경로)와 똑같은 계산을 cdr 로그로 재현한다.
  1단계: CUSUM > h(0.5) = 강수형 거리 지터 존재 (frames > 30)          ← 1차와 동일(nf/lso 미발동 관문 G4)
  2단계: 강도-거리 감쇠 계수. 매 프레임 1 m 빈(3~40 m)별 반사강도(uint8) 하위 중앙값의 ln 을 빈 점수 가중
         최소제곱으로 적합한 기울기의 부호 반전 katt(= a_atm + 2α). 맑은 기준선 kbase 는 시그마 기준선과 같은
         규칙(워밍업 30프레임 EMA 0.2, 이후 1.5배 미만일 때만 0.01 추종). CUSUM 초과 순간 kbase 고정 →
         α_now = max(0, (katt − kbase_trip)/2) → EMA(ema)
         ln R = a + b ln(max(α_ema, eps_a))     (Goodin 2019: α = 0.01 R^0.6 → 이론값 a = ln(100)/0.6 = 7.675, b = 1/0.6)
         q = clamp(0.5 - beta log10(R/7.6), 0.05, 0.95)   (beta: 2.5 mm/h -> 0.7, 7.6 -> 0.5)
1차(2026-11-08 23:32; 특징 = 원거리 잔존율 f·근거리 비 n, 검증 105런 rep 0-14)는 G2b(5 mm/h 주행 유지 0.00)·
G3(1/2/5 mm/h 장거리 오상향 1.00) 실패 — 점수 비가 장면(개활지·근접 구조물) 의존이라 계수로는 못 고침.
보존: results/retune_ext/{calib_report_v1_fn.md, calib_cases_v1_fn.csv, lcl_severity_calib.py.v1_fn_1108, lidar_quality_check.hpp.v5_fn_1108}
2차 사전 지정(자료 수집 전 고정, 2026-11-09 00시):
  - 자료 = 새 모니터(α̂ 로그)로 돈 사다리 lclraw rep 40-43 (7수준 × 4), 학습 = rep 40-41, 시험 = rep 42-43
  - 표본 = 초과 후 1~60 s 구간 10프레임마다 ln α_ema → ln R, 수준별 동일 가중 최소제곱 (1차와 동일)
  - 판정 창 = 초과 후 1~10 s; 10프레임 연속 q<0.5 = MRM(그 시점 q>=0.4 대피, 아니면 정지), 없으면 주행 유지 (동일)
  - 위험 = 기상 '강한 비'(> 7.6 mm/h): 1,2,5 mm/h 는 주행 유지가 정답, 10 이상은 MRM 이 정답 (동일)
관문(모두 통과해야 설정 파일을 쓴다; 1차와 동일):
  G1 시험 수준별 q 중앙값(초과 후 3 s)과 강우율의 Spearman <= -0.9
  G2 균형 정확도 >= 0.8, 5 mm/h 주행 유지 >= 0.8, 15/25/40 mm/h 각각 MRM >= 0.9
  G3 1/2/5 mm/h 장거리 오상향(초과 후 전 구간 10프레임 연속 q<0.5) 각 <= 0.2
  G4 8월 nf 124건·lso 236건에서 CUSUM 초과 0건(새 경로 미도달)
사용: lcl_severity_calib.py calibrate   → results/retune_ext/{lcl_sev_cfg.txt, calib_report.md, calib_cases.csv}, 실패 시 exit 2
      lcl_severity_calib.py check LOG [CFG] → 폐루프 로그의 rain q 와 재현값 비교 (최대 차 <= 0.02 이면 exit 0)
      lcl_severity_calib.py xcheck [CFG]  → 사다리 2 Hz 원시 점군(raw_vision/lad-*)으로 오프라인 α̂ 를 계산해 온라인 로그와 비교
"""
import csv, glob, gzip, math, os, re, sys, collections
import numpy as np

RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"
OUT = f"{RES}/retune_ext"
H = 0.5
FIXED = dict(beta=0.2 / math.log10(7.6 / 2.5), r_heavy=7.6, q_min=0.05, q_max=0.95,
             ema=0.1, eps_a=1e-4, f_floor=0.01, eps_f=0.01, eps_n=0.001)
TRAIN_REPS = (40, 41)
TEST_REPS = (42, 43)
PAT = re.compile(r"LIDAR_front quality: ([-\d.e]+) \(sigma ([-\d.e]+)m, base ([-\d.e]+)m, pts (\d+)/(\d+), "
                 r"cusum ([-\d.e]+), near (\d+)/(\d+), far (\d+)/(\d+)")
ATT = re.compile(r"LIDAR_front att: katt (\S+) kbase (\S+)")
RAIN = re.compile(r"LIDAR_front rain: rhat (\S+) alpha (\S+) aema (\S+) f (\S+) n (\S+) q (\S+)")


def _f(s):
    try:
        return float(s)
    except ValueError:
        return float("nan")


def parse(path):
    op = gzip.open if path.endswith(".gz") else open
    fr, rain = [], {}
    with op(path, "rt", errors="ignore") as f:
        for l in f:
            m = PAT.search(l)
            if m:
                g = [float(x) for x in m.groups()]
                fr.append(dict(q=g[0], cusum=g[5], near=g[6], near_base=g[7], far=g[8], far_base=g[9],
                               katt=None, kbase=None))
                continue
            m = ATT.search(l)
            if m and fr:
                fr[-1]["katt"] = _f(m.group(1)); fr[-1]["kbase"] = _f(m.group(2))
                continue
            m = RAIN.search(l)
            if m and fr:
                rain[len(fr) - 1] = _f(m.group(6))
    return fr, rain


def has_att(fr):
    return any(x["katt"] is not None and math.isfinite(x["katt"]) for x in fr)


def att_slope(r, I):
    """C++ LidarQualityChecker::attenuationSlope 와 같은 계산 (r: 거리[m], I: uint8 반사강도)."""
    m = (r >= 3.0) & (r < 40.0)
    b = (r[m] - 3.0).astype(int); iv = I[m].astype(int)
    sw = swx = swy = swxx = swxy = 0.0; nb = 0
    for k in range(37):
        s = b == k; cnt = int(s.sum())
        if cnt < 30: continue
        h = np.bincount(iv[s], minlength=256)
        med = int(np.searchsorted(np.cumsum(h), (cnt + 1) // 2))   # 하위 중앙값
        if med < 6: continue
        x = 3.0 + k + 0.5; y = math.log(med); w = float(cnt)
        sw += w; swx += w * x; swy += w * y; swxx += w * x * x; swxy += w * x * y; nb += 1
    if nb < 4: return float("nan")
    den = sw * swxx - swx * swx
    if den <= 1e-9: return float("nan")
    return -(sw * swxy - swx * swy) / den


def qmap(rhat, c):
    return min(max(0.5 - c["beta"] * math.log10(max(rhat, 1e-6) / c["r_heavy"]), c["q_min"]), c["q_max"])


def alpha_of(x, k_trip):
    ka = x["katt"]
    if ka is None or not math.isfinite(ka): return None
    return max(0.0, (ka - k_trip) / 2.0)


def replay(fr, c, coef=None):
    """C++ 와 같은 순서. coef=None 이면 특징만(학습용). 반환: trip 인덱스, 프레임별 (q, xa, active)."""
    rain = False; k_trip = 0.0; a_ema = 0.0; trip = None; out = []
    for i, x in enumerate(fr):
        frames = i + 1
        q = x["q"]; xa = None; act = False
        if frames > 30:
            if x["cusum"] > H:
                if not rain:
                    rain = True
                    kb = x["kbase"]; k_trip = kb if (kb is not None and math.isfinite(kb)) else 0.0
                    a0 = alpha_of(x, k_trip); a_ema = a0 if a0 is not None else 0.0
                    if trip is None: trip = i
                else:
                    a1 = alpha_of(x, k_trip)
                    if a1 is not None: a_ema += c["ema"] * (a1 - a_ema)
                xa = math.log(max(a_ema, c["eps_a"])); act = True
                if coef is not None:
                    q = qmap(math.exp(coef[0] + coef[1] * xa), c)
            elif rain:
                rain = False
        out.append((q, xa, act))
    return trip, out


def decide(out, trip, lo, hi):
    """창 [trip+lo, trip+hi) 에서 10프레임 연속 q<0.5 → ('mrm', 대피/정지) 아니면 ('continue',)."""
    run = 0
    for i in range(trip + lo, min(trip + hi, len(out))):
        run = run + 1 if out[i][0] < 0.5 else 0
        if run >= 10:
            return "evacuate" if out[i][0] >= 0.4 else "stop"
    return "continue"


EXCLUDED = []   # 하네스 실패로 뺀 검증 케이스
NOATT = []      # α̂ 로그가 없는 케이스(구 모니터)


def fault_injected(d, p):
    """하네스 실패 판정(결과를 보지 않는 사전 기준): 같은 케이스 GT
    (gt/stock-lcl-<R>_<clutter>-def-r<rep>-*.csv 중 cdr 로그보다 0~15분 앞선 것)에서 ego 의 fault 열이 한 번도 1 이 아니면 False.
    GT 를 못 찾으면 None(판단 불가 → 포함)."""
    m = re.search(r"lclraw_([\d.]+_\d+)_r(\d+)$", d)
    t = os.path.getmtime(p); best = None
    for g in glob.glob(f"{RES}/gt/stock-lcl-{m.group(1)}-def-r{m.group(2)}-*.csv"):
        if g.endswith("_tl.csv"): continue
        dt = t - os.path.getmtime(g)
        if -60 <= dt <= 900 and (best is None or dt < best[0]): best = (dt, g)
    if best is None: return None
    with open(best[1], newline="") as f:
        for r in csv.DictReader(f):
            if r.get("kind") == "ego" and r.get("fault") == "1": return True
    return False


def load_validation():
    cases = []
    for d in sorted(glob.glob(f"{RES}/case_logs/lclraw_*_r*")):
        m = re.search(r"lclraw_([\d.]+)_(\d+)_r(\d+)$", d)
        p = f"{d}/cdr.log.gz"
        if not m or not os.path.exists(p): continue
        rep = int(m.group(3))
        if rep not in TRAIN_REPS + TEST_REPS: continue      # 1차 검증(rep 0-14)에는 α̂ 가 없다
        if fault_injected(d, p) is False:
            EXCLUDED.append(os.path.basename(d)); continue
        fr, _ = parse(p)
        if len(fr) < 60: continue
        if not has_att(fr):
            NOATT.append(os.path.basename(d)); continue
        cases.append(dict(src="val", R=float(m.group(1)), rep=rep, tag=os.path.basename(d), fr=fr))
    return cases


def load_august():
    cases = []
    rows = list(csv.DictReader(open(f"{RES}/lcl_components.csv")))
    for r in rows:
        p = f"{RES}/case_logs/{r['tag']}/cdr.log.gz"
        if not os.path.exists(p): continue
        fr, _ = parse(p)
        R = {"mid": 5.0, "high": 25.0, "nf": 0.0}.get(r["sev"])
        if R is None or len(fr) < 40: continue
        cases.append(dict(src="aug", R=R, rep=-1, tag=r["tag"], fr=fr))
    return cases


def calibrate():
    os.makedirs(OUT, exist_ok=True)
    c = dict(FIXED)
    val = load_validation()
    if not val:
        print("no ladder logs with alpha (lclraw rep 40-43)"); return 2
    train = [k for k in val if k["rep"] in TRAIN_REPS]; test = [k for k in val if k["rep"] in TEST_REPS]
    # 학습 표본
    X, y, w = [], [], []
    per_level = collections.Counter()
    samples = []
    for k in train:
        trip, out = replay(k["fr"], c)
        k["trip"] = trip
        if trip is None: continue
        for j in range(trip + 10, min(trip + 600, len(out)), 10):
            if out[j][2]:
                samples.append((k["R"], out[j][1]))
    for R, xa in samples: per_level[R] += 1
    for R, xa in samples:
        X.append([1.0, xa]); y.append(math.log(R)); w.append(1.0 / per_level[R])
    if len(samples) < 10:
        print("too few training samples", len(samples)); return 2
    X = np.array(X); y = np.array(y); W = np.sqrt(np.array(w))
    coef, *_ = np.linalg.lstsq(X * W[:, None], y * W, rcond=None)
    coef = [float(v) for v in coef]
    resid = y - X @ np.array(coef)
    # 평가
    rows = []
    aug = load_august()
    lso_trips = 0; lso_n = 0
    for d in sorted(glob.glob(f"{RES}/case_logs/*_lso")):
        p = f"{d}/cdr.log.gz"
        if not os.path.exists(p): continue
        fr, _ = parse(p); lso_n += 1
        if replay(fr, c)[0] is not None: lso_trips += 1
    for k in test:
        trip, out = replay(k["fr"], c, coef)
        if trip is None:
            rows.append(dict(src=k["src"], tag=k["tag"], R=k["R"], rep=k["rep"], trip="", q3="", ahat3="", rhat3="",
                             decision="continue(no-trip)", long_false="0", post_frames=0)); continue
        j3 = min(trip + 30, len(out) - 1)
        q3 = out[j3][0]; xa = out[j3][1]
        ah3 = math.exp(xa) if xa is not None else float("nan")
        rh3 = math.exp(coef[0] + coef[1] * xa) if xa is not None else float("nan")
        dec = decide(out, trip, 10, 100)
        lf = decide(out, trip, 10, len(out)) != "continue"
        rows.append(dict(src=k["src"], tag=k["tag"], R=k["R"], rep=k["rep"], trip=trip, q3=round(q3, 3),
                         ahat3=round(ah3, 5), rhat3=round(rh3, 2), decision=dec, long_false=int(lf), post_frames=len(out) - trip))
    with open(f"{OUT}/calib_cases.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    # 관문
    vt = [r for r in rows if r["src"] == "val"]
    levels = sorted(set(r["R"] for r in vt))
    med = {}
    for R in levels:
        v = sorted(r["q3"] if r["q3"] != "" else qmap(0.0, c) for r in vt if r["R"] == R)
        med[R] = v[len(v) // 2]
    rk = lambda a: [sorted(a).index(x) for x in a]
    ql = [med[R] for R in levels]
    rho = float(np.corrcoef(rk(levels), rk(ql))[0, 1]) if len(levels) > 2 else float("nan")
    acc = {}
    for R in levels:
        L = [r for r in vt if r["R"] == R]
        ok = [(r["decision"].startswith("continue")) if R <= 7.6 else (not r["decision"].startswith("continue")) for r in L]
        acc[R] = sum(ok) / len(ok)
    lfa = {R: sum(int(r["long_false"]) for r in vt if r["R"] == R) / max(1, len([r for r in vt if r["R"] == R]))
           for R in levels if R <= 7.6}
    nf_trips = sum(1 for k in aug if k["R"] == 0.0 and replay(k["fr"], c)[0] is not None)
    nf_n = sum(1 for k in aug if k["R"] == 0.0)
    G = {
        "G1 Spearman(R, q med) <= -0.9": rho <= -0.9,
        "G2a balanced acc >= 0.8": (sum(acc.values()) / len(acc)) >= 0.8 if acc else False,
        "G2b 5 mm/h continue >= 0.8": acc.get(5.0, 0) >= 0.8,
        "G2c 15/25/40 MRM >= 0.9": all(acc.get(R, 0) >= 0.9 for R in (15.0, 25.0, 40.0)),
        "G3 long-drive false escalation <= 0.2 (1,2,5)": all(v <= 0.2 for v in lfa.values()) if lfa else False,
        "G4 nf/lso CUSUM trips == 0": nf_trips == 0 and lso_trips == 0,
    }
    ok = all(G.values())
    rep = [f"# lcl 세기 보정 보고 v5b(감쇠 계수 α̂) — {len(train)} 학습(rep {TRAIN_REPS}) / {len(test)} 시험(rep {TEST_REPS}) 사다리 케이스, 8월 {len(aug)}건(G4)\n",
           f"계수: a={coef[0]:.4f}, b={coef[1]:.4f}  (학습 표본 {len(samples)}개, ln R 잔차 RMS {float(np.sqrt(np.mean(resid**2))):.3f}; "
           f"Goodin 이론값 a={math.log(100)/0.6:.3f}, b={1/0.6:.3f})\n",
           "| 강우 mm/h | 시험 n | q 중앙값(3 s) | α̂(3 s) 중앙값 | R̂(3 s) 중앙값 | 정답률 | 장거리 오상향 | 결정 분포 |", "|---|---|---|---|---|---|---|---|"]
    for R in levels:
        L = [r for r in vt if r["R"] == R]
        am = sorted(r["ahat3"] for r in L if r["ahat3"] != ""); rm = sorted(r["rhat3"] for r in L if r["rhat3"] != "")
        rep.append(f"| {R:g} | {len(L)} | {med[R]:.2f} | {(am[len(am)//2] if am else float('nan')):.4f} | {(rm[len(rm)//2] if rm else float('nan')):.2f} | "
                   f"{acc[R]:.2f} | {lfa.get(R, float('nan')):.2f} | {dict(collections.Counter(r['decision'] for r in L))} |")
    rep += ["", f"G4: 8월 nf CUSUM 초과 {nf_trips}/{nf_n}, lso 초과 {lso_trips}/{lso_n} (8월 5/25 mm/h 폐루프 판정은 구 모니터 로그라 α̂ 없음 → 재실험 블록 A/B 에서 확인)",
            f"Spearman = {rho:.3f}",
            f"하네스 실패로 제외(고장 미주입·차량 미출발, GT 기준): {len(EXCLUDED)}건 {EXCLUDED}",
            f"α̂ 로그 없음(제외): {len(NOATT)}건 {NOATT}", ""]
    rep += [f"- {'PASS' if v else 'FAIL'} {k}" for k, v in G.items()]
    rep.append(f"\n판정: {'통과 — 설정 파일 작성' if ok else '실패 — 설정 파일 없음, 재실험 보류'}")
    open(f"{OUT}/calib_report.md", "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))
    if ok:
        with open(f"{OUT}/lcl_sev_cfg.txt", "w") as f:
            f.write(f"# lcl severity cfg v5b (calibrated {os.popen('date +%F_%T').read().strip()}; see calib_report.md)\n")
            f.write(f"a {coef[0]:.6f}\nb {coef[1]:.6f}\nc 0.000000\n")
            for k_ in ("eps_a", "beta", "r_heavy", "q_min", "q_max", "ema", "f_floor", "eps_f", "eps_n"):
                f.write(f"{k_} {c[k_]:.6f}\n")
        return 0
    return 2


def load_cfg(path):
    c = dict(FIXED); coef = [0.0, 0.0]
    for l in open(path):
        if not l.strip() or l.startswith("#"): continue
        k, v = l.split()[:2]
        if k == "a": coef[0] = float(v)
        elif k == "b": coef[1] = float(v)
        elif k == "c": pass
        else: c[k] = float(v)
    return c, coef


def check(log, cfg):
    c, coef = load_cfg(cfg)
    fr, rain = parse(log)
    if not rain:
        print("no rain lines in log (path not active?)"); return 3
    if not has_att(fr):
        print("no att lines in log (old monitor binary?)"); return 3
    trip, out = replay(fr, c, coef)
    diffs = [abs(out[i][0] - q) for i, q in rain.items() if i < len(out) and out[i][2]]
    mx = max(diffs) if diffs else float("nan")
    print(f"rain frames {len(rain)}, compared {len(diffs)}, max |dq| = {mx:.4f}, trip at {trip}")
    return 0 if diffs and mx <= 0.02 else 4


def xcheck(cfg):
    """사다리 2 Hz 원시 점군으로 오프라인 katt/α̂ 를 계산해 온라인(cdr 로그) 값과 비교."""
    c, coef = load_cfg(cfg) if os.path.exists(cfg) else (dict(FIXED), [math.log(100) / 0.6, 1 / 0.6])
    print("case | offline: kbase(pre med)  alpha(post med)  R̂ | online: kbase@trip  aema(post med)  R̂ | pre_n post_n")
    for d in sorted(glob.glob(f"{RES}/raw_vision/lad-lcl-*-r*")):
        m = re.search(r"lad-lcl-([\d.]+)_(\d+)-r(\d+)$", d)
        if not m: continue
        inj = None
        try:
            for row in list(csv.reader(open(f"{d}/inj.csv")))[1:]:
                if row[2] in ("True", "1", "true"): inj = float(row[1]); break
        except FileNotFoundError:
            pass
        ks = []
        for fz in sorted(glob.glob(f"{d}/lidar_*.npz")):
            z = np.load(fz); t = z["t_sim"]; off = z["off"]; xyz = z["xyz_cm"]; it = z["inten"]
            for k in range(len(t)):
                a, b = int(off[k]), int(off[k + 1]) if k + 1 < len(off) else len(xyz)
                p = xyz[a:b].astype(np.float32) / 100.0
                ks.append((float(t[k]), att_slope(np.linalg.norm(p, axis=1), it[a:b])))
        if not ks or inj is None: print(os.path.basename(d), "no frames/inj"); continue
        pre = [k for t, k in ks if t < inj - 1 and math.isfinite(k)]; post = [k for t, k in ks if t > inj + 5 and math.isfinite(k)]
        if len(pre) < 3 or len(post) < 3: print(os.path.basename(d), "too few frames"); continue
        kb = float(np.median(pre)); al = float(np.median([max(0.0, (k - kb) / 2) for k in post]))
        rh = math.exp(coef[0] + coef[1] * math.log(max(al, c["eps_a"])))
        # 온라인
        lg = f"{RES}/case_logs/lclraw_{m.group(1)}_{m.group(2)}_r{m.group(3)}/cdr.log.gz"
        on = "n/a"
        if os.path.exists(lg):
            fr, _ = parse(lg); trip, out = replay(fr, c, coef)
            if trip is not None:
                ae = [math.exp(o[1]) for o in out[trip + 50:] if o[2] and o[1] is not None]
                if ae:
                    aem = float(np.median(ae)); on = f"{fr[trip]['kbase']:.5f}  {aem:.5f}  {math.exp(coef[0] + coef[1] * math.log(max(aem, c['eps_a']))):.2f}"
        print(f"{os.path.basename(d)} | {kb:.5f}  {al:.5f}  {rh:.2f} | {on} | {len(pre)} {len(post)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "calibrate":
        sys.exit(calibrate())
    if len(sys.argv) >= 3 and sys.argv[1] == "check":
        sys.exit(check(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else f"{OUT}/lcl_sev_cfg.txt"))
    if len(sys.argv) >= 2 and sys.argv[1] == "xcheck":
        sys.exit(xcheck(sys.argv[2] if len(sys.argv) > 2 else f"{OUT}/lcl_sev_cfg.txt"))
    print(__doc__); sys.exit(1)
