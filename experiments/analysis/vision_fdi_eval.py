#!/usr/bin/env python3
"""[2026-11-08] 비전(LiDAR·카메라) 베이스라인 비교 — 원시 2 Hz 기록(results/raw_vision/vb-*) + 표준 bag 통계(baseline_fdi/stats).

검출기 (모두 '구조 재구현'; 원문 알고리즘 세부가 아니라 공개된 구조를 따른다)
  WON  Won 2023: 구면좌표(채널×방위) 비트맵에서 '평소 돌아오던 셀'이 1 s(2프레임) 연속 비는 비율.
       CARLA 라이다는 기본 무작위 드롭(≈48%)이 있어 셀을 2링×2.4°로 묶는다. 기준 점유 = 1 s 지연 EMA ≥ 0.8.
  ZH   Zhang 2024: 거리×반사강도 2D 히스토그램과 2 s 지연 EMA 기준분포의 Jensen–Shannon 발산(비트). 학습 없음.
       보조 변형 ZH_near = 근거리(2.5–10 m, z>−1 m) 점 비율 (공간 분포만).
  LEE  Lee 2022: VGG 계열 축소 CNN(4블록) 4분류(normal/noise/blur/deadpx). 보정용 nf 런(짝수 rep) 프레임 + 합성 손상으로 CPU 학습,
       추론은 5개 224×224 크롭 평균. 경보 = argmax≠normal 1 s(2프레임) 연속.
  B0   Autoware 진단그래프 /autoware/perception/* 유닛 ERROR/STALE ≥1 s, 그리고 Autoware MRM(state≥2).
  OURS 감독기 재생(baseline_fdi_eval.ours_replay 결과, stats npz 의 t_ours).
규칙은 A안과 동일: 문턱 = nf 짝수 rep 의 FP 창 최대값, 오탐 = nf 홀수 rep + 고장 런 주입 전 창, 1 s 지속 확정, 지연은 시뮬 시간.

사용:
  --features [--workers N]   라이다 특징 → results/raw_vision/feat/<vb>.npz
  --train-lee [--epochs E]   CNN 학습 → results/raw_vision/lee_cnn.pt
  --infer-lee                CNN 추론 → feat/<vb>_lee.npz
  --report                   results/raw_vision/report.md, cases.csv
"""
import os, sys, csv, glob, math, json, argparse, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import baseline_fdi_eval as bfe   # wilson, mcnemar_p, first_idx, diag_paths, STATS, DIAG

RES = os.path.join(HERE, "..", "results")
RAW = os.path.join(RES, "raw_vision"); FEAT = os.path.join(RAW, "feat")
HZ = 2.0; PERSIST = 2            # 2 Hz → 2프레임 = 1 s 확정 (A안 PERSIST=10 @10 Hz 와 동일 시간)
CLASSES = ["normal", "noise", "blur", "deadpx"]

# ───────────────────────────── raw loading ─────────────────────────────
def lidar_frames(vbdir):
    for f in sorted(glob.glob(os.path.join(vbdir, "lidar_*.npz"))):
        d = np.load(f); off = d["off"]
        for i in range(len(d["t_sim"])):
            a, b = off[i], off[i + 1]
            yield float(d["t_sim"][i]), d["xyz_cm"][a:b].astype(np.float32) * 0.01, d["inten"][a:b], d["chan"][a:b]

def cam_index(vbdir):
    p = os.path.join(vbdir, "cam_index.csv")
    if not os.path.exists(p): return []
    rows = list(csv.DictReader(open(p)))
    return [(int(r["idx"]), float(r["t_sim"]), os.path.join(vbdir, "cam", f"{int(r['idx']):06d}.png")) for r in rows]

# ───────────────────────────── LiDAR detectors ─────────────────────────────
RING_G = 2; AZ_BIN = 2.4; NAZ = int(round(360 / AZ_BIN)); NRING = 128 // RING_G
R_EDGES = np.array([0, 2.5, 5, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 85, 120.0])
I_EDGES = np.array([0, 32, 64, 96, 128, 160, 192, 224, 256.0])
WON_LAG = 2; WON_A = 0.1; WON_REF = 0.8
ZH_LAG = 4; ZH_A = 0.1

def js_div(p, q, eps=1e-9):
    p = p + eps; q = q + eps; p /= p.sum(); q /= q.sum(); m = 0.5 * (p + q)
    return float(0.5 * np.sum(p * np.log2(p / m)) + 0.5 * np.sum(q * np.log2(q / m)))

def lidar_features(vbdir):
    name = os.path.basename(vbdir.rstrip("/")); out = os.path.join(FEAT, name + ".npz")
    if os.path.exists(out): return name, "cached"
    T, WON, ZH, NEAR, FAR, NPTS = [], [], [], [], [], []
    ema = None; ema_hist = []; occ_prev = None; href = None; href_hist = []
    for t, xyz, inten, chan in lidar_frames(vbdir):
        if len(xyz) < 100:
            T.append(t); WON.append(np.nan); ZH.append(np.nan); NEAR.append(np.nan); FAR.append(np.nan); NPTS.append(len(xyz)); continue
        r = np.hypot(xyz[:, 0], xyz[:, 1])
        az = ((np.degrees(np.arctan2(xyz[:, 1], xyz[:, 0])) + 180.0) / AZ_BIN).astype(int) % NAZ
        ring = np.minimum(chan.astype(int) // RING_G, NRING - 1)
        occ = np.zeros((NRING, NAZ), bool); occ[ring, az] = True
        # WON: 기준(1 s 전 EMA)이 '평소 돌아옴'인 셀 중 지금과 직전 프레임 모두 빈 비율
        if ema is None: ema = occ.astype(float)
        ref = ema_hist[-WON_LAG] if len(ema_hist) >= WON_LAG else None
        if ref is not None and occ_prev is not None:
            normal = ref >= WON_REF
            WON.append(float(np.mean((~occ[normal]) & (~occ_prev[normal]))) if normal.sum() > 50 else np.nan)
        else: WON.append(np.nan)
        ema_hist.append(ema.copy()); ema = (1 - WON_A) * ema + WON_A * occ; occ_prev = occ
        if len(ema_hist) > WON_LAG + 1: ema_hist.pop(0)
        # ZH: 거리×반사강도 분포 vs 2 s 지연 EMA 기준분포
        h, _, _ = np.histogram2d(r, inten.astype(float), bins=[R_EDGES, I_EDGES]); h = h.ravel() / max(h.sum(), 1)
        refh = href_hist[-ZH_LAG] if len(href_hist) >= ZH_LAG else None
        ZH.append(js_div(h.copy(), refh.copy()) if refh is not None else np.nan)
        href = h.copy() if href is None else (1 - ZH_A) * href + ZH_A * h
        href_hist.append(href.copy())
        if len(href_hist) > ZH_LAG + 1: href_hist.pop(0)
        NEAR.append(float(np.mean((r > 2.5) & (r < 10.0) & (xyz[:, 2] > -1.0))))
        FAR.append(float(np.mean(r > 35.0))); NPTS.append(len(xyz)); T.append(t)
    if not T: return name, "FAIL no lidar frames"
    os.makedirs(FEAT, exist_ok=True)
    np.savez_compressed(out, t=np.array(T), won=np.array(WON), zh=np.array(ZH), near=np.array(NEAR), far=np.array(FAR), npts=np.array(NPTS))
    return name, f"ok frames={len(T)} won_med={np.nanmedian(WON):.4f} zh_med={np.nanmedian(ZH):.4f}"

# ───────────────────────────── LEE (CNN) ─────────────────────────────
CROP = 224
def _torch():
    import torch, torch.nn as nn
    torch.set_num_threads(int(os.environ.get("LEE_THREADS", "8")))
    return torch, nn

def build_model():
    torch, nn = _torch()
    def block(i, o):
        return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
                             nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True), nn.MaxPool2d(2))
    class SmallVGG(nn.Module):
        def __init__(self):
            super().__init__()
            self.f = nn.Sequential(block(3, 32), block(32, 64), block(64, 128), block(128, 256))
            self.head = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Dropout(0.3), nn.Linear(256, len(CLASSES)))
        def forward(self, x): return self.head(self.f(x))
    return SmallVGG()

def corrupt(img, cls, rng):
    import cv2
    if cls == 0: return img
    if cls == 1:   # 가우시안 픽셀 노이즈 (cn 과 같은 유형; σ 는 넓게)
        s = rng.uniform(5.0, 40.0); return np.clip(img.astype(np.float32) + rng.normal(0, s, img.shape), 0, 255).astype(np.uint8)
    if cls == 2:   # 블러
        k = int(rng.choice([5, 9, 13])); return cv2.GaussianBlur(img, (k, k), 0)
    p = rng.uniform(0.01, 0.05); m = rng.random(img.shape[:2]) < p   # 죽은/포화 픽셀
    out = img.copy(); out[m] = np.where(rng.random((m.sum(), 1)) < 0.5, 0, 255).astype(np.uint8); return out

def to_tensor(torch, img):
    x = torch.from_numpy(np.ascontiguousarray(img[:, :, ::-1])).permute(2, 0, 1).float() / 255.0
    return (x - 0.5) / 0.25

def train_lee(cal_dirs, out_pt, epochs=6, step=2, seed=0):
    import cv2
    torch, nn = _torch(); rng = np.random.default_rng(seed); torch.manual_seed(seed)
    frames = []
    for d in cal_dirs:
        idx = cam_index(d)[::step]
        for _, _, p in idx:
            im = cv2.imread(p)
            if im is not None: frames.append(im)
    print(f"[lee] train frames={len(frames)} from {len(cal_dirs)} nf runs; classes={CLASSES}", flush=True)
    model = build_model(); opt = torch.optim.Adam(model.parameters(), 1e-3); lossf = nn.CrossEntropyLoss()
    H, W = frames[0].shape[:2]; B = 32
    for ep in range(epochs):
        model.train(); order = rng.permutation(len(frames)); tot = 0; correct = 0; n = 0; t0 = time.time()
        for s in range(0, len(order), B):
            xs, ys = [], []
            for j in order[s:s + B]:
                c = int(rng.integers(len(CLASSES))); y0 = int(rng.integers(0, H - CROP + 1)); x0 = int(rng.integers(0, W - CROP + 1))
                im = corrupt(frames[j][y0:y0 + CROP, x0:x0 + CROP], c, rng)
                if rng.random() < 0.5: im = im[:, ::-1]
                xs.append(to_tensor(torch, im)); ys.append(c)
            x = torch.stack(xs); y = torch.tensor(ys)
            opt.zero_grad(); out = model(x); loss = lossf(out, y); loss.backward(); opt.step()
            tot += float(loss) * len(ys); correct += int((out.argmax(1) == y).sum()); n += len(ys)
        print(f"[lee] epoch {ep + 1}/{epochs} loss={tot / n:.4f} acc={correct / n:.3f} ({time.time() - t0:.0f}s)", flush=True)
    torch.save(model.state_dict(), out_pt); return out_pt

def infer_lee(vbdir, pt):
    import cv2
    name = os.path.basename(vbdir.rstrip("/")); out = os.path.join(FEAT, name + "_lee.npz")
    if os.path.exists(out): return name, "cached"
    torch, nn = _torch(); model = build_model(); model.load_state_dict(torch.load(pt, map_location="cpu")); model.eval()
    idx = cam_index(vbdir)
    if not idx: return name, "FAIL no camera frames"
    T, P = [], []
    with torch.no_grad():
        for _, t, p in idx:
            im = cv2.imread(p)
            if im is None: continue
            H, W = im.shape[:2]; cy, cx = (H - CROP) // 2, (W - CROP) // 2
            crops = [im[0:CROP, 0:CROP], im[0:CROP, W - CROP:W], im[H - CROP:H, 0:CROP], im[H - CROP:H, W - CROP:W], im[cy:cy + CROP, cx:cx + CROP]]
            x = torch.stack([to_tensor(torch, c) for c in crops])
            pr = torch.softmax(model(x), 1).mean(0).numpy()
            T.append(t); P.append(pr)
    os.makedirs(FEAT, exist_ok=True)
    P = np.array(P); np.savez_compressed(out, t=np.array(T), p=P, cls=P.argmax(1))
    return name, f"ok frames={len(T)} normal_rate={np.mean(P.argmax(1) == 0):.3f}"

# ───────────────────────────── report ─────────────────────────────
def load_map():
    rows = list(csv.DictReader(open(os.path.join(RAW, "map.csv"))))
    return [r for r in rows if r["bag_tag"] and r["result"] not in ("CARLA_DIED", "INTERRUPTED", "SETUP_FAIL", "NONE")]

def b0_unit_times(tag, prefix):
    f = os.path.join(bfe.DIAG, tag + ".npz")
    if not os.path.exists(f): return None
    d = np.load(f); paths = bfe.diag_paths(); L = d["level"]
    idx = [i for i, p in enumerate(paths) if p.startswith(prefix) and i < L.shape[1]]
    if not idx: return None
    t = d["h"] if len(d["h"]) else d["t"]; bad = (L[:, idx] >= 2).any(axis=1).astype(int)
    starts = []; run0 = None
    for i in range(len(bad)):
        if bad[i] and run0 is None: run0 = i
        if (not bad[i] or i == len(bad) - 1) and run0 is not None:
            if t[min(i, len(t) - 1)] - t[run0] >= 1.0: starts.append(t[run0] + 1.0)
            run0 = None
    return starts

def report():
    rows = []
    for m in load_map():
        tag = m["bag_tag"]; sf = os.path.join(bfe.STATS, tag + ".npz"); vb = os.path.basename(m["raw_dir"].rstrip("/"))
        ff = os.path.join(FEAT, vb + ".npz"); lf = os.path.join(FEAT, vb + "_lee.npz")
        if not os.path.exists(sf): print("skip (no stats):", tag); continue
        s = dict(np.load(sf)); feat = dict(np.load(ff)) if os.path.exists(ff) else None; lee = dict(np.load(lf)) if os.path.exists(lf) else None
        t_inj = float(s["t_inj"]); t_move = float(s["t_move"]); t_end = float(s["t_end"])
        rows.append(dict(tag=tag, vb=vb, fault=m["fault"], sev=m["sev"], rep=int(m["rep"]), result=m["result"], s=s, feat=feat, lee=lee,
                         t_inj=t_inj, t_move=t_move, t_end=t_end, fp0=t_move + 10.0, fp1=(t_inj if not np.isnan(t_inj) else t_end)))
    nf = [r for r in rows if r["fault"] == "nf"]; nf_cal = [r for r in nf if r["rep"] % 2 == 0]; nf_tst = [r for r in nf if r["rep"] % 2 == 1]
    KEYS = ["won", "zh", "near"]
    def win_max(r, key, a, b):
        if r["feat"] is None: return np.nan
        t = r["feat"]["t"]; v = r["feat"][key]; m = (t >= a) & (t <= b) & ~np.isnan(v); return np.nanmax(v[m]) if m.any() else np.nan
    thr = {}
    for key in KEYS:
        vals = [win_max(r, key, r["fp0"], r["fp1"]) for r in nf_cal]; vals = [v for v in vals if not np.isnan(v)]
        thr[key] = float(np.max(vals)) if vals else np.nan
    DET = ["b0_perc", "b0_mrm", "won", "zh", "near", "lee", "ours"]
    LABEL = {"b0_perc": "B0 인지진단", "b0_mrm": "B0 MRM", "won": "WON 비트맵", "zh": "ZH 분포", "near": "ZH_near(변형)", "lee": "LEE CNN", "ours": "제안"}
    csvrows = []
    for r in rows:
        s = r["s"]; g = s["grid"]; gw = s["grid_wall"]; t_inj = r["t_inj"]; det = {}; fp = {}; detw = {}
        def put(key, tdet):
            det[key] = (tdet - t_inj) if (tdet is not None and not np.isnan(tdet) and not np.isnan(t_inj)) else np.nan
            detw[key] = (np.interp(tdet, g, gw) - float(s["t_inj_wall"])) if not np.isnan(det[key]) else np.nan
        if r["feat"] is not None:
            t = r["feat"]["t"]
            for key in KEYS:
                v = r["feat"][key]
                fp[key] = bfe.first_idx(t, v, thr[key], r["fp0"], r["fp1"], persist=PERSIST) >= 0
                k = bfe.first_idx(t, v, thr[key], t_inj, r["t_end"], persist=PERSIST) if not np.isnan(t_inj) else -1
                put(key, t[k] if k >= 0 else np.nan)
        else:
            for key in KEYS: fp[key] = False; det[key] = detw[key] = np.nan
        if r["lee"] is not None:
            t = r["lee"]["t"]; v = (r["lee"]["cls"] != 0).astype(float)
            fp["lee"] = bfe.first_idx(t, v, 0.5, r["fp0"], r["fp1"], persist=PERSIST) >= 0
            k = bfe.first_idx(t, v, 0.5, t_inj, r["t_end"], persist=PERSIST) if not np.isnan(t_inj) else -1
            put("lee", t[k] if k >= 0 else np.nan)
        else: fp["lee"] = False; det["lee"] = detw["lee"] = np.nan
        t_ours = float(s["t_ours"]); fp["ours"] = (not np.isnan(t_ours)) and (t_ours < r["fp1"])
        put("ours", t_ours if (not np.isnan(t_ours) and not np.isnan(t_inj) and t_ours >= t_inj) else np.nan)
        mrmv = s["mrm"]
        fp["b0_mrm"] = bfe.first_idx(g, mrmv, 1.5, r["fp0"], r["fp1"], persist=1) >= 0
        k = bfe.first_idx(g, mrmv, 1.5, t_inj, r["t_end"], persist=1) if not np.isnan(t_inj) else -1
        put("b0_mrm", g[k] if k >= 0 else np.nan)
        st = b0_unit_times(r["tag"], "/autoware/perception")
        if st is None: fp["b0_perc"] = False; det["b0_perc"] = detw["b0_perc"] = np.nan
        else:
            post = [x for x in st if not np.isnan(t_inj) and x >= t_inj]; pre = [x for x in st if r["fp0"] <= x < r["fp1"]]
            fp["b0_perc"] = bool(pre); put("b0_perc", post[0] if post else np.nan)
        r["det"] = det; r["fp"] = fp
        csvrows.append(dict(tag=r["tag"], vb=r["vb"], fault=r["fault"], sev=r["sev"], rep=r["rep"], result=r["result"],
                            t_inj_rel=round(t_inj - r["t_move"], 1) if not np.isnan(t_inj) else "", post_s=round(r["t_end"] - t_inj, 1) if not np.isnan(t_inj) else "",
                            sim_rate=round(float(s["sim_rate"]), 2),
                            **{f"det_{k}": (round(v, 2) if not np.isnan(v) else "") for k, v in det.items()},
                            **{f"detw_{k}": (round(v, 2) if not np.isnan(v) else "") for k, v in detw.items()},
                            **{f"fp_{k}": int(v) for k, v in fp.items()}))
    os.makedirs(RAW, exist_ok=True)
    with open(os.path.join(RAW, "cases.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(csvrows[0].keys())); w.writeheader(); w.writerows(csvrows)
    # ---- tables
    L = []
    L.append(f"# 비전 베이스라인 비교 (원시 2 Hz 기록, {len(rows)}런; 생성 {time.strftime('%Y-%m-%d %H:%M')})\n")
    L.append("검출기: " + ", ".join(f"{LABEL[k]}" for k in DET) + ". 모든 검출기 1 s 지속 확정, 지연 = 확정 시각 − 주입 시각(시뮬 초). ")
    L.append(f"문턱: nf 짝수 rep {len(nf_cal)}런 FP 창 최대값 → WON {thr['won']:.4f}, ZH {thr['zh']:.4f} bit, ZH_near {thr['near']:.4f}; LEE 는 argmax. "
             f"오탐 평가: nf 홀수 rep {len(nf_tst)}런 + 고장 런 주입 전 창.\n")
    L.append("| 고장 | n | " + " | ".join(LABEL[k] for k in DET) + " |"); L.append("|---|---|" + "---|" * len(DET))
    groups = sorted({(r["fault"], r["sev"]) for r in rows if r["fault"] != "nf"}, key=lambda x: (["lso", "lcl", "cn"].index(x[0]) if x[0] in ("lso", "lcl", "cn") else 9, x[1] != "mid"))
    for f, sv in groups:
        G = [r for r in rows if r["fault"] == f and r["sev"] == sv and not np.isnan(r["t_inj"])]; n = len(G)
        cells = []
        for k in DET:
            lat = np.array([r["det"][k] for r in G]); hit = int(np.sum(~np.isnan(lat)))
            lo, hi = bfe.wilson(hit, n)
            if hit: cells.append(f"{hit}/{n} ({100 * lo:.0f}–{100 * hi:.0f}%) {np.nanmedian(lat):.1f} s")
            else: cells.append(f"0/{n} ({100 * lo:.0f}–{100 * hi:.0f}%)")
        L.append(f"| {f}-{sv} | {n} | " + " | ".join(cells) + " |")
    L.append("\n## 오탐 (경보가 난 런/창 수)\n")
    L.append("| 구간 | n | " + " | ".join(LABEL[k] for k in DET) + " |"); L.append("|---|---|" + "---|" * len(DET))
    for name, G in (("nf 보정용(짝수 rep)", nf_cal), ("nf 평가용(홀수 rep)", nf_tst), ("고장 런 주입 전 창", [r for r in rows if r["fault"] != "nf" and not np.isnan(r["t_inj"])])):
        L.append(f"| {name} | {len(G)} | " + " | ".join(str(sum(int(r["fp"][k]) for r in G)) for k in DET) + " |")
    L.append("\n## McNemar (제안 vs 각 검출기; b=제안만, c=비교만 검출)\n")
    L.append("| 고장 | " + " | ".join(LABEL[k] for k in DET if k != "ours") + " |"); L.append("|---|" + "---|" * (len(DET) - 1))
    for f, sv in groups:
        G = [r for r in rows if r["fault"] == f and r["sev"] == sv and not np.isnan(r["t_inj"])]; cells = []
        for k in DET:
            if k == "ours": continue
            b = sum(1 for r in G if not np.isnan(r["det"]["ours"]) and np.isnan(r["det"][k])); c = sum(1 for r in G if np.isnan(r["det"]["ours"]) and not np.isnan(r["det"][k]))
            p = bfe.mcnemar_p(b, c); cells.append(f"b={b} c={c} p={p:.3f}" if not np.isnan(p) else f"b={b} c={c} —")
        L.append(f"| {f}-{sv} | " + " | ".join(cells) + " |")
    L.append("\n## 런별\n"); L.append("| 런 | 결과 | 주입(출발+s) | " + " | ".join(LABEL[k] for k in DET) + " |"); L.append("|---|---|---|" + "---|" * len(DET))
    for r in sorted(rows, key=lambda r: (r["fault"], r["sev"], r["rep"])):
        L.append(f"| {r['vb']} | {r['result']} | {(r['t_inj'] - r['t_move']) if not np.isnan(r['t_inj']) else float('nan'):.1f} | " +
                 " | ".join((f"{r['det'][k]:.1f}" if not np.isnan(r['det'][k]) else ("FP" if r["fp"][k] else "—")) for k in DET) + " |")
    open(os.path.join(RAW, "report.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:len(groups) + 6]))
    print(f"→ {os.path.join(RAW, 'report.md')}, cases.csv ({len(csvrows)} rows)")

# ───────────────────────────── main ─────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", action="store_true"); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--train-lee", action="store_true"); ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--infer-lee", action="store_true"); ap.add_argument("--report", action="store_true")
    ap.add_argument("--dirs", nargs="*", default=None, help="vb 디렉터리 지정(기본: results/raw_vision/vb-*)")
    a = ap.parse_args()
    dirs = a.dirs if a.dirs else sorted(glob.glob(os.path.join(RAW, "vb-*")))
    dirs = [d for d in dirs if glob.glob(os.path.join(d, "lidar_*.npz"))]
    if a.features:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(a.workers) as ex:
            for name, msg in ex.map(lidar_features, dirs): print(f"[feat] {name}: {msg}", flush=True)
    if a.train_lee:
        cal = [d for d in dirs if os.path.basename(d).startswith("vb-nf-") and int(os.path.basename(d).split("-r")[-1]) % 2 == 0]
        train_lee(cal, os.path.join(RAW, "lee_cnn.pt"), epochs=a.epochs)
    if a.infer_lee:
        pt = os.path.join(RAW, "lee_cnn.pt")
        for d in dirs:
            name, msg = infer_lee(d, pt); print(f"[lee] {name}: {msg}", flush=True)
    if a.report: report()
