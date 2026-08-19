import time, rclpy
from rclpy.node import Node
from autoware_adapi_v1_msgs.msg import RouteState
S={0:"UNKNOWN",1:"UNSET",2:"SET",3:"ARRIVED",4:"CHANGING",5:"ABORTED"}
class W(Node):
    def __init__(s):
        super().__init__("watch_route"); s.last=None; s.t=None
        s.create_subscription(RouteState,"/api/routing/route_state",s.cb,1)
        s.create_timer(1.0,s.done); s.get_logger().info("watching /api/routing/route_state ...")
    def cb(s,m):
        s.t=time.time()
        st=S.get(m.state,m.state)
        if st!=s.last: print("ROUTE STATE ->",st,flush=True); s.last=st
    def done(s):
        if s.t and time.time()-s.t>8: raise SystemExit
rclpy.init(); 
try: rclpy.spin(W())
except SystemExit: pass
