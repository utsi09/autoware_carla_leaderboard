#!/usr/bin/env python3
"""[2026-11-08] A안: 순정(stock, --mrm-off) bag 에서 베이스라인 FDI 평가에 필요한 신호만 뽑아 npz 캐시로 저장.
입력: results/stock_outcomes.csv 의 유효 케이스(tag → results/bags/<tag>), 고장 imn/imb/imd/gn/gb/gm + nf(+lf/cf, B0용)
출력: results/baseline_fdi/cache/<tag>.npz   (시각은 bag 수신 wall time [s], 각 배열 첫 열)
사용: baseline_fdi_extract.py [--workers 2] [--only SUBSTR] [--limit N]
"""
import os, sys, csv, math, argparse, time
import numpy as np
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CACHE = os.path.join(RES, "baseline_fdi", "cache")
FAULTS = ("imn", "imb", "imd", "gn", "gb", "gm", "nf", "lf", "cf")
SKIP = ("CARLA_DIED", "SETUP_FAIL", "INTERRUPTED", "DISK_FULL")

def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

def extract(tag):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    bag = os.path.join(RES, "bags", tag)
    out = os.path.join(CACHE, tag + ".npz")
    if os.path.exists(out): return tag, "cached"
    for attempt in range(3):
        try:
            r = rosbag2_py.SequentialReader()
            r.open(rosbag2_py.StorageOptions(uri=bag, storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
            types = {t.name: t.type for t in r.get_all_topics_and_types()}
            cls = {}
            A = {k: [] for k in ("imu", "vel", "steer", "gnss", "ndt", "ks", "score", "mrm", "diag", "inj", "tp", "nvtl")}
            T = {"/sensing/imu/imu_data": "imu", "/vehicle/status/velocity_status": "vel", "/vehicle/status/steering_status": "steer",
                 "/sensing/gnss/pose_with_covariance": "gnss", "/localization/pose_estimator/pose_with_covariance": "ndt",
                 "/localization/kinematic_state": "ks", "/monitor/scores": "score", "/system/fail_safe/mrm_state": "mrm",
                 "/diagnostics_graph/status": "diag", "/fault_injection/active": "inj",
                 "/localization/pose_estimator/transform_probability": "tp", "/localization/pose_estimator/nearest_voxel_transformation_likelihood": "nvtl"}
            t0 = None
            while r.has_next():
                topic, data, t = r.read_next()
                if t0 is None: t0 = t
                k = T.get(topic)
                if k is None: continue
                if topic not in cls: cls[topic] = get_message(types[topic])
                m = deserialize_message(data, cls[topic]); ts = t * 1e-9
                if k == "imu":
                    h = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
                    A[k].append((ts, h, m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z, m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z))
                elif k == "vel": A[k].append((ts, m.longitudinal_velocity, m.lateral_velocity, m.heading_rate))
                elif k == "steer": A[k].append((ts, m.steering_tire_angle))
                elif k == "gnss": A[k].append((ts, m.pose.pose.position.x, m.pose.pose.position.y, m.pose.pose.position.z))
                elif k == "ndt":
                    p = m.pose.pose; c = m.pose.covariance
                    A[k].append((ts, p.position.x, p.position.y, yaw_of(p.orientation), c[0], c[7], c[35]))
                elif k == "ks":
                    p = m.pose.pose; c = m.pose.covariance; tw = m.twist.twist
                    A[k].append((ts, p.position.x, p.position.y, yaw_of(p.orientation), tw.linear.x, tw.angular.z, c[0], c[7], c[35]))
                elif k == "score":
                    d = {s.name: float(s.message) if s.message not in ("", "nan") else float("nan") for s in m.status}
                    A[k].append((ts, d.get("capability/localization", np.nan), d.get("sensor/LIDAR_front", np.nan), d.get("sensor/CAMERA_front", np.nan),
                                 d.get("capability/perception", np.nan), d.get("capability/obstacle", np.nan)))
                elif k == "mrm": A[k].append((ts, m.state, m.behavior))
                elif k == "diag":
                    lv = [int.from_bytes(n.level, "little") if isinstance(n.level, bytes) else int(n.level) for n in m.nodes]
                    A[k].append((ts, lv[0] if lv else -1, sum(1 for x in lv if x >= 2), len(lv)))
                elif k == "inj": A[k].append((ts, 1.0 if m.data else 0.0))
                elif k in ("tp", "nvtl"): A[k].append((ts, m.data))
            np.savez_compressed(out, t0=t0 * 1e-9, **{k: np.array(v, dtype=float) for k, v in A.items()})
            return tag, f"ok imu={len(A['imu'])} gnss={len(A['gnss'])} ndt={len(A['ndt'])} inj={len(A['inj'])}"
        except Exception as e:
            err = repr(e); time.sleep(5)      # bag 교체(압축) 순간과 겹친 경우 재시도
    return tag, "FAIL " + err

def cases(only="", limit=0):
    rows = list(csv.DictReader(open(os.path.join(RES, "stock_outcomes.csv"))))
    tags = []
    for r in rows:
        if r["fault"] not in FAULTS or r["judge"] in SKIP: continue
        if r["fault"] != "nf" and r["no_fault"]: continue
        if only and only not in r["tag"]: continue
        if os.path.isdir(os.path.join(RES, "bags", r["tag"])): tags.append(r["tag"])
    return tags[:limit] if limit else tags

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); ap.add_argument("--only", default=""); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--tags-file", default="")
    a = ap.parse_args()
    tags = [l.strip() for l in open(a.tags_file) if l.strip()] if a.tags_file else cases(a.only, a.limit); print(f"{len(tags)} cases", flush=True)
    from multiprocessing import Pool
    n = 0
    with Pool(a.workers) as p:
        for tag, msg in p.imap_unordered(extract, tags):
            n += 1
            if msg != "cached" or n % 50 == 0: print(f"[{n}/{len(tags)}] {tag}: {msg}", flush=True)
    print("done", flush=True)
