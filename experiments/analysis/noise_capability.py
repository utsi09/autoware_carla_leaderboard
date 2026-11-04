#!/usr/bin/env python3
"""noise-capability 스윕 분석기 (계획: fs_failsafe/docs/followup_noise_capability_plan.md 4-4, 5절).

실행 하나 = (GT csv, rosbag) -> 실행당 한 줄의 요약 지표.

  bash -lc 'source /opt/ros/humble/setup.bash && source ~/autoware_awcl/autoware/install/setup.bash && \
            python3 experiments/analysis/noise_capability.py --all'          # results/gt/*.csv 전부
  ... noise_capability.py --tag lso-0.2_90-def-r0-1104_1800                   # 하나만
  ... noise_capability.py --all --out results/noise_capability_runs.csv

인지 (고장 뒤, 전방 ±SECTOR°):
  R_h    : GT 차량이 0~H m 에 있는 (프레임,차량) 중 검출 객체 중심이 MATCH m 안에 있는 비율
  R_far  : H~FAR m 구간 같은 정의
  D_det  : 차량마다 "3프레임 연속 매칭"이 처음 성립한 거리; 멀리서(> FAR) 접근한 차량만, 중앙값
  FP_s   : 전방 FAR m 안 검출 중 GT(차량·보행자) 4 m 안에 없는 것 / 초
  S_lidar, S_perc : /monitor/scores 의 LIDAR_front quality_score, perception 점수 중앙값
측위 (고장 뒤):
  e_lat_p95, ate_rmse, e_yaw_p95 : EKF(kinematic_state) - GT, 고장 전 구간 평균 오프셋 제거
  nvtl_med, ndt_hz               : NDT 신뢰도 중앙값, NDT pose 발행률
  s_loc_med                      : supervisor loc_meas 식 재계산 (GNSS-EKF 잔차)
"""
import argparse
import csv
import glob
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path("/home/taewook/autoware_carla_leaderboard")
RES = REPO / "experiments" / "results"

H_M = 26.0       # 판단 창 (Autoware 충돌검사 5 s × 4.17 m/s + 정지여유 5 m)
FAR_M = 50.0
SECTOR_DEG = 45.0
MATCH_M = 2.0    # nuScenes TP 매칭 임계
MATCH_SENS_M = 4.0
FP_M = 4.0
DDET_WINDOW_M = 80.0      # D_det 는 GT 최대 기록 거리(80 m)까지 본다
DDET_MIN_START_M = 60.0   # 이보다 멀리서 섹터에 들어온 차량만 D_det 산출 (접근 궤적 보장)
VEH_LABELS = {1, 2, 3, 4, 5}   # autoware ObjectClassification CAR..MOTORCYCLE
PED_LABEL = 7

DET_TOPIC = "/perception/object_recognition/detection/objects"
DET_FALLBACK = "/perception/object_recognition/detection/centerpoint/objects"
TRK_TOPIC = "/perception/object_recognition/objects"


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def stamp_s(h):
    return h.stamp.sec + h.stamp.nanosec * 1e-9


# ----------------------------------------------------------------- bag reading
def read_bag(bag_dir):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    mcaps = sorted(glob.glob(str(Path(bag_dir) / "*.mcap")))
    if not mcaps:
        raise FileNotFoundError(f"no mcap in {bag_dir}")
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(bag_dir), storage_id="mcap"),
                rosbag2_py.ConverterOptions("", ""))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    # 분석에 쓰는 토픽만 역직렬화 (진단 그래프·제어 명령 등은 타입 불일치로 실패할 수 있음)
    NEED = (DET_TOPIC, DET_FALLBACK, TRK_TOPIC, "/localization/kinematic_state",
            "/localization/pose_estimator/pose_with_covariance",
            "/localization/pose_estimator/nearest_voxel_transformation_likelihood",
            "/sensing/gnss/pose_with_covariance", "/monitor/scores", "/fault_injection/active")
    out = defaultdict(list)
    cls = {}
    bad = set()
    while reader.has_next():
        topic, data, t_ns = reader.read_next()
        if topic not in NEED or topic in bad:
            continue
        if topic not in cls:
            try:
                cls[topic] = get_message(types[topic])
            except Exception:
                cls[topic] = None
        if cls[topic] is None:
            continue
        try:
            out[topic].append((t_ns * 1e-9, deserialize_message(data, cls[topic])))
        except Exception:
            bad.add(topic)
    return out


def objects_frames(msgs):
    """[(stamp, [(x, y, cls)])], frame_id  (detection = base_link, tracking/prediction = map)"""
    frames = []
    frame_id = msgs[0][1].header.frame_id if msgs else "map"
    for _, m in msgs:
        t = stamp_s(m.header)
        objs = []
        for o in m.objects:
            k = o.kinematics
            pwc = getattr(k, "pose_with_covariance", None) or getattr(k, "initial_pose_with_covariance", None)
            p = pwc.pose.position
            label = o.classification[0].label if o.classification else -1
            objs.append((p.x, p.y, label))
        frames.append((t, objs))
    return frames, frame_id


def scores_series(msgs):
    """/monitor/scores DiagnosticArray -> {(status_name, key): [(t, value)]}"""
    ser = defaultdict(list)
    names = set()
    for t_bag, m in msgs:
        t = stamp_s(m.header) if m.header.stamp.sec else t_bag
        for st in m.status:
            names.add(st.name)
            for kv in st.values:
                try:
                    ser[(st.name, kv.key)].append((t, float(kv.value)))
                except ValueError:
                    pass
            # level 도 기록
            ser[(st.name, "level")].append((t, float(st.level[0] if isinstance(st.level, bytes) else st.level)))
    return ser, names


# ----------------------------------------------------------------- GT reading
def read_gt(path):
    ego = {}        # aw_sec -> dict
    actors = defaultdict(list)   # aw_sec -> [dict]
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            t = round(float(r["aw_sec"]), 3)
            if t < 0:
                continue
            d = {k: (float(v) if k not in ("kind", "id", "tl") else v) for k, v in r.items()}
            d["id"] = int(d["id"])
            if r["kind"] == "ego":
                ego[t] = d
            else:
                actors[t].append(d)
    ts = np.array(sorted(ego.keys()))
    return ego, actors, ts


def nearest_tick(ts, t, tol=0.08):
    i = np.searchsorted(ts, t)
    cands = [j for j in (i - 1, i) if 0 <= j < len(ts)]
    if not cands:
        return None
    j = min(cands, key=lambda k: abs(ts[k] - t))
    return ts[j] if abs(ts[j] - t) <= tol else None


# ----------------------------------------------------------------- perception
def perception_metrics(frames, ego, actors, ts, t_fault, match_m, frame_id="map", lon_off=-1.4):
    tp = {"h": 0, "far": 0}
    fn = {"h": 0, "far": 0}
    fp = 0
    fp_all = 0
    n_frames = 0
    per_vehicle = defaultdict(list)   # id -> [(t, dist, matched)]
    for t, objs in frames:
        if t < t_fault:
            continue
        tk = nearest_tick(ts, t)
        if tk is None:
            continue
        e = ego[tk]
        n_frames += 1
        ex, ey, eyaw = e["x"], e["y"], math.radians(e["yaw_deg"])
        if frame_id != "map":
            # detections are in base_link: GT base_link = GT center shifted lon_off along heading
            bx, by = ex + lon_off * math.cos(eyaw), ey + lon_off * math.sin(eyaw)
            c, s_ = math.cos(eyaw), math.sin(eyaw)
            objs = [(bx + c * x - s_ * y, by + s_ * x + c * y, lab) for (x, y, lab) in objs]
        gts = []   # (id, x, y, dist, kind)
        for a in actors.get(tk, []):
            if abs(a["bearing_deg"]) > SECTOR_DEG or a["dist"] > DDET_WINDOW_M:
                continue
            gts.append((a["id"], a["x"], a["y"], a["dist"], a["kind"]))
        # detections in the front sector within FAR
        dets = []
        for (x, y, lab) in objs:
            dx, dy = x - ex, y - ey
            dist = math.hypot(dx, dy)
            if dist > DDET_WINDOW_M:
                continue
            b = math.degrees(math.atan2(dy, dx) - eyaw)
            b = (b + 180.0) % 360.0 - 180.0
            if abs(b) > SECTOR_DEG:
                continue
            dets.append((x, y, dist, lab))
        used = set()
        # greedy: GT vehicles by distance ascending
        for (aid, ax, ay, dist, kind) in sorted(gts, key=lambda g: g[3]):
            best, bestd = None, match_m
            for k, (x, y, _, _) in enumerate(dets):
                if k in used:
                    continue
                d = math.hypot(x - ax, y - ay)
                if d < bestd:
                    best, bestd = k, d
            matched = best is not None
            if matched:
                used.add(best)
            if kind == "veh":
                if dist <= FAR_M:
                    bin_ = "h" if dist <= H_M else "far"
                    (tp if matched else fn)[bin_] += 1
                per_vehicle[aid].append((t, dist, matched))
        # false positives: remaining detections with no GT (veh or walker) within FP_M
        for k, (x, y, dist, lab) in enumerate(dets):
            if k in used or dist > FAR_M:
                continue
            if all(math.hypot(x - ax, y - ay) > FP_M for (_, ax, ay, _, _) in gts):
                fp_all += 1
                if lab in VEH_LABELS or lab == PED_LABEL:
                    fp += 1
    out = {}
    for b in ("h", "far"):
        n = tp[b] + fn[b]
        out[f"R_{b}"] = tp[b] / n if n else float("nan")
        out[f"n_{b}"] = n
    dur = (frames[-1][0] - max(t_fault, frames[0][0])) if frames else 0.0
    out["FP_s"] = fp / dur if dur > 0 else float("nan")          # 차량·보행자 클래스만
    out["FP_all_s"] = fp_all / dur if dur > 0 else float("nan")  # unknown 포함
    out["n_frames"] = n_frames
    # D_det
    dd = []
    for aid, seq in per_vehicle.items():
        seq.sort()
        if not seq or seq[0][1] < DDET_MIN_START_M:
            continue           # did not approach from far
        for i in range(len(seq) - 2):
            if seq[i][2] and seq[i + 1][2] and seq[i + 2][2]:
                dd.append(seq[i][1])
                break
        else:
            dd.append(0.0)     # never detected while approaching
    out["D_det"] = float(np.median(dd)) if dd else float("nan")
    out["n_ddet"] = len(dd)
    return out


# ----------------------------------------------------------------- localization
def localization_metrics(bag, ego, ts, t_fault):
    out = {}
    kin = bag.get("/localization/kinematic_state", [])
    rows = []
    for _, m in kin:
        t = stamp_s(m.header)
        tk = nearest_tick(ts, t, tol=0.06)
        if tk is None:
            continue
        e = ego[tk]
        p = m.pose.pose.position
        yaw = yaw_of(m.pose.pose.orientation)
        rows.append((t, p.x - e["x"], p.y - e["y"], yaw - math.radians(e["yaw_deg"]),
                     math.radians(e["yaw_deg"])))
    if rows:
        arr = np.array(rows)
        pre = arr[arr[:, 0] < t_fault]
        if len(pre) < 20:            # nf 처럼 고장이 없으면 처음 10 s 를 기준으로
            pre = arr[arr[:, 0] < arr[0, 0] + 10.0]
        # EKF(base_link) - GT(center) 를 차량 좌표로: 종방향 오프셋 = base_link 가 중심에서 뒤로 얼마
        yaw_pre = pre[:, 4]
        lon = np.cos(yaw_pre) * pre[:, 1] + np.sin(yaw_pre) * pre[:, 2]
        lat = -np.sin(yaw_pre) * pre[:, 1] + np.cos(yaw_pre) * pre[:, 2]
        out["lon_off"] = float(np.median(lon)) if len(pre) else -1.4
        out["lat_off"] = float(np.median(lat)) if len(pre) else 0.0
        # 위치 오프셋을 각 샘플의 heading 으로 되돌려 빼기 위해 차량좌표 오프셋을 쓴다
        off = None
        post = arr[arr[:, 0] >= t_fault]
        if len(post):
            yaw = post[:, 4]
            ex = post[:, 1] - (np.cos(yaw) * out["lon_off"] - np.sin(yaw) * out["lat_off"])
            ey = post[:, 2] - (np.sin(yaw) * out["lon_off"] + np.cos(yaw) * out["lat_off"])
            e_lat = -np.sin(yaw) * ex + np.cos(yaw) * ey
            e_yaw = (post[:, 3] + np.pi) % (2 * np.pi) - np.pi
            e_yaw -= np.median(((pre[:, 3] + np.pi) % (2 * np.pi) - np.pi)) if len(pre) > 20 else 0.0
            out["e_lat_p95"] = float(np.percentile(np.abs(e_lat), 95))
            out["e_lat_max"] = float(np.abs(e_lat).max())
            out["ate_rmse"] = float(np.sqrt(np.mean(ex ** 2 + ey ** 2)))
            out["e_pos_p95"] = float(np.percentile(np.hypot(ex, ey), 95))
            out["e_yaw_p95_deg"] = float(np.degrees(np.percentile(np.abs(e_yaw), 95)))
            out["offset_pre_m"] = float(math.hypot(out["lon_off"], out["lat_off"]))
        out["n_ekf"] = len(post)
    # NDT
    ndt = bag.get("/localization/pose_estimator/pose_with_covariance", [])
    post_ndt = [stamp_s(m.header) for _, m in ndt if stamp_s(m.header) >= t_fault]
    if post_ndt:
        out["ndt_hz"] = len(post_ndt) / max(post_ndt[-1] - post_ndt[0], 1e-6)
    nv = [(t, m.data) for t, m in bag.get(
        "/localization/pose_estimator/nearest_voxel_transformation_likelihood", [])]
    # Float32Stamped? -> try .data else .data
    vals = []
    for t, m in bag.get("/localization/pose_estimator/nearest_voxel_transformation_likelihood", []):
        v = getattr(m, "data", None)
        if v is None:
            continue
        tt = stamp_s(m) if hasattr(m, "stamp") else t
        if tt >= t_fault:
            vals.append(float(v))
    if vals:
        out["nvtl_med"] = float(np.median(vals))
        out["nvtl_p05"] = float(np.percentile(vals, 5))
    # loc_meas recompute (supervisor.py:472-493): r = |GNSS-EKF| - base(60 samples), inst=exp(-max(0,r-0.2)/0.55), EMA 0.9
    gnss = bag.get("/sensing/gnss/pose_with_covariance", [])
    if gnss and kin:
        kt = np.array([stamp_s(m.header) for _, m in kin])
        kx = np.array([m.pose.pose.position.x for _, m in kin])
        ky = np.array([m.pose.pose.position.y for _, m in kin])
        r_series = []
        for _, g in gnss:
            t = stamp_s(g.header)
            i = np.searchsorted(kt, t)
            if i >= len(kt):
                i = len(kt) - 1
            r = math.hypot(g.pose.pose.position.x - kx[i], g.pose.pose.position.y - ky[i])
            r_series.append((t, r))
        base = np.mean([r for _, r in r_series[:60]]) if len(r_series) >= 60 else 0.0
        ema, s_loc = None, []
        for t, r in r_series:
            inst = math.exp(-max(0.0, r - base - 0.2) / 0.55)
            ema = inst if ema is None else 0.9 * ema + 0.1 * inst
            if t >= t_fault:
                s_loc.append(ema)
        if s_loc:
            out["s_loc_med"] = float(np.median(s_loc))
            out["s_loc_min"] = float(np.min(s_loc))
    return out


# ----------------------------------------------------------------- one run
def analyse(tag, gt_path, bag_dir, match_m=MATCH_M, verbose=True):
    ego, actors, ts = read_gt(gt_path)
    bag = read_bag(bag_dir)
    # fault time: first GT row with fault=1, else /fault_injection/active, else 0
    t_fault = None
    for t in ts:
        if ego[t]["fault"] >= 1:
            t_fault = float(t)
            break
    if t_fault is None:
        fa = bag.get("/fault_injection/active", [])
        t_fault = fa[0][0] if fa else float(ts[0]) if len(ts) else 0.0
        # bag time (wall) != sim time; approximate by first clock message if available
    det_topic = DET_TOPIC if bag.get(DET_TOPIC) else DET_FALLBACK
    frames, det_frame = objects_frames(bag.get(det_topic, []))
    loc = localization_metrics(bag, ego, ts, t_fault)
    lon_off = loc.get("lon_off", -1.4)
    res = {"tag": tag, "t_fault": t_fault, "det_topic": det_topic,
           "gt_ticks": len(ts), "t_end": float(ts[-1]) if len(ts) else float("nan")}
    parts = tag.split("-")
    res["fault"] = parts[0] if parts else ""
    res["sev"] = parts[1] if len(parts) > 1 else ""
    res["rep"] = next((p[1:] for p in parts if p.startswith("r") and p[1:].isdigit()), "")
    res["det_frame"] = det_frame
    if frames:
        res.update(perception_metrics(frames, ego, actors, ts, t_fault, match_m, det_frame, lon_off))
        sens = perception_metrics(frames, ego, actors, ts, t_fault, MATCH_SENS_M, det_frame, lon_off)
        res["R_h_4m"] = sens["R_h"]
        trk, trk_frame = objects_frames(bag.get(TRK_TOPIC, []))
        if trk:
            res["R_h_trk"] = perception_metrics(trk, ego, actors, ts, t_fault, match_m, trk_frame, lon_off)["R_h"]
    ser, names = scores_series(bag.get("/monitor/scores", []))
    def med(name_sub, key):
        vals = [v for (n, k), s in ser.items() if name_sub in n and k == key for (t, v) in s if t >= t_fault]
        return float(np.median(vals)) if vals else float("nan")
    res["S_lidar_front"] = med("LIDAR_front", "quality_score")
    res["S_lidar_front_total"] = med("LIDAR_front", "score")
    res["S_lidar_rear"] = med("LIDAR_rear", "quality_score")
    res["S_perc"] = med("capability/perception", "score")
    res["S_obs"] = med("capability/obstacle", "score")
    res["S_loc_cdr"] = med("capability/localization", "score")
    res["S_sector_F"] = med("sector/F", "score")
    res.update(loc)
    if verbose:
        print(f"[{tag}] fault_t={t_fault:.1f} det={det_topic.split('/')[-2]}@{det_frame} lon_off={lon_off:.2f} "
              f"frames={res.get('n_frames')} S_perc={res['S_perc']:.2f} "
              f"R_h={res.get('R_h', float('nan')):.3f} (n={res.get('n_h')}) "
              f"R_far={res.get('R_far', float('nan')):.3f} D_det={res.get('D_det', float('nan')):.1f} "
              f"FP/s={res.get('FP_s', float('nan')):.2f} S_lidar={res['S_lidar_front']:.2f} "
              f"e_lat95={res.get('e_lat_p95', float('nan')):.2f} nvtl={res.get('nvtl_med', float('nan')):.2f} "
              f"ndt_hz={res.get('ndt_hz', float('nan')):.1f} s_loc={res.get('s_loc_med', float('nan')):.2f}")
        print("   score status names:", ", ".join(sorted(names)))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default=str(RES / "noise_capability_runs.csv"))
    ap.add_argument("--match", type=float, default=MATCH_M)
    a = ap.parse_args()
    tags = [a.tag] if a.tag else sorted(p.stem for p in (RES / "gt").glob("*.csv")) if a.all else []
    if not tags:
        ap.error("--tag or --all")
    rows = []
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    for tag in tags:
        gt = RES / "gt" / f"{tag}.csv"
        bag = RES / "bags" / tag
        if not gt.exists() or not bag.exists():
            print(f"[skip] {tag}: missing gt or bag")
            continue
        try:
            rows.append(analyse(tag, gt, bag, a.match))
        except Exception as e:
            print(f"[fail] {tag}: {e}")
    if rows:
        keys = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"-> {a.out} ({len(rows)} runs)")


if __name__ == "__main__":
    main()
