#!/usr/bin/env python3
"""Record two poses over a run, to localize the bug:
  - /localization/kinematic_state          : Autoware's fused estimate (EKF output)
  - /sensing/gnss/pose_with_covariance     : the pose the agent feeds in (CARLA-derived)
Writes ego_path.csv with a 'src' column. Stops ~8s after messages stop.
"""
import csv
import time

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped


class Recorder(Node):
    def __init__(self):
        super().__init__("ego_path_recorder")
        self.rows = []
        self.t0 = None
        self.last = None
        self.create_subscription(Odometry, "/localization/kinematic_state", self.cb_kin, 10)
        self.create_subscription(PoseWithCovarianceStamped,
                                 "/sensing/gnss/pose_with_covariance", self.cb_gnss, 10)
        self.create_timer(1.0, self.check_done)
        self.get_logger().info("waiting for poses ...")

    def _t(self):
        now = time.time()
        if self.t0 is None:
            self.t0 = now
            self.get_logger().info("recording started")
        self.last = now
        return round(now - self.t0, 2)

    def cb_kin(self, msg):
        p = msg.pose.pose.position
        self.rows.append((round(time.time(),2), "kin", round(p.x, 3), round(p.y, 3)))

    def cb_gnss(self, msg):
        p = msg.pose.pose.position
        self.rows.append((round(time.time(),2), "gnss", round(p.x, 3), round(p.y, 3)))

    def check_done(self):
        # only finish once we've actually captured a run and then it stopped for a while
        if self.last and len(self.rows) > 100 and (time.time() - self.last) > 12.0:
            self.save()
            raise SystemExit(0)

    def save(self):
        with open("/home/taewook/autoware_carla_leaderboard/experiments/results/ego_path_gnmid.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t", "src", "x", "y"])
            w.writerows(self.rows)
        n_kin = sum(1 for r in self.rows if r[1] == "kin")
        n_gnss = sum(1 for r in self.rows if r[1] == "gnss")
        self.get_logger().info(f"saved ego_path.csv (kin={n_kin}, gnss={n_gnss})")


def main():
    rclpy.init()
    node = Recorder()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        if node.rows:
            node.save()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
