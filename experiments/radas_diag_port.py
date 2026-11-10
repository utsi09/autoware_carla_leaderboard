#!/usr/bin/env python3
"""RADAS ROS2 (Aalto Autonomy & Mobility Lab, autonomymobilitylab/radas_ros2, firmware/src/webUI/*_diagnostics.py) 의
센서 진단 로직을 우리 토픽에 맞춰 이식한 대조군 노드 (2026-11-09).

원본 로직(그대로 유지): 1 s 주기 평가, 최근 2 s 창의 메시지 수로 Hz 계산,
  마지막 메시지 > 2 s(GNSS 5 s) → STALE,  Hz/기대Hz ≤ 0.70 → ERROR,  < 0.90 → WARN,  그 외 OK.
  (LiDAR 원본은 기대 10 Hz 에 대한 고정 문턱 7/9 Hz = 같은 비율.)
우리 환경 적응(보고서에 명시):
  - 토픽: LiDAR /sensor/lidar/front, Camera /sensing/camera/traffic_light/image_raw, IMU /sensing/imu/imu_data,
          GNSS /sensing/gnss/pose_with_covariance (수신기 상태 메시지가 없어 GNSS 는 스트림 타임아웃만 평가 가능).
  - 시계: 시뮬레이터가 실시간보다 느리므로 Hz 는 /clock(시뮬 시간) 기준으로 계산(벽시계 기준이면 정상 상태도 ERROR).
  - 기대 Hz: 고장 주입 전 처음 20 s 의 중앙값으로 자동 보정(RADAS 는 하드웨어 공칭값을 상수로 둠).
출력: CSV 한 줄/초 — wall, sim, fault_active, 각 센서 hz·level(0 OK 1 WARN 2 ERROR 3 STALE)·expected.
"""
import csv, sys, time, collections, statistics
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2, Image, Imu
from geometry_msgs.msg import PoseWithCovarianceStamped
from rosgraph_msgs.msg import Clock
from std_msgs.msg import Bool

OK, WARN, ERROR, STALE = 0, 1, 2, 3
SENSORS = {  # name: (topic, msg type, timeout s)
    "lidar":  ("/sensor/lidar/front", PointCloud2, 2.0),
    "camera": ("/sensing/camera/traffic_light/image_raw", Image, 2.0),
    "imu":    ("/sensing/imu/imu_data", Imu, 2.0),
    "gnss":   ("/sensing/gnss/pose_with_covariance", PoseWithCovarianceStamped, 5.0),
}
RATE_WINDOW, CALIB_S = 2.0, 20.0

class RadasPort(Node):
    def __init__(self, out):
        super().__init__("radas_diag_port")
        self.sim = None; self.fault = False; self.t_fault_sim = None
        self.times = {k: collections.deque() for k in SENSORS}
        self.last = {k: None for k in SENSORS}
        self.calib = {k: [] for k in SENSORS}; self.expected = {k: None for k in SENSORS}
        self.first_sim = None
        for k, (topic, T, _) in SENSORS.items():
            self.create_subscription(T, topic, lambda m, k=k: self.cb(k), qos_profile_sensor_data, raw=True)
        self.create_subscription(Clock, "/clock", self.cb_clock, qos_profile_sensor_data)
        self.create_subscription(Bool, "/fault_injection/active", self.cb_fault, 10)
        self.fh = open(out, "w", newline=""); self.w = csv.writer(self.fh)
        self.w.writerow(["wall", "sim", "fault_active", "t_since_fault"] + [f"{k}_{f}" for k in SENSORS for f in ("hz", "level", "expected")])
        self.create_timer(1.0, self.tick)
        self.get_logger().info(f"RADAS port logging to {out}")
    def cb_clock(self, m):
        self.sim = m.clock.sec + m.clock.nanosec * 1e-9
        if self.first_sim is None: self.first_sim = self.sim
    def cb_fault(self, m):
        if m.data and not self.fault: self.t_fault_sim = self.sim
        self.fault = bool(m.data)
    def cb(self, k):
        if self.sim is None: return
        self.last[k] = self.sim; self.times[k].append(self.sim)
        cut = self.sim - RATE_WINDOW
        while self.times[k] and self.times[k][0] < cut: self.times[k].popleft()
    def hz(self, k):
        t = self.times[k]
        if len(t) < 2: return 0.0
        el = t[-1] - t[0]
        return (len(t) - 1) / el if el > 0 else 0.0
    def tick(self):
        if self.sim is None: return
        row = [f"{time.time():.3f}", f"{self.sim:.3f}", int(self.fault), "" if self.t_fault_sim is None else f"{self.sim - self.t_fault_sim:.1f}"]
        for k, (_, _, timeout) in SENSORS.items():
            h = self.hz(k); last = self.last[k]
            if not self.fault and last is not None and self.expected[k] is None and h > 0:
                self.calib[k].append(h)
                if self.sim - self.first_sim >= CALIB_S and len(self.calib[k]) >= 5: self.expected[k] = statistics.median(self.calib[k])
            exp = self.expected[k] if self.expected[k] is not None else (statistics.median(self.calib[k]) if self.calib[k] else None)
            if last is None or self.sim - last > timeout: lvl = STALE
            elif exp is None or exp <= 0: lvl = OK
            else:
                r = h / exp
                lvl = ERROR if r <= 0.70 else WARN if r < 0.90 else OK
            row += [f"{h:.2f}", lvl, "" if exp is None else f"{exp:.2f}"]
        self.w.writerow(row); self.fh.flush()

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/radas_port.csv"
    rclpy.init(); n = RadasPort(out)
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    finally:
        n.fh.close(); n.destroy_node(); rclpy.shutdown()

if __name__ == "__main__": main()
