#!/usr/bin/env python3
"""PARKED_SUCCESS 실차(월드에 잔존한 실제 ego)를 그대로 촬영 — 무연출."""
import math, os, queue, time
import carla
import numpy as np
from PIL import Image
OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/snapshots_v2"
client = carla.Client("localhost", 2000); client.set_timeout(60.0)
world = client.get_world()
target = None
for a in world.get_actors().filter('vehicle.*'):
    L = a.get_location()
    if 'tesla' in a.type_id:
        a.destroy()  # 내 촬영용 테슬라 제거
        continue
    if abs(L.x - (-45.9)) < 6 and abs(L.y - (-8.7)) < 6:
        target = a
if target is None:
    print("REAL EGO NOT FOUND"); raise SystemExit
time.sleep(1.0)
L = target.get_location(); R = target.get_transform().rotation
x, y = L.x, L.y
print(f"real parked ego: {target.type_id} at ({x:.2f},{y:.2f}) yaw={R.yaw:.1f}")
def aim(cam, tgt):
    dx, dy, dz = tgt.x - cam.x, tgt.y - cam.y, tgt.z - cam.z
    return carla.Rotation(pitch=math.degrees(math.atan2(dz, math.hypot(dx, dy))), yaw=math.degrees(math.atan2(dy, dx)))
def grab(tf):
    cb = world.get_blueprint_library().find("sensor.camera.rgb")
    cb.set_attribute("image_size_x", "1920"); cb.set_attribute("image_size_y", "1080")
    cam = world.spawn_actor(cb, tf); q = queue.Queue(); cam.listen(q.put)
    img = None; n = 0; dl = time.time() + 12
    while time.time() < dl:
        try: img = q.get(timeout=2.0)
        except queue.Empty: continue
        n += 1
        if n >= 10: break
    cam.stop(); cam.destroy()
    a = np.frombuffer(img.raw_data, dtype=np.uint8).reshape(img.height, img.width, 4)
    return a[:, :, [2, 1, 0]]
car = carla.Location(x=x, y=y, z=0.9)
shots = [
    ("view_from_road", carla.Location(x=x - 1.0, y=y + 9.5, z=2.4)),
    ("view_side", carla.Location(x=x - 7.5, y=y + 5.0, z=2.6)),
    ("top", None),
]
for name, loc2 in shots:
    tf = (carla.Transform(carla.Location(x=x, y=y, z=28.0), carla.Rotation(pitch=-90.0, yaw=R.yaw)) if loc2 is None
          else carla.Transform(loc2, aim(loc2, car)))
    arr = grab(tf)
    p = f"{OUT}/REAL_pad_parked_{name}.png"
    for _ in range(3):
        Image.fromarray(arr).save(p)
        if os.path.getsize(p) > 100000: break
    print(os.path.basename(p), os.path.getsize(p))
