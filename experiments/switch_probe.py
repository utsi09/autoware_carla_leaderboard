#!/usr/bin/env python3
"""1s마다 scenario/속도/운전모드 기록 — 전환 불발 원인 판별용."""
import rclpy, time
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from autoware_internal_planning_msgs.msg import Scenario
from nav_msgs.msg import Odometry
from autoware_adapi_v1_msgs.msg import OperationModeState

rclpy.init()
n = Node('switch_probe')
state = {'sc': '?', 'v': -1.0, 'om': '?', 'ctrl': '?'}
n.create_subscription(Scenario, '/planning/scenario_planning/scenario',
                      lambda m: state.update(sc=m.current_scenario), 1)
n.create_subscription(Odometry, '/localization/kinematic_state',
                      lambda m: state.update(v=abs(m.twist.twist.linear.x)), 1)
n.create_subscription(OperationModeState, '/api/operation_mode/state',
                      lambda m: state.update(om=m.mode, ctrl=m.is_autoware_control_enabled),
                      QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE))
last = 0.0
def tick():
    global last
    now = time.time()
    if now - last >= 1.0:
        last = now
        print(f"{now:.0f} sc={state['sc']} v={state['v']:.4f} om={state['om']} ctrl={state['ctrl']}", flush=True)
n.create_timer(0.2, tick)
rclpy.spin(n)
