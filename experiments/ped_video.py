#!/usr/bin/env python3
"""보행자 조우 구간 영상 녹화: walker 등장 순간부터 소멸(or 45s)까지
에고 추격캠 10fps 프레임 저장. 1회 녹화 후 종료."""
import math, os, queue, time
import carla

import sys
OUT = f"/home/taewook/autoware_carla_leaderboard/experiments/results/pvid_{int(time.time())}"
os.makedirs(OUT, exist_ok=True)
client = carla.Client("localhost", 2000); client.set_timeout(8.0)

def pair(world):
    h = None
    for a in world.get_actors().filter("vehicle.*"):
        if a.attributes.get("role_name") in ("hero", "ego_vehicle"):
            h = a; break
    ws = list(world.get_actors().filter("walker.*"))
    return h, (ws[0] if ws else None)

world = client.get_world()
# walker 등장 대기
while True:
    h, w = pair(world)
    if h is not None and w is not None:
        break
    time.sleep(0.5)
bp = world.get_blueprint_library().find("sensor.camera.rgb")
bp.set_attribute("image_size_x", "960"); bp.set_attribute("image_size_y", "540")
bp.set_attribute("sensor_tick", "0.1")
cam = world.spawn_actor(bp, carla.Transform(
    carla.Location(x=-6.5, z=4.0), carla.Rotation(pitch=-10.0)), attach_to=h)
q = queue.Queue(maxsize=4)
def cb(img):
    try: q.put_nowait(img)
    except Exception: pass
cam.listen(cb)
t0 = time.time(); n = 0
while time.time() - t0 < 45.0:
    try:
        img = q.get(timeout=3.0)
        img.save_to_disk(f"{OUT}/f{n:04d}.png"); n += 1
    except Exception:
        break
    if pair(world)[1] is None and time.time() - t0 > 8.0:
        break
cam.destroy()
open(f"{OUT}/DONE", "w").write(str(n))
print(f"recorded {n} frames -> {OUT}", flush=True)
