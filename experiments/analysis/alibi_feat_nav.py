#!/usr/bin/env python3
"""GNSS·IMU 특징 추출(bag → npz) — Alibi Detect Online MMD 대조군용. 순정 매트릭스 bag(def 교통) 사용.
출력 results/alibi/feat/<tag>.npz: t(sim, 20 Hz 그리드), fault_active(t), gnss_feat(t,4)=[GNSS−EKF dx, dy, |GNSS 점프|, EKF 속도], imu_feat(t,6)=gyro xyz, accel xyz(원시 20 Hz 샘플 그리드 정렬)."""
import sys, glob, os, csv, numpy as np
from pathlib import Path
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results"); OUT = RES / "alibi" / "feat"
def st(h): return h.stamp.sec + h.stamp.nanosec * 1e-9
def run(tag):
    out = OUT / f"{tag}.npz"
    if out.exists(): return "skip"
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(RES / "bags" / tag), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    need = {"/localization/kinematic_state", "/sensing/gnss/pose_with_covariance", "/sensing/imu/imu_data", "/fault_injection/active", "/clock"}
    cls = {t: get_message(types[t]) for t in need if t in types}
    kin, gnss, imu, fault, clock = [], [], [], [], []
    while reader.has_next():
        topic, data, t_ns = reader.read_next()
        if topic not in cls: continue
        m = deserialize_message(data, cls[topic]); tb = t_ns * 1e-9
        if topic == "/clock": clock.append((tb, m.clock.sec + m.clock.nanosec * 1e-9))
        elif topic == "/localization/kinematic_state": kin.append((tb, st(m.header), m.pose.pose.position.x, m.pose.pose.position.y, m.twist.twist.linear.x))
        elif topic == "/sensing/gnss/pose_with_covariance": gnss.append((tb, m.pose.pose.position.x, m.pose.pose.position.y))
        elif topic == "/sensing/imu/imu_data": imu.append((tb, m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z, m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z))
        elif topic == "/fault_injection/active": fault.append((tb, int(m.data)))
    clock = np.array(clock); kin = np.array(kin); gnss = np.array(gnss); imu = np.array(imu)
    if len(clock) < 10 or len(kin) < 10 or len(gnss) < 10 or len(imu) < 10: return "short"
    def bag2sim(tb): return np.interp(tb, clock[:, 0], clock[:, 1])
    # fault time: topic if present else live csv t_fault (sim)
    tf = None
    if fault: 
        on = [tb for tb, v in fault if v]; tf = bag2sim(on[0]) if on else None
    if tf is None:
        p = RES / "live" / f"{tag}.csv"
        if p.exists():
            try: tf = float(next(csv.DictReader(open(p)))["t_fault"])
            except Exception: tf = None
    ts = bag2sim(gnss[:, 0])  # GNSS sample times (sim)
    kx = np.interp(gnss[:, 0], kin[:, 0], kin[:, 2]); ky = np.interp(gnss[:, 0], kin[:, 0], kin[:, 3]); kv = np.interp(gnss[:, 0], kin[:, 0], kin[:, 4])
    dx = gnss[:, 1] - kx; dy = gnss[:, 2] - ky
    jump = np.r_[0.0, np.hypot(np.diff(gnss[:, 1]), np.diff(gnss[:, 2]))]
    gf = np.c_[dx, dy, jump, kv]
    im = np.c_[[np.interp(gnss[:, 0], imu[:, 0], imu[:, k]) for k in range(1, 7)]].T
    np.savez_compressed(out, t=ts, t_fault=np.nan if tf is None else tf, gnss_feat=gf.astype(np.float32), imu_feat=im.astype(np.float32),
                        imu_t=bag2sim(imu[:, 0]).astype(np.float32), imu_raw=imu[:, 1:].astype(np.float32))
    return f"ok n={len(ts)} tf={tf}"
if __name__ == "__main__":
    for tag in sys.argv[1:]:
        try: print(tag, run(tag), flush=True)
        except Exception as e: print(tag, "ERR", e, flush=True)
