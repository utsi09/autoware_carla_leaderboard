#!/usr/bin/env python3
"""Alibi Detect Online MMD (MMDDriftOnline, pytorch) 를 네 센서 특징 스트림에 동일하게 적용한 대조군 평가 (2026-11-09).
센서별 기준 데이터 = 무고장 짝수 rep 런의 특징(표준화), 시험 = 무고장 홀수 rep(오탐) + 고장 런(검출·지연).
LiDAR·카메라: results/alibi/feat/vb-*.npz (2 Hz, raw_vision 36런), GNSS·IMU: results/alibi/feat/stock-*.npz (20 Hz 샘플, 순정 bag def rep 0–4).
검출 = 주입 뒤 처음 is_drift==1 인 시각(연속 2스텝 확정). ert = 기대 오경보 간격(스텝): 2 Hz 센서 600(5 분), 20 Hz 센서 6000.
사용: venv_alibi/bin/python alibi_mmd_eval.py  → results/alibi/report.md, cases.csv"""
import glob, os, re, csv, collections, numpy as np, statistics as st
from alibi_detect.cd import MMDDriftOnline
RES = "/home/taewook/autoware_carla_leaderboard/experiments/results"; F = f"{RES}/alibi/feat"
import torch; torch.manual_seed(0); np.random.seed(0)
WMULT = float(os.environ.get("MMD_WMULT", "1"))      # window 배수 (기본 1 = 10/20)
PCT = float(os.environ.get("MMD_THR_PCT", "100"))    # 문턱 백분위 (100 = 최대값)
TAG = os.environ.get("MMD_TAG", "")
SENS = {  # sensor: (file glob, time key, feat key, ert, window, nf glob, downsample)
    "lidar":  ("vb-*.npz", "lidar_t", "lidar_feat", 600, 10, "vb-nf-mid-r*.npz", 1),
    "camera": ("vb-*.npz", "cam_t", "cam_feat", 600, 10, "vb-nf-mid-r*.npz", 1),
    "gnss":   ("stock-*.npz", "t", "gnss_feat", 1200, 20, "stock-nf-mid-def-r*.npz", 5),   # 20 Hz → 4 Hz 다운샘플
    "imu":    ("stock-*.npz", "t", "imu_feat", 1200, 20, "stock-nf-mid-def-r*.npz", 5),
}
FAULT_OF = {"lidar": ("lso", "lcl"), "camera": ("cn",), "gnss": ("gn", "gm", "gb"), "imu": ("imn", "imb", "imd")}
def rep_of(name):
    m = re.search(r"-r(\d+)", name); return int(m.group(1)) if m else -1
def fault_sev(name):
    m = re.match(r"(?:vb|stock)-([a-z]+)-([a-z]+)", name); return (m.group(1), m.group(2)) if m else ("?", "?")
def load(path, tk, fk, ds):
    z = np.load(path); t = z[tk][::ds]; x = z[fk][::ds]; tf = float(z["t_fault"]) if "t_fault" in z.files else np.nan
    return t, x, tf
rows = []
for s, (gl, tk, fk, ert, W, nfgl, ds) in SENS.items():
    files = sorted(glob.glob(f"{F}/{gl}")); nf = [p for p in files if "-nf-" in p]
    ref_files = [p for p in nf if rep_of(p) % 2 == 0]; fp_files = [p for p in nf if rep_of(p) % 2 == 1]
    fault_files = [p for p in files if fault_sev(os.path.basename(p))[0] in FAULT_OF[s]]
    if not ref_files or not fault_files: print(s, "no data"); continue
    xr = np.concatenate([load(p, tk, fk, ds)[1] for p in ref_files]); xr = xr[:, :3] if s == "gnss" else xr; xr = xr[np.isfinite(xr).all(1)]
    mu, sd = xr.mean(0), xr.std(0) + 1e-6; xr = ((xr - mu) / sd).astype(np.float32)
    if len(xr) > 3000: xr = xr[np.random.choice(len(xr), 3000, replace=False)]
    print(f"[{s}] ref {xr.shape} from {len(ref_files)} nf runs; fp runs {len(fp_files)}; fault runs {len(fault_files)}", flush=True)
    W = int(W * WMULT)
    cd = MMDDriftOnline(xr, ert=ert, window_size=W, backend="pytorch", n_bootstraps=1500, verbose=False)
    def stream(p):
        t, x, tf = load(p, tk, fk, ds); x = x[:, :3] if s == "gnss" else x; x = ((x - mu) / sd).astype(np.float32); cd.reset_state(); stats = []; flags = []
        for xi in x:
            if not np.isfinite(xi).all(): stats.append(0.0); flags.append(0); continue
            r = cd.predict(xi, return_test_stat=True)["data"]; stats.append(float(r["test_stat"] or 0.0)); flags.append(int(r["is_drift"]))
        return t, np.array(stats), np.array(flags), tf
    def confirm(flag):
        conf = np.zeros_like(flag); conf[1:] = (flag[1:] == 1) & (flag[:-1] == 1); return conf   # 연속 2 스텝 확정
    # 문턱 보정(다른 베이스라인과 같은 규칙): 홀수 rep 무고장 런의 앞 절반에서 통계량 최대값 → 문턱; 나머지 홀수 런 + 고장 런 주입 전 창 = 오탐 평가
    streams = {p: stream(p) for p in fp_files + fault_files}
    cal = fp_files[: max(1, len(fp_files) // 2)]; fp_eval = [p for p in fp_files if p not in cal]
    calstats = np.concatenate([streams[p][1][streams[p][0] > streams[p][0][0] + 30] for p in cal]) if cal else np.array([np.inf])
    thr = float(np.percentile(calstats, PCT))
    print(f"[{s}] calibrated threshold {thr:.4g} from {len(cal)} nf runs (alibi ERT threshold ≈ {float(np.nanmean(cd.thresholds)) if hasattr(cd, 'thresholds') else float('nan'):.4g})", flush=True)
    for p in fp_eval + fault_files:
        name = os.path.basename(p)[:-4]; f, sv = fault_sev(name); t, stat, flag_ert, tf = streams[p]
        conf = confirm((stat > thr).astype(int)); conf_ert = confirm(flag_ert)
        if f == "nf":
            w = t > t[0] + 30
            rows.append(dict(sensor=s, run=name, fault="nf", sev="-", t_fault="", fp=int(conf[w].any()), det="", fp_ert=int(conf_ert[w].any()), det_ert=""))
        else:
            if not np.isfinite(tf): continue
            w = (t > t[0] + 30) & (t < tf); post = np.where((t >= tf) & (conf == 1))[0]; post_e = np.where((t >= tf) & (conf_ert == 1))[0]
            rows.append(dict(sensor=s, run=name, fault=f, sev=sv, t_fault=round(tf, 1), fp=int(conf[w].any()), det=round(float(t[post[0]] - tf), 1) if len(post) else "",
                             fp_ert=int(conf_ert[w].any()), det_ert=round(float(t[post_e[0]] - tf), 1) if len(post_e) else ""))
        print(f"  {name}: {rows[-1]}", flush=True)
with open(f"{RES}/alibi/cases{TAG}.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# report
g = collections.defaultdict(list)
for r in rows: g[(r["sensor"], r["fault"], r["sev"])].append(r)
lines = ["# Alibi Detect Online MMD 대조군 (센서별 동일 알고리즘, MMDDriftOnline pytorch)", "",
         "기준 = 무고장 짝수 rep 특징(표준화, ≤3000점). 문턱 = (a) 데이터 보정: 홀수 rep 무고장 런 앞 절반의 통계량 최대값(다른 베이스라인과 같은 규칙) / (b) Alibi 기본 ERT 부트스트랩.",
         "검출 = 주입 후 통계량>문턱 연속 2스텝. 지연 = 시뮬 초(2 Hz 센서 0.5 s 해상도, 20 Hz 센서 5배 다운샘플 → 0.25 s). 오탐 = 무고장 평가 런 + 고장 런 주입 전 창(워밍업 30 s 제외).", "",
         "| 센서 | 고장 | 세기 | n | 검출 (a) | 중앙 지연 (a) | 오탐 (a) | 검출 (b ERT) | 오탐 (b ERT) |", "|---|---|---|---|---|---|---|---|---|"]
for k in sorted(g):
    rs = g[k]; det = [r["det"] for r in rs if r["det"] != ""]; dete = [r["det_ert"] for r in rs if r["det_ert"] != ""]
    med = f"{st.median(det):.1f}" if det else "–"
    lines.append(f"| {k[0]} | {k[1]} | {k[2]} | {len(rs)} | {len(det)}/{len(rs)} | {med} | {sum(r['fp'] for r in rs)} | {len(dete)}/{len(rs)} | {sum(r['fp_ert'] for r in rs)} |")
lines.insert(1, f"설정: window ×{WMULT:g} (lidar/camera {int(10*WMULT)}, gnss/imu {int(20*WMULT)} 스텝), 문턱 백분위 {PCT:g}")
open(f"{RES}/alibi/report{TAG}.md", "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
