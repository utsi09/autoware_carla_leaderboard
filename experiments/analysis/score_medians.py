"""bag 의 /monitor/scores 에서 주입 후 점수 중앙값(카메라·신호등·위치·라이다·인지)을 뽑아 CSV 로. 사용: score_medians.py OUT.csv tag1 tag2 ..."""
import sys, csv, numpy as np, os
from pathlib import Path
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
BAGS = Path("/home/taewook/autoware_carla_leaderboard/experiments/results/bags"); LIVE = Path("/home/taewook/autoware_carla_leaderboard/experiments/results/live")
KEYS = {"cam": ("sensor/CAMERA_front", "quality_score"), "tl": ("capability/traffic_light", "score"), "loc": ("capability/localization", "score"),
        "lid": ("sensor/LIDAR_front", "quality_score"), "perc": ("capability/perception", "score"), "obs": ("capability/obstacle", "score")}
out = sys.argv[1]; done = set()
if os.path.exists(out):
    done = {r["tag"] for r in csv.DictReader(open(out))}
fh = open(out, "a", newline=""); w = csv.writer(fh)
if not done: w.writerow(["tag", "t_fault", "n"] + list(KEYS))
for tag in sys.argv[2:]:
    if tag in done: continue
    try:
        tf = float(next(csv.DictReader(open(LIVE / f"{tag}.csv")))["t_fault"])
        reader = rosbag2_py.SequentialReader()
        reader.open(rosbag2_py.StorageOptions(uri=str(BAGS / tag), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
        types = {t.name: t.type for t in reader.get_all_topics_and_types()}; cls = get_message(types["/monitor/scores"])
        acc = {k: [] for k in KEYS}; n = 0
        while reader.has_next():
            topic, data, t_ns = reader.read_next()
            if topic != "/monitor/scores": continue
            m = deserialize_message(data, cls); t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if t < tf: continue
            n += 1
            for st in m.status:
                for kv in st.values:
                    for k, (nm, key) in KEYS.items():
                        if (nm in st.name) and kv.key == key:
                            try: acc[k].append(float(kv.value))
                            except ValueError: pass
        w.writerow([tag, round(tf, 2), n] + [round(float(np.median(v)), 4) if v else "" for v in acc.values()]); fh.flush()
        print(tag, n, {k: (round(float(np.median(v)), 3) if v else None) for k, v in acc.items()})
    except Exception as e:
        print(tag, "ERR", e)
