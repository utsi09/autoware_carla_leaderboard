"""noise_capability.py 의 s_loc_med(GNSS-EKF 잔차 기반 위치추정 점수)를 bag 에서 재계산. 사용: loc_score.py OUT.csv tag..."""
import sys, csv, math, os, numpy as np
from pathlib import Path
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
BAGS = Path("/home/taewook/autoware_carla_leaderboard/experiments/results/bags"); LIVE = Path("/home/taewook/autoware_carla_leaderboard/experiments/results/live")
out = sys.argv[1]; done = {r["tag"] for r in csv.DictReader(open(out))} if os.path.exists(out) else set()
fh = open(out, "a", newline=""); w = csv.writer(fh)
if not done: w.writerow(["tag", "t_fault", "s_loc_med", "s_loc_min"])
def st(h): return h.stamp.sec + h.stamp.nanosec * 1e-9
for tag in sys.argv[2:]:
    if tag in done: continue
    try:
        tf = float(next(csv.DictReader(open(LIVE / f"{tag}.csv")))["t_fault"])
        reader = rosbag2_py.SequentialReader()
        reader.open(rosbag2_py.StorageOptions(uri=str(BAGS / tag), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
        types = {t.name: t.type for t in reader.get_all_topics_and_types()}
        need = {"/localization/kinematic_state", "/sensing/gnss/pose_with_covariance"}
        cls = {t: get_message(types[t]) for t in need if t in types}
        kin, gnss = [], []
        while reader.has_next():
            topic, data, t_ns = reader.read_next()
            if topic not in cls: continue
            m = deserialize_message(data, cls[topic])
            (kin if topic == "/localization/kinematic_state" else gnss).append((t_ns * 1e-9, st(m.header), m.pose.pose.position.x, m.pose.pose.position.y))
        kin.sort(); kb = np.array([k[0] for k in kin]); kt = np.array([k[1] for k in kin]); kx = np.array([k[2] for k in kin]); ky = np.array([k[3] for k in kin])
        rs = []   # GNSS 는 bag 수신 시각으로 kinematic_state 에 맞추고, 시각은 kin 의 헤더(시뮬)로 환산 (GNSS 헤더 시계가 다른 런 대비)
        for tb, th, gx, gy in sorted(gnss):
            i = min(np.searchsorted(kb, tb), len(kb) - 1); rs.append((kt[i], math.hypot(gx - kx[i], gy - ky[i])))
        base = np.mean([r for _, r in rs[:60]]) if len(rs) >= 60 else 0.0
        ema, s = None, []
        for t, r in rs:
            inst = math.exp(-max(0.0, r - base - 0.2) / 0.55); ema = inst if ema is None else 0.9 * ema + 0.1 * inst
            if t >= tf: s.append(ema)
        w.writerow([tag, round(tf, 2), round(float(np.median(s)), 4) if s else "", round(float(np.min(s)), 4) if s else ""]); fh.flush()
        print(tag, len(kin), len(gnss), round(float(np.median(s)), 3) if s else None)
    except Exception as e:
        print(tag, "ERR", e)
