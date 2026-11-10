import sys, glob, csv, numpy as np
from pathlib import Path
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
BAGS = Path("/home/taewook/autoware_carla_leaderboard/experiments/results/bags")
LIVE = Path("/home/taewook/autoware_carla_leaderboard/experiments/results/live")
OUT = Path("/home/taewook/autoware_carla_leaderboard/experiments/results/derived/series")
OUT.mkdir(exist_ok=True)
KEYS = {("capability/perception", "score"): "perc", ("LIDAR_front", "quality_score"): "qlid",
        ("capability/obstacle", "score"): "obs", ("sector/F", "score"): "secF", ("capability/localization", "score"): "loc"}
def run(tag):
    d = BAGS / tag
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(d), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    cls = get_message(types["/monitor/scores"])
    ser = {v: [] for v in KEYS.values()}
    n = 0
    while reader.has_next():
        topic, data, t_ns = reader.read_next()
        if topic != "/monitor/scores": continue
        m = deserialize_message(data, cls)
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9 if m.header.stamp.sec else t_ns * 1e-9
        n += 1
        for st in m.status:
            for kv in st.values:
                k = KEYS.get((st.name, kv.key))
                if k is None and "LIDAR_front" in st.name and kv.key == "quality_score": k = "qlid"
                if k:
                    try: ser[k].append((t, float(kv.value)))
                    except ValueError: pass
    tf = float(next(csv.DictReader(open(LIVE / f"{tag}.csv")))["t_fault"])
    names = sorted({st.name for st in m.status})
    np.savez(OUT / f"{tag}.npz", t_fault=tf, **{k: np.array(v) for k, v in ser.items()})
    print(tag, "msgs", n, "t_fault", round(tf, 1), {k: len(v) for k, v in ser.items()}, names[:12])
for tag in sys.argv[1:]:
    try: run(tag)
    except Exception as e: print(tag, "ERR", e)
