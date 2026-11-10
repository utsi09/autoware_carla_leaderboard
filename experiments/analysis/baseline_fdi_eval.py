#!/usr/bin/env python3
"""[2026-11-08] A안: 순정 bag 캐시(baseline_fdi_extract.py) 위에서 검출기 4종을 같은 스트림에 돌려 검출률·오탐·지연 비교.
  YU   : Yu et al. 2021 상태영역 χ² (GNSS/INS 느슨결합 KF; 사전–사후 상태 차이를 공분산 차이의 의사역으로 정규화 = 혁신 χ²와 동치,
         IGG-III 강건 가중으로 필터 오염 방지; W=10 갱신 창 평균) — 원문 미열람, 초록·관련문헌 기준 재구현
  GOS  : Huang & Su 2015 일반화 관측기(EKF 뱅크: 전체 + 센서 1개씩 제외 4개; 센서별 1 s 창 평균 NIS/dof 의 최대) — 재구현
  OURS : mrm_supervisor 의 측위 채널 오프라인 재생 (loc_meas GNSS–EKF 잔차+침묵, loc_jump, IMU 바이어스/ZUPT, cdr capability/localization)
         → health=min(perception, cap_loc); 밴드(health<0.7) 1 s 또는 바닥(≤0.3) 2 s 확정 시각 = 검출
  B0   : Autoware 자체 — (a) 진단그래프 ERROR 노드 수 증가(1 s 지속) (b) MRM 상태 ≥2
사용: baseline_fdi_eval.py --stats [--workers 3] [--only SUBSTR]   → results/baseline_fdi/stats/<tag>.npz
      baseline_fdi_eval.py --report                                → results/baseline_fdi/report.md, cases.csv
"""
import os, sys, csv, math, glob, argparse, collections
import numpy as np
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CACHE = os.path.join(RES, "baseline_fdi", "cache"); STATS = os.path.join(RES, "baseline_fdi", "stats")
LEVER = 1.27          # GNSS 안테나가 base_link 보다 앞에 있는 거리 [m] (정상 구간 실측 +1.23~1.43)
def wrap(a): return (a + np.pi) % (2 * np.pi) - np.pi

# ───────────────────────────── YU: GNSS/INS KF + state-domain chi-square ─────────────────────────────
def yu_stats(imu, vel, gnss, ndt, t_from, sig_v=0.3, sig_w=0.02, sig_g=0.1, k0=1.5, k1=4.0, W=10):
    i0 = int(np.searchsorted(imu[:, 0], t_from)); i0 = min(max(i0, 1), len(imu) - 1)
    gi = int(np.searchsorted(gnss[:, 0], imu[i0, 0]))
    if gi >= len(gnss): return np.zeros((0, 2))
    j = min(int(np.searchsorted(ndt[:, 0], imu[i0, 0])), len(ndt) - 1)
    x = np.array([gnss[gi, 1] - LEVER * math.cos(ndt[j, 3]), gnss[gi, 2] - LEVER * math.sin(ndt[j, 3]), ndt[j, 3]])
    P = np.diag([1.0, 1.0, 0.05]); R = np.eye(2) * sig_g ** 2; H = np.array([[1, 0, 0], [0, 1, 0]], float)
    win = collections.deque(maxlen=W); out = []
    vcol = vel[:, 1] if len(vel) == len(imu) else np.interp(imu[:, 0], vel[:, 0], vel[:, 1])
    for i in range(i0 + 1, len(imu)):
        dt = imu[i, 0] - imu[i - 1, 0]
        if dt <= 0 or dt > 1.0: continue
        v, w = vcol[i], imu[i, 4]; c, s = math.cos(x[2]), math.sin(x[2])
        x = x + np.array([v * c * dt, v * s * dt, w * dt]); x[2] = wrap(x[2])
        F = np.array([[1, 0, -v * s * dt], [0, 1, v * c * dt], [0, 0, 1]]); G = np.array([[c * dt, 0], [s * dt, 0], [0, dt]])
        P = F @ P @ F.T + G @ np.diag([sig_v ** 2, sig_w ** 2]) @ G.T + np.diag([1e-4, 1e-4, 1e-5]) * dt
        while gi < len(gnss) and gnss[gi, 0] <= imu[i, 0] + 0.01:
            z = np.array([gnss[gi, 1] - LEVER * math.cos(x[2]), gnss[gi, 2] - LEVER * math.sin(x[2])]); tg = gnss[gi, 0]; gi += 1
            nu = z - x[:2]; S = P[:2, :2] + R
            # 사전–사후 차이 β=Kν, Cov(β)=P⁻−P⁺=KSKᵀ → λ=βᵀ(KSKᵀ)⁺β (= νᵀS⁻¹ν, K 열충분계수)
            K = P[:, :2] @ np.linalg.inv(S); beta = K @ nu; T = K @ S @ K.T
            lam = float(beta @ np.linalg.pinv(T, rcond=1e-10) @ beta)
            nis = float(nu @ np.linalg.inv(S) @ nu)       # 혁신 χ² (동치 확인용)
            win.append(lam); out.append((tg, float(np.mean(win)), lam, nis))
            r = np.abs(nu) / np.sqrt(np.diag(S))           # IGG-III 강건 가중 (필터 보호용; 통계량은 비가중)
            wgt = np.where(r <= k0, 1.0, np.where(r <= k1, (k0 / np.maximum(r, 1e-9)) * ((k1 - r) / (k1 - k0)) ** 2, 1e-6))
            Rr = R / np.maximum(wgt, 1e-6); Sr = P[:2, :2] + Rr; Kr = P[:, :2] @ np.linalg.inv(Sr)
            x = x + Kr @ nu; x[2] = wrap(x[2]); P = (np.eye(3) - Kr @ H) @ P
    return np.array(out) if out else np.zeros((0, 4))

# ───────────────────────────── GOS: EKF bank (Huang & Su) ─────────────────────────────
SENSORS = ("gnss", "ndt", "imu", "wheel"); DOF = {"gnss": 2, "ndt": 3, "imu": 1, "wheel": 1}
class EKF5:
    def __init__(self, x0, sa=1.0, salpha=0.3):
        self.x = np.array(x0, float); self.P = np.diag([1.0, 1.0, 0.05, 1.0, 0.1]); self.sa, self.salpha = sa, salpha
    def predict(self, dt):
        px, py, psi, v, w = self.x; c, s = math.cos(psi), math.sin(psi)
        self.x = np.array([px + v * c * dt, py + v * s * dt, wrap(psi + w * dt), v, w])
        F = np.eye(5); F[0, 2] = -v * s * dt; F[0, 3] = c * dt; F[1, 2] = v * c * dt; F[1, 3] = s * dt; F[2, 4] = dt
        Q = np.diag([1e-4, 1e-4, 1e-5, self.sa ** 2, self.salpha ** 2]) * dt
        self.P = F @ self.P @ F.T + Q
    def update(self, kind, z):
        x = self.x
        if kind == "gnss":
            c, s = math.cos(x[2]), math.sin(x[2]); h = np.array([x[0] + LEVER * c, x[1] + LEVER * s])
            H = np.array([[1, 0, -LEVER * s, 0, 0], [0, 1, LEVER * c, 0, 0]], float); R = np.eye(2) * 0.1 ** 2; nu = z - h
        elif kind == "ndt":
            h = x[:3].copy(); H = np.zeros((3, 5)); H[0, 0] = H[1, 1] = H[2, 2] = 1; R = np.diag([0.1 ** 2, 0.1 ** 2, 0.02 ** 2])
            nu = z - h; nu[2] = wrap(nu[2])
        elif kind == "imu":
            h = x[4:5]; H = np.zeros((1, 5)); H[0, 4] = 1; R = np.eye(1) * 0.02 ** 2; nu = z - h
        else:
            h = x[3:4]; H = np.zeros((1, 5)); H[0, 3] = 1; R = np.eye(1) * 0.1 ** 2; nu = z - h
        S = H @ self.P @ H.T + R; Si = np.linalg.inv(S); nis = float(nu @ Si @ nu)
        K = self.P @ H.T @ Si; self.x = self.x + K @ nu; self.x[2] = wrap(self.x[2]); self.P = (np.eye(5) - K @ H) @ self.P
        return nis

def gos_stats(imu, vel, gnss, ndt, t_from, grid, win_s=1.0):
    i0 = int(np.searchsorted(imu[:, 0], t_from)); i0 = min(max(i0, 1), len(imu) - 1)
    j = min(int(np.searchsorted(ndt[:, 0], imu[i0, 0])), len(ndt) - 1)
    x0 = [ndt[j, 1], ndt[j, 2], ndt[j, 3], 0.0, 0.0]
    names = ["all"] + [f"no_{s}" for s in SENSORS]; bank = {n: EKF5(x0) for n in names}
    excl = {"all": None, **{f"no_{s}": s for s in SENSORS}}
    vcol = vel[:, 1] if len(vel) == len(imu) else np.interp(imu[:, 0], vel[:, 0], vel[:, 1])
    gi = int(np.searchsorted(gnss[:, 0], imu[i0, 0])); ni = int(np.searchsorted(ndt[:, 0], imu[i0, 0]))
    rec = {n: {s: [] for s in SENSORS} for n in names}       # (t, nis)
    def upd(kind, z, t):
        for n, f in bank.items():
            if excl[n] != kind: rec[n][kind].append((t, f.update(kind, np.array(z, float))))
    for i in range(i0 + 1, len(imu)):
        dt = imu[i, 0] - imu[i - 1, 0]
        if dt <= 0 or dt > 1.0: continue
        for f in bank.values(): f.predict(dt)
        t = imu[i, 0]
        upd("imu", [imu[i, 4]], t); upd("wheel", [vcol[i]], t)
        while gi < len(gnss) and gnss[gi, 0] <= t + 0.01: upd("gnss", gnss[gi, 1:3], gnss[gi, 0]); gi += 1
        while ni < len(ndt) and ndt[ni, 0] <= t + 0.01: upd("ndt", ndt[ni, 1:4], ndt[ni, 0]); ni += 1
    # 창 평균 NIS/dof → 그리드. 필터 통계량 = 포함 센서 중 최대
    out = {}
    for n in names:
        best = np.full(len(grid), np.nan)
        for s in SENSORS:
            if excl[n] == s or not rec[n][s]: continue
            a = np.array(rec[n][s]); ts, v = a[:, 0], a[:, 1] / DOF[s]
            cs = np.concatenate([[0.0], np.cumsum(v)])
            hi = np.searchsorted(ts, grid, side="right"); lo = np.searchsorted(ts, grid - win_s, side="right")
            cnt = hi - lo; m = np.where(cnt > 0, (cs[hi] - cs[lo]) / np.maximum(cnt, 1), np.nan)
            best = np.fmax(best, m)
        out[n] = best
    return out

# ───────────────────────────── OURS: supervisor localization channels replay ─────────────────────────────
def ours_replay(d, grid):
    imu, ks, gnss, sc = d["imu"], d["ks"], d["gnss"], d["score"]
    ev = [(t, 0, i) for i, t in enumerate(ks[:, 0])] + [(t, 1, i) for i, t in enumerate(gnss[:, 0])] + [(t, 2, i) for i, t in enumerate(imu[:, 0])] + [(t, 3, i) for i, t in enumerate(grid)]
    ev.sort()
    S = dict(pose=None, speed=None, last_odom=None, loc_jump=1.0, loc_meas=1.0, meas_base=0.0, meas_n=0, meas_last=None, sim_now=None,
             ekf_win=collections.deque(), imu_win=collections.deque(), imu_t0=None, imu_calib_n=0, imu_dmean=0.0, imu_base_m2=0.0,
             imu_mean_sum=0.0, imu_mean_n=0, imu_bias_bad=None, imu_bias=1.0, zupt_win=collections.deque(), zupt_bad=None, zupt=1.0,
             armed=False, armed_ticks=0, band=0, floor=0)
    si = 0; perception = np.nan; cap_loc_cdr = np.nan
    out_health = np.full(len(grid), np.nan); out_caploc = np.full(len(grid), np.nan); t_det = np.nan; det_kind = ""
    for t, kind, i in ev:
        if kind == 0:   # odom
            x, y, vx, wz = ks[i, 1], ks[i, 2], ks[i, 4], ks[i, 5]
            S["speed"] = abs(vx); S["sim_now"] = t; S["ekf_win"].append((t, wz))
            if S["last_odom"] is not None:
                px, py, pt, pv = S["last_odom"]; dt = t - pt
                if 0.0 < dt < 1.0:
                    jump = abs(math.hypot(x - px, y - py) - pv * dt); inst = math.exp(-max(0.0, jump - 0.3) / 0.5)
                    S["loc_jump"] = 0.9 * S["loc_jump"] + 0.1 * inst
            S["last_odom"] = (x, y, t, S["speed"]); S["pose"] = (x, y)
        elif kind == 1:  # gnss
            S["meas_last"] = t
            if S["pose"] is None: continue
            r = math.hypot(S["pose"][0] - gnss[i, 1], S["pose"][1] - gnss[i, 2])
            if S["meas_n"] < 60:
                S["meas_base"] = r if S["meas_n"] == 0 else 0.9 * S["meas_base"] + 0.1 * r; S["meas_n"] += 1; continue
            excess = max(0.0, r - S["meas_base"] - 0.2); S["loc_meas"] = 0.9 * S["loc_meas"] + 0.1 * math.exp(-excess / 0.55)
        elif kind == 2:  # imu
            wz = imu[i, 4]
            if S["speed"] is not None and S["speed"] < 0.1:
                S["zupt_win"].append((t, wz))
                while S["zupt_win"] and t - S["zupt_win"][0][0] > 1.0: S["zupt_win"].popleft()
                if len(S["zupt_win"]) >= 10:
                    zv = [v for _, v in S["zupt_win"]]; zm = sum(zv) / len(zv); zvar = sum((v - zm) ** 2 for v in zv) / len(zv)
                    if abs(zm) > 0.05 or zvar > 0.01:
                        if S["zupt_bad"] is None: S["zupt_bad"] = t
                        if t - S["zupt_bad"] >= 2.0:
                            ex = max(abs(zm) - 0.05, 0.0) + max(zvar - 0.01, 0.0); S["zupt"] = 0.9 * S["zupt"] + 0.1 * math.exp(-ex / 0.1)
                    else: S["zupt_bad"] = None; S["zupt"] = min(1.0, S["zupt"] + 0.02)
            else:
                S["zupt_win"].clear(); S["zupt_bad"] = None; S["zupt"] = min(1.0, S["zupt"] + 0.005)
            if S["imu_t0"] is None:
                if S["speed"] is None or S["speed"] < 1.0: continue
                S["imu_t0"] = t
            if t - S["imu_t0"] < 3.0:
                if S["imu_win"]:
                    dd = wz - S["imu_win"][-1][1]; S["imu_calib_n"] += 1; delta = dd - S["imu_dmean"]
                    S["imu_dmean"] += delta / S["imu_calib_n"]; S["imu_base_m2"] += delta * (dd - S["imu_dmean"])
                S["imu_mean_sum"] += wz; S["imu_mean_n"] += 1; S["imu_win"].append((t, wz)); continue
            S["imu_win"].append((t, wz))
            while S["imu_win"] and t - S["imu_win"][0][0] > 3.0: S["imu_win"].popleft()
            n = len(S["imu_win"])
            if n < 10 or S["imu_calib_n"] < 5: continue
            mean = sum(v for _, v in S["imu_win"]) / n
            while S["ekf_win"] and t - S["ekf_win"][0][0] > 3.0: S["ekf_win"].popleft()
            off = abs(mean - sum(v for _, v in S["ekf_win"]) / len(S["ekf_win"])) if len(S["ekf_win"]) >= 5 else 0.0
            if off > 0.2:
                if S["imu_bias_bad"] is None: S["imu_bias_bad"] = t
                bs = t - S["imu_bias_bad"] >= 3.0
            else: S["imu_bias_bad"] = None; bs = False
            S["imu_bias"] = 0.9 * S["imu_bias"] + 0.1 * (math.exp(-max(0.0, off - 0.2) / 0.2) if bs else 1.0)
        else:            # tick 10 Hz
            while si < len(sc) and sc[si, 0] <= t:
                if not np.isnan(sc[si, 4]): perception = sc[si, 4]
                if not np.isnan(sc[si, 1]): cap_loc_cdr = sc[si, 1]
                si += 1
            if S["armed"] and S["meas_last"] is not None and S["sim_now"] is not None:
                stale = S["sim_now"] - S["meas_last"]
                if stale > 1.0: S["loc_meas"] = min(S["loc_meas"], math.exp(-(stale - 1.0) / 0.8))
            imu_health = min(S["imu_bias"], S["zupt"])
            cap_loc = min(cap_loc_cdr if not np.isnan(cap_loc_cdr) else 1.0, S["loc_jump"], S["loc_meas"], imu_health)
            p = perception if not np.isnan(perception) else 1.0
            health = min(p, cap_loc); out_health[i] = health; out_caploc[i] = cap_loc
            if not S["armed"]:
                if not np.isnan(perception) and perception >= 0.7:
                    S["armed_ticks"] += 1
                    if S["armed_ticks"] >= 30: S["armed"] = True
                else: S["armed_ticks"] = 0
                continue
            S["floor"] = S["floor"] + 1 if health <= 0.3 else 0
            S["band"] = S["band"] + 1 if health < 0.7 else 0
            if np.isnan(t_det) and (S["floor"] >= 20 or S["band"] >= 10):
                t_det = t; det_kind = "floor" if S["floor"] >= 20 else "band"
    return out_health, out_caploc, t_det, det_kind

# ───────────────────────────── per-case stats ─────────────────────────────
def hold(ts, vals, grid):
    idx = np.searchsorted(ts, grid, side="right") - 1
    out = np.where(idx >= 0, vals[np.clip(idx, 0, len(vals) - 1)], np.nan); return out

def case_stats(tag):
    out = os.path.join(STATS, tag + ".npz")
    if os.path.exists(out): return tag, "cached"
    try:
        d = dict(np.load(os.path.join(CACHE, tag + ".npz")))
        if len(d["ndt"]) < 50 or len(d["imu"]) < 50: return tag, "FAIL short"
        # 시간축: 시뮬이 벽시계보다 빠르게 돌아(IMU 수신 ~28 Hz vs 시뮬 20 Hz) 벽시계 dt 로 적분하면 속도·요레이트가 ~20% 작게 들어간다.
        # IMU (수신시각, 헤더 시뮬시각) 쌍으로 단조 사상을 만들어 모든 토픽을 시뮬 시간으로 옮긴다. 지연 보고는 다시 벽시계로 환산.
        tw, th = d["imu"][:, 0].copy(), d["imu"][:, 1].copy()
        to_sim = lambda t: np.interp(t, tw, th); to_wall = lambda t: np.interp(t, th, tw)
        for k in ("imu", "vel", "steer", "gnss", "ndt", "ks", "score", "mrm", "diag", "inj", "tp", "nvtl"):
            if len(d[k]): d[k][:, 0] = to_sim(d[k][:, 0])
        d["imu"][:, 0] = th
        imu, vel, gnss, ndt, ks, mrm, diag, inj = d["imu"], d["vel"], d["gnss"], d["ndt"], d["ks"], d["mrm"], d["diag"], d["inj"]
        t_end = imu[-1, 0]; t_inj = inj[0, 0] if len(inj) else np.nan
        mv = vel[vel[:, 1] > 1.0]
        if not len(mv): return tag, "FAIL never moved"
        t_move = mv[0, 0]; t_from = max(t_move - 3.0, ndt[0, 0], gnss[0, 0] if len(gnss) else 0)
        grid = np.arange(t_from, t_end, 0.1)
        yu = yu_stats(imu, vel, gnss, ndt, t_from)
        yu_g = hold(yu[:, 0], yu[:, 1], grid) if len(yu) else np.full(len(grid), np.nan)
        # 1 s 이상 GNSS 갱신이 없으면 통계량 무효(NaN) — gb 블랙아웃은 YU 가 볼 수 없음
        if len(yu):
            last = hold(yu[:, 0], yu[:, 0], grid); yu_g = np.where(grid - last > 1.0, np.nan, yu_g)
        yu_eq = float(np.max(np.abs(yu[:, 2] - yu[:, 3]) / np.maximum(yu[:, 3], 1e-9))) if len(yu) else np.nan   # |λ_state − NIS| / NIS 최대
        gos = gos_stats(imu, vel, gnss, ndt, t_from, grid)
        health, caploc, t_ours, ours_kind = ours_replay(d, grid)
        mrm_g = hold(mrm[:, 0], mrm[:, 1], grid) if len(mrm) else np.full(len(grid), np.nan)      # 11/04 초기 bag 엔 mrm/diag 미녹화
        nerr_g = hold(diag[:, 0], diag[:, 2], grid) if len(diag) else np.full(len(grid), np.nan)
        np.savez_compressed(out, grid=grid, grid_wall=to_wall(grid), t_inj=t_inj, t_inj_wall=(to_wall(t_inj) if not np.isnan(t_inj) else np.nan),
                            t_move=t_move, t_end=t_end, sim_rate=(th[-1] - th[0]) / max(tw[-1] - tw[0], 1e-6), yu_eq=yu_eq, yu=yu_g, gos_all=gos["all"],
                            **{f"gos_{s}": gos[f"no_{s}"] for s in SENSORS}, health=health, caploc=caploc, t_ours=t_ours, ours_kind=ours_kind,
                            mrm=mrm_g, nerr=nerr_g)
        return tag, f"ok t_move={t_move - d['t0']:.1f} t_inj={(t_inj - d['t0']) if not np.isnan(t_inj) else -1:.1f} ours_det={(t_ours - t_inj) if not np.isnan(t_ours) and not np.isnan(t_inj) else float('nan'):.1f}"
    except Exception as e:
        import traceback; return tag, "FAIL " + traceback.format_exc().splitlines()[-1]

def meta(tag):
    p = tag.split("-"); return dict(fault=p[1], sev=p[2], npc=p[3], rep=p[4].lstrip("r"))


DIAG = os.path.join(RES, "baseline_fdi", "diag")
def diag_paths():
    f = os.path.join(RES, "baseline_fdi", "diag_struct.yaml")
    if not os.path.exists(f): return []
    return [l.split("path:", 1)[1].strip().strip("'\"") for l in open(f) if l.strip().startswith("- path:")]
def b0_loc_times(tag, to_sim_pairs):
    """측위 유닛(/autoware/localization/...) 중 하나라도 level>=2(ERROR/STALE) 가 1 s 이상 지속되는 구간의 확정(시작+1 s) 시각들 [sim s]. 없으면 []."""
    f = os.path.join(DIAG, tag + ".npz")
    if not os.path.exists(f): return None
    d = np.load(f); paths = diag_paths(); L = d["level"]
    idx = [i for i, p in enumerate(paths) if p.startswith("/autoware/localization") and i < L.shape[1]]
    if not idx: return None
    t = d["h"] if len(d["h"]) else d["t"]                      # 헤더(시뮬) 시각 우선
    bad = (L[:, idx] >= 2).any(axis=1).astype(int)
    starts = []; run0 = None
    for i in range(len(bad)):
        if bad[i] and run0 is None: run0 = i
        if (not bad[i] or i == len(bad) - 1) and run0 is not None:
            if t[min(i, len(t) - 1)] - t[run0] >= 1.0: starts.append(t[run0] + 1.0)      # 1 s 지속 확정 시각
            run0 = None
    return starts

# ───────────────────────────── report ─────────────────────────────
from math import comb
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))
def mcnemar_p(b, c):
    """정확 McNemar (이항): b=제안만 검출, c=비교만 검출."""
    n = b + c
    if n == 0: return np.nan
    k = min(b, c); p = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return min(1.0, p)
def first_idx(grid, stat, thr, t0, t1, persist=2):
    """경보 '확정' 시각 인덱스: stat>thr 가 persist 샘플 연속 유지된 마지막 샘플(= 실제 경보가 울리는 순간; 제안 방식의 밴드 확정과 동일 정의)."""
    m = (grid >= t0) & (grid <= t1) & ~np.isnan(stat); idx = np.where(m & (stat > thr))[0]
    for k in idx:
        if all((k + j) < len(stat) and stat[k + j] > thr for j in range(persist)): return int(k + persist - 1)
    return -1

PERSIST = 10   # 경보 확정에 필요한 연속 샘플 수(10 Hz → 1 s), 제안 방식의 밴드 홀드와 동일
def report():
    rows = []
    for f in sorted(glob.glob(os.path.join(STATS, "*.npz"))):
        tag = os.path.basename(f)[:-4]
        if not tag.startswith("stock-"): continue          # ours 검증 bag 은 비교표에서 제외
        s = dict(np.load(f)); m = meta(tag)
        t_inj = float(s["t_inj"]); t_move = float(s["t_move"]); t_end = float(s["t_end"]); grid = s["grid"]
        rows.append(dict(tag=tag, **m, t_inj=t_inj, t_inj_wall=float(s["t_inj_wall"]), t_move=t_move, t_end=t_end,
                         fp0=t_move + 10.0, fp1=(t_inj if not np.isnan(t_inj) else t_end), s=s, grid=grid, gw=s["grid_wall"]))
    nf = [r for r in rows if r["fault"] == "nf"]
    nf_cal = [r for r in nf if int(r["rep"]) % 2 == 0]; nf_tst = [r for r in nf if int(r["rep"]) % 2 == 1]
    def win_max(r, key, a, b):
        g = r["grid"]; v = r["s"][key]; m = (g >= a) & (g <= b) & ~np.isnan(v); return np.nanmax(v[m]) if m.any() else np.nan
    thr = {}
    for key in ("yu", "gos_all"):
        vals = [win_max(r, key, r["fp0"], r["fp1"]) for r in nf_cal]; vals = [v for v in vals if not np.isnan(v)]
        thr[key] = float(np.max(vals)) * 1.0 if vals else np.nan
    thr_text = {"yu": 4.53, "gos_all": 1.84}     # 교과서: YU χ²(2W)/W, GOS χ²(40)/40, α=1e-3
    csvrows = []
    for r in rows:
        g, gw, s = r["grid"], r["gw"], r["s"]; t_inj = r["t_inj"]; det = {}; detw = {}; fp = {}
        def put(key, k):
            det[key] = (g[k] - t_inj) if k >= 0 else np.nan; detw[key] = (gw[k] - r["t_inj_wall"]) if k >= 0 else np.nan
        for key in ("yu", "gos_all"):
            fp[key] = first_idx(g, s[key], thr[key], r["fp0"], r["fp1"], persist=PERSIST) >= 0
            put(key, first_idx(g, s[key], thr[key], t_inj, r["t_end"], persist=PERSIST) if not np.isnan(t_inj) else -1)
            fp[key + "_tb"] = first_idx(g, s[key], thr_text[key], r["fp0"], r["fp1"], persist=PERSIST) >= 0
            put(key + "_tb", first_idx(g, s[key], thr_text[key], t_inj, r["t_end"], persist=PERSIST) if not np.isnan(t_inj) else -1)
        iso = ""
        k = first_idx(g, s["gos_all"], thr["gos_all"], t_inj, r["t_end"], persist=PERSIST) if not np.isnan(t_inj) else -1
        if k >= 0:
            m = (g >= g[k]) & (g <= g[k] + 2.0)
            cand = {sn: np.nanmean(s[f"gos_{sn}"][m]) for sn in SENSORS if not np.all(np.isnan(s[f"gos_{sn}"][m]))}
            if cand: iso = min(cand, key=cand.get)
        t_ours = float(s["t_ours"])
        fp["ours"] = (not np.isnan(t_ours)) and (t_ours < r["fp1"])
        if not np.isnan(t_ours) and not np.isnan(t_inj) and t_ours >= t_inj:
            det["ours"] = t_ours - t_inj; detw["ours"] = np.interp(t_ours, g, gw) - r["t_inj_wall"]
        else: det["ours"] = detw["ours"] = np.nan
        nerr = s["nerr"]; mrmv = s["mrm"]
        base_pre = np.nanmedian(nerr[(g >= r["fp0"]) & (g < r["fp0"] + 5)]) if ((g >= r["fp0"]) & (g < r["fp0"] + 5)).any() else np.nan
        fp["b0_diag"] = (first_idx(g, nerr, base_pre, r["fp0"] + 5, r["fp1"], persist=10) >= 0) if not np.isnan(base_pre) else False
        fp["b0_mrm"] = first_idx(g, mrmv, 1.5, r["fp0"], r["fp1"], persist=1) >= 0
        if not np.isnan(t_inj):
            base = np.nanmedian(nerr[(g >= t_inj - 5) & (g < t_inj)]) if ((g >= t_inj - 5) & (g < t_inj)).any() else np.nan
            put("b0_diag", first_idx(g, nerr, base, t_inj, r["t_end"], persist=10) if not np.isnan(base) else -1)
            put("b0_mrm", first_idx(g, mrmv, 1.5, t_inj, r["t_end"], persist=1))
        else: det["b0_diag"] = det["b0_mrm"] = detw["b0_diag"] = detw["b0_mrm"] = np.nan
        st = b0_loc_times(r["tag"], None)
        b0loc_avail = st is not None
        if st is None: det["b0_loc"] = detw["b0_loc"] = np.nan; fp["b0_loc"] = False
        else:
            post = [x for x in st if not np.isnan(t_inj) and x >= t_inj]; pre = [x for x in st if r["fp0"] <= x < r["fp1"]]
            det["b0_loc"] = (post[0] - t_inj) if post else np.nan; detw["b0_loc"] = (np.interp(post[0], g, gw) - r["t_inj_wall"]) if post else np.nan; fp["b0_loc"] = bool(pre)
        csvrows.append(dict(tag=r["tag"], fault=r["fault"], sev=r["sev"], npc=r["npc"], rep=r["rep"], post_s=round(r["t_end"] - t_inj, 1) if not np.isnan(t_inj) else "",
                            sim_rate=round(float(s["sim_rate"]), 2), yu_eq=(f"{float(s['yu_eq']):.1e}" if not np.isnan(float(s["yu_eq"])) else ""),
                            **{f"det_{k}": (round(v, 2) if not np.isnan(v) else "") for k, v in det.items()},
                            **{f"detw_{k}": (round(v, 2) if not np.isnan(v) else "") for k, v in detw.items()},
                            **{f"fp_{k}": int(v) for k, v in fp.items()}, gos_iso=iso, b0loc_avail=int(b0loc_avail)))
    with open(os.path.join(RES, "baseline_fdi", "cases.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(csvrows[0].keys())); w.writeheader(); w.writerows(csvrows)
    DET = [("b0_loc", "B0 측위진단"), ("b0_mrm", "B0 MRM"), ("yu", "YU 상태χ²"), ("gos_all", "GOS 잔차"), ("ours", "제안(재생)")]
    eqs = [float(r["s"]["yu_eq"]) for r in rows if not np.isnan(float(r["s"]["yu_eq"]))]
    L = [f"# 베이스라인 FDI 비교 (순정 bag 오프라인, {len(csvrows)}건; 시각은 시뮬 시간, 벽시계 환산은 cases.csv detw_*)\n",
         f"- 문턱: nf 짝수 rep {len(nf_cal)}런(보정용) FP 창 최대값 → YU {thr['yu']:.2f} (교과서 {thr_text['yu']}), GOS {thr['gos_all']:.2f} (교과서 {thr_text['gos_all']}). 오탐 평가는 nf 홀수 rep {len(nf_tst)}런 + 고장 런 주입 전 창(별도 데이터).",
         f"- YU 상태영역 통계량 vs 혁신 χ² 상대차 최대 {max(eqs) if eqs else float('nan'):.1e} (수치 동치 확인)",
         "- 검출률 = 주입 후 종료까지 경보 / 케이스 [Wilson 95% CI]. 지연 = 중앙값 [s]. 모든 검출기 경보 확정 = 1 s 지속. McNemar p: 제안 vs 해당 검출기(대응 표본, 정확검정).",
         "- B0 측위진단 = /autoware/localization/* 유닛 중 ERROR/STALE 1 s 지속(새로 발생). 참고: 진단그래프 '전체 ERROR 노드 수 증가'는 nf 전부에서 울려 검출기로 쓸 수 없음(cases.csv det_b0_diag).\n",
         "| 고장 | 세기 | n | " + " | ".join(f"{nm}" for _, nm in DET) + " | GOS 격리 |", "|---|---|---|" + "---|" * (len(DET) + 1)]
    groups = collections.OrderedDict()
    for c in csvrows: groups.setdefault((c["fault"], c["sev"]), []).append(c)
    for (f_, s_), cs in groups.items():
        if f_ == "nf": continue
        cells = []
        for k, _ in DET:
            pool = [c for c in cs if c["b0loc_avail"]] if k == "b0_loc" else cs
            if not pool: cells.append("n/a"); continue
            d = [c[f"det_{k}"] for c in pool if c[f"det_{k}"] != ""]; lo, hi = wilson(len(d), len(pool))
            txt = f"{len(d)}/{len(pool)} [{lo:.2f}–{hi:.2f}]" + (f" · {np.median(d):.1f} s" if d else "")
            if k != "ours":
                b = sum(1 for c in pool if c["det_ours"] != "" and c[f"det_{k}"] == ""); cc = sum(1 for c in pool if c["det_ours"] == "" and c[f"det_{k}"] != "")
                p = mcnemar_p(b, cc); txt += (" · p<0.001" if p < 0.001 else f" · p={p:.3f}") if not np.isnan(p) else " · p=–"
            cells.append(txt)
        iso = collections.Counter(c["gos_iso"] for c in cs if c["gos_iso"])
        L.append(f"| {f_} | {s_} | {len(cs)} | " + " | ".join(cells) + " | " + ", ".join(f"{k}:{v}" for k, v in iso.most_common()) + " |")
    L.append("\n## 오탐 (경보 런 수 / 창 수)\n")
    L.append("| 구간 | " + " | ".join(nm for _, nm in DET) + " |"); L.append("|---|" + "---|" * len(DET))
    nfc_cal = [c for c in csvrows if c["fault"] == "nf" and int(c["rep"]) % 2 == 0]; nfc_tst = [c for c in csvrows if c["fault"] == "nf" and int(c["rep"]) % 2 == 1]
    prec = [c for c in csvrows if c["fault"] != "nf"]
    for nm, cs in (("nf 보정용(짝수 rep)", nfc_cal), ("nf 평가용(홀수 rep)", nfc_tst), ("고장 런 주입 전 창", prec)):
        L.append(f"| {nm} (n={len(cs)}) | " + " | ".join(f"{sum(c[f'fp_{k}'] for c in cs)}" for k, _ in DET) + " |")
    L.append("\n## 교과서 문턱(보정 없음) 기준 YU/GOS\n")
    L.append("| 고장 | 세기 | YU 검출률 · 지연 | GOS 검출률 · 지연 |"); L.append("|---|---|---|---|")
    for (f_, s_), cs in groups.items():
        if f_ == "nf": continue
        cells = []
        for k in ("yu_tb", "gos_all_tb"):
            d = [c[f"det_{k}"] for c in cs if c[f"det_{k}"] != ""]; cells.append(f"{len(d)}/{len(cs)}" + (f" · {np.median(d):.1f} s" if d else ""))
        L.append(f"| {f_} | {s_} | " + " | ".join(cells) + " |")
    L.append(f"| nf 오탐(전체 {len(nfc_cal) + len(nfc_tst)}) | | {sum(c['fp_yu_tb'] for c in nfc_cal + nfc_tst)} | {sum(c['fp_gos_all_tb'] for c in nfc_cal + nfc_tst)} |")
    txt = "\n".join(L); open(os.path.join(RES, "baseline_fdi", "report.md"), "w").write(txt + "\n"); print(txt)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stats", action="store_true"); ap.add_argument("--report", action="store_true")
    ap.add_argument("--workers", type=int, default=3); ap.add_argument("--only", default=""); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(); os.makedirs(STATS, exist_ok=True)
    if a.stats:
        tags = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(CACHE, "*.npz")) if a.only in f)
        if a.limit: tags = tags[:a.limit]
        from multiprocessing import Pool
        with Pool(a.workers) as p:
            for n, (tag, msg) in enumerate(p.imap_unordered(case_stats, tags), 1):
                if msg != "cached": print(f"[{n}/{len(tags)}] {tag}: {msg}", flush=True)
    if a.report: report()
