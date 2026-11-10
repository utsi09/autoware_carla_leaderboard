#!/usr/bin/env python3
"""LiDAR·카메라 특징 추출(raw_vision 2 Hz 기록 → npz) — Alibi Detect Online MMD 대조군용.
LiDAR 특징(프레임당 14): log 점수, 평균/중앙 강도, 3~35 m 점 비율 8개 거리 구간(히스토그램, 정규화), >35 m 비율, <12 m 비율, 강도-거리 기울기(α̂ 유사).
카메라 특징(프레임당 20): 회색조 평균·표준편차, 라플라시안 분산, 인접 픽셀 차 평균(고주파), 16-bin 히스토그램(정규화).
출력 results/alibi/feat/vb-<f>-<s>-r<rep>.npz: lidar_t, lidar_feat, cam_t, cam_feat, t_fault(sim)."""
import sys, glob, os, csv, numpy as np
from pathlib import Path
from PIL import Image
RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results"); OUT = RES / "alibi" / "feat"
EDGES = np.array([3, 7, 11, 15, 19, 23, 27, 31, 35], dtype=np.float32)
def lidar_feats(xyz, inten):
    r = np.sqrt((xyz ** 2).sum(1)); m = r > 0.5; r = r[m]; I = inten[m].astype(np.float32)
    n = len(r)
    if n < 100: return np.zeros(14, np.float32)
    h, _ = np.histogram(r, EDGES); h = h / n
    far = (r > 35).mean(); near = (r < 12).mean()
    sel = (r >= 3) & (r < 40) & (I >= 6)
    slope = 0.0
    if sel.sum() > 200:
        A = np.c_[r[sel], np.ones(sel.sum())]; coef, *_ = np.linalg.lstsq(A, np.log(I[sel]), rcond=None); slope = -coef[0]
    return np.r_[np.log(n), I.mean() / 255.0, np.median(I) / 255.0, h, far, near, slope * 100].astype(np.float32)
def cam_feats(path):
    g = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    if g.shape[0] > 360: g = g[::2, ::2]
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    hf = np.abs(np.diff(g, axis=1)).mean()
    h, _ = np.histogram(g, 16, (0, 255)); h = h / g.size
    return np.r_[g.mean() / 255.0, g.std() / 255.0, lap.var() / 1e4, hf / 255.0, h].astype(np.float32)
def run(d):
    tag = os.path.basename(d); out = OUT / f"{tag}.npz"
    if out.exists(): return "skip"
    tf = np.nan
    try:
        rows = list(csv.DictReader(open(f"{d}/inj.csv")))
        on = [float(r["t_sim"]) for r in rows if r["value"] == "1"]; tf = on[0] if on else np.nan
    except Exception: pass
    lt, lf = [], []
    for p in sorted(glob.glob(f"{d}/lidar_*.npz")):
        z = np.load(p); off = z["off"]; xyz = z["xyz_cm"].astype(np.float32) * 0.01; inten = z["inten"]
        for i, t in enumerate(z["t_sim"]):
            lt.append(float(t)); lf.append(lidar_feats(xyz[off[i]:off[i + 1]], inten[off[i]:off[i + 1]]))
    ct, cf = [], []
    idx = f"{d}/cam_index.csv"
    if os.path.exists(idx):
        for r in csv.DictReader(open(idx)):
            p = f"{d}/cam/{int(r['idx']):06d}.png"
            if os.path.exists(p): ct.append(float(r["t_sim"])); cf.append(cam_feats(p))
    np.savez_compressed(out, t_fault=tf, lidar_t=np.array(lt, np.float32), lidar_feat=np.array(lf, np.float32), cam_t=np.array(ct, np.float32), cam_feat=np.array(cf, np.float32) if cf else np.zeros((0, 20), np.float32))
    return f"ok lidar={len(lt)} cam={len(ct)} tf={tf}"
if __name__ == "__main__":
    for d in sorted(glob.glob(str(RES / "raw_vision" / "vb-*"))):
        try: print(os.path.basename(d), run(d), flush=True)
        except Exception as e: print(os.path.basename(d), "ERR", e, flush=True)
