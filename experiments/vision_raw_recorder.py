#!/usr/bin/env python3
"""[2026-11-08 비전 베이스라인] 전방 LiDAR 점군과 카메라 이미지를 2 Hz(시뮬 시간)로 솎아 저장.

러너의 표준 bag에는 점군·이미지가 없어(Hz 보호) Won 2023 / Zhang 2024 / Lee 2022 구조 재구현
베이스라인을 돌릴 입력이 없다. 이 노드는 러너 옆에서 따로 떠서(호스트, raw 바이트 구독 →
보존 프레임만 역직렬화) 다음을 남긴다.

  <out>/lidar_XXXX.npz : t_sim, t_wall, off(N+1), xyz_cm int16[M,3], inten uint8[M], chan uint8[M]
  <out>/cam/XXXXXX.png : BGR 무손실(노이즈 보존), <out>/cam_index.csv : idx,t_sim,t_wall
  <out>/inj.csv        : /fault_injection/active 수신 (t_wall, t_sim(최근 /clock), value)
  <out>/meta.json      : 토픽·수신 카운트·보존 카운트

사용: python3 vision_raw_recorder.py --out DIR [--hz 2.0]    (SIGTERM/SIGINT 로 종료 → 플러시)
"""
import argparse, csv, json, os, queue, signal, sys, threading, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import PointCloud2, Image
from std_msgs.msg import Bool
from rosgraph_msgs.msg import Clock

LIDAR_TOPIC = "/sensor/lidar/front"
CAM_TOPIC = "/sensing/camera/traffic_light/image_raw"
INJ_TOPIC = "/fault_injection/active"
CHUNK = 40  # LiDAR frames per npz (2 Hz → 20 s)


def stamp_s(st):
    return st.sec + st.nanosec * 1e-9


class Recorder(Node):
    def __init__(self, out, hz, cam=True):
        super().__init__("vision_raw_recorder")
        self.out = out
        os.makedirs(os.path.join(out, "cam"), exist_ok=True)
        self.period = 1.0 / hz
        self.last_l = -1e9
        self.last_c = -1e9
        self.sim_now = float("nan")
        self.n_rx = {"lidar": 0, "cam": 0, "inj": 0}
        self.n_keep = {"lidar": 0, "cam": 0}
        self.lbuf = []          # list of (t_sim, t_wall, xyz_cm, inten, chan)
        self.lchunk = 0
        self.q = queue.Queue(maxsize=64)
        self.worker = threading.Thread(target=self._writer, daemon=True)
        self.worker.start()
        self.cam_idx = open(os.path.join(out, "cam_index.csv"), "w", newline="")
        self.cam_csv = csv.writer(self.cam_idx)
        self.cam_csv.writerow(["idx", "t_sim", "t_wall"])
        self.inj_f = open(os.path.join(out, "inj.csv"), "w", newline="")
        self.inj_csv = csv.writer(self.inj_f)
        self.inj_csv.writerow(["t_wall", "t_sim", "value"])
        self.create_subscription(PointCloud2, LIDAR_TOPIC, self.cb_lidar, qos_profile_sensor_data, raw=True)
        if cam:   # [2026-11-09] --no-cam: 라이다만(사다리 교차검증용)
            self.create_subscription(Image, CAM_TOPIC, self.cb_cam, qos_profile_sensor_data, raw=True)
        self.create_subscription(Clock, "/clock", self.cb_clock, qos_profile_sensor_data)
        inj_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST)
        self.create_subscription(Bool, INJ_TOPIC, self.cb_inj, inj_qos)

    # ---- callbacks -------------------------------------------------------
    def cb_clock(self, m):
        self.sim_now = stamp_s(m.clock)

    def cb_inj(self, m):
        self.n_rx["inj"] += 1
        self.inj_csv.writerow([f"{time.time():.3f}", f"{self.sim_now:.3f}", int(m.data)])
        self.inj_f.flush()

    def cb_lidar(self, raw):
        self.n_rx["lidar"] += 1
        # 헤더 시각만 먼저 본다: PointCloud2 CDR = 4B 캡슐 헤더 + sec(int32) + nanosec(uint32)
        sec = int.from_bytes(raw[4:8], "little", signed=True)
        nsec = int.from_bytes(raw[8:12], "little")
        t = sec + nsec * 1e-9
        if t - self.last_l < self.period - 0.02:
            return
        self.last_l = t
        m = deserialize_message(raw, PointCloud2)
        if m.point_step != 16 or m.width * m.height == 0:
            return
        a = np.frombuffer(bytes(m.data), dtype=np.uint8).reshape(-1, 16)
        xyz = a[:, 0:12].copy().view(np.float32).reshape(-1, 3)
        xyz_cm = np.clip(np.round(xyz * 100.0), -32000, 32000).astype(np.int16)
        inten = a[:, 12].copy()
        chan = np.clip(a[:, 14:16].copy().view(np.uint16).reshape(-1), 0, 255).astype(np.uint8)
        self.lbuf.append((t, time.time(), xyz_cm, inten, chan))
        self.n_keep["lidar"] += 1
        if len(self.lbuf) >= CHUNK:
            self._flush_lidar()

    def cb_cam(self, raw):
        self.n_rx["cam"] += 1
        sec = int.from_bytes(raw[4:8], "little", signed=True)
        nsec = int.from_bytes(raw[8:12], "little")
        t = sec + nsec * 1e-9
        if t - self.last_c < self.period - 0.02:
            return
        self.last_c = t
        m = deserialize_message(raw, Image)
        if m.encoding not in ("bgra8", "bgr8", "rgb8", "rgba8"):
            return
        ch = 4 if m.encoding.endswith("a8") else 3
        img = np.frombuffer(bytes(m.data), dtype=np.uint8).reshape(m.height, m.width, ch)
        if m.encoding.startswith("rgb"):
            img = img[:, :, [2, 1, 0] + ([3] if ch == 4 else [])]
        bgr = np.ascontiguousarray(img[:, :, :3])
        idx = self.n_keep["cam"]
        self.n_keep["cam"] += 1
        self.cam_csv.writerow([idx, f"{t:.4f}", f"{time.time():.3f}"])
        self.cam_idx.flush()
        try:
            self.q.put_nowait(("cam", idx, bgr))
        except queue.Full:
            self.get_logger().warn("writer queue full — dropping camera frame")

    # ---- writer ------------------------------------------------------------
    def _flush_lidar(self):
        if not self.lbuf:
            return
        buf, self.lbuf = self.lbuf, []
        k = self.lchunk
        self.lchunk += 1
        try:
            self.q.put_nowait(("lidar", k, buf))
        except queue.Full:
            self.get_logger().warn("writer queue full — dropping lidar chunk")

    def _writer(self):
        import cv2
        while True:
            item = self.q.get()
            if item is None:
                return
            kind, k, payload = item
            if kind == "cam":
                cv2.imwrite(os.path.join(self.out, "cam", f"{k:06d}.png"), payload,
                            [cv2.IMWRITE_PNG_COMPRESSION, 1])
            else:
                t_sim = np.array([b[0] for b in payload])
                t_wall = np.array([b[1] for b in payload])
                off = np.cumsum([0] + [len(b[2]) for b in payload]).astype(np.int64)
                np.savez_compressed(os.path.join(self.out, f"lidar_{k:04d}.npz"),
                                    t_sim=t_sim, t_wall=t_wall, off=off,
                                    xyz_cm=np.concatenate([b[2] for b in payload]),
                                    inten=np.concatenate([b[3] for b in payload]),
                                    chan=np.concatenate([b[4] for b in payload]))

    def close(self):
        self._flush_lidar()
        self.q.put(None)
        self.worker.join(timeout=120)
        self.cam_idx.close()
        self.inj_f.close()
        with open(os.path.join(self.out, "meta.json"), "w") as f:
            json.dump({"lidar_topic": LIDAR_TOPIC, "cam_topic": CAM_TOPIC, "period_s": self.period,
                       "n_rx": self.n_rx, "n_keep": self.n_keep, "lidar_chunks": self.lchunk,
                       "t_end_wall": time.time()}, f, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--hz", type=float, default=2.0)
    ap.add_argument("--no-cam", action="store_true", help="카메라 저장 생략(라이다만)")
    args = ap.parse_args()
    rclpy.init()
    node = Recorder(args.out, args.hz, cam=not args.no_cam)
    stop = {"flag": False}

    def _sig(*_):
        stop["flag"] = True
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    try:
        while rclpy.ok() and not stop["flag"]:
            rclpy.spin_once(node, timeout_sec=0.2)
    finally:
        node.close()
        print(f"[vision_raw_recorder] rx={node.n_rx} keep={node.n_keep} -> {args.out}", flush=True)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
