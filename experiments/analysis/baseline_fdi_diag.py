#!/usr/bin/env python3
"""[2026-11-08] B0용: bag 의 /diagnostics_graph/status 를 노드별 level(uint8) 시계열로 추출 → results/baseline_fdi/diag/<tag>.npz
노드 순서는 results/baseline_fdi/diag_struct.yaml (라이브 시스템 /diagnostics_graph/struct 덤프, 62노드) 의 path 순서와 같다(bag 의 nodes 길이 62 로 확인).
사용: baseline_fdi_diag.py [--workers 1] [--tags-file F]   (기본: cache/ 에 있는 모든 tag)
"""
import os, sys, glob, argparse, time
import numpy as np
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
OUT = os.path.join(RES, "baseline_fdi", "diag"); os.makedirs(OUT, exist_ok=True)

def extract(tag):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    out = os.path.join(OUT, tag + ".npz")
    if os.path.exists(out): return tag, "cached"
    bag = os.path.join(RES, "bags", tag)
    for attempt in range(3):
        try:
            r = rosbag2_py.SequentialReader(); r.open(rosbag2_py.StorageOptions(uri=bag, storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
            types = {t.name: t.type for t in r.get_all_topics_and_types()}
            if "/diagnostics_graph/status" not in types: return tag, "no diag topic"
            cls = get_message(types["/diagnostics_graph/status"]); ts, hs, lv = [], [], []
            while r.has_next():
                topic, data, t = r.read_next()
                if topic != "/diagnostics_graph/status": continue
                m = deserialize_message(data, cls)
                ts.append(t * 1e-9); hs.append(m.stamp.sec + m.stamp.nanosec * 1e-9)
                lv.append([int.from_bytes(n.level, "little") if isinstance(n.level, bytes) else int(n.level) for n in m.nodes])
            n = max(len(x) for x in lv) if lv else 0
            L = np.full((len(lv), n), 255, dtype=np.uint8)
            for i, x in enumerate(lv): L[i, :len(x)] = x
            np.savez_compressed(out, t=np.array(ts), h=np.array(hs), level=L)
            return tag, f"ok {len(ts)} msgs x {n} nodes"
        except Exception as e:
            err = repr(e); time.sleep(5)
    return tag, "FAIL " + err

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=1); ap.add_argument("--tags-file", default="")
    a = ap.parse_args()
    if a.tags_file: tags = [l.strip() for l in open(a.tags_file) if l.strip()]
    else: tags = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RES, "baseline_fdi", "cache", "*.npz")))
    from multiprocessing import Pool
    with Pool(a.workers) as p:
        for n, (tag, msg) in enumerate(p.imap_unordered(extract, tags), 1):
            if msg != "cached": print(f"[{n}/{len(tags)}] {tag}: {msg}", flush=True)
    print("done", flush=True)
