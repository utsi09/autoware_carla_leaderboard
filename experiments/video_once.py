#!/usr/bin/env python3
"""단발 녹화: hero 등장 대기 → 부착 → 프레임 저장 → 스트림 끊기면 종료."""
import os, queue, time, sys
import carla
import numpy as np
from PIL import Image
OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/frames"
os.makedirs(OUT, exist_ok=True)
seg = int(time.time())
client = carla.Client("localhost", 2000); client.set_timeout(10.0)
world = client.get_world()
hero = None
t0 = time.time()
while time.time() - t0 < 120 and hero is None:
    for a in world.get_actors().filter('vehicle.audi.etron'):
        hero = a; break
    if hero is None: time.sleep(1.5)
if hero is None:
    print("no-hero"); sys.exit(0)
bp = world.get_blueprint_library().find('sensor.camera.rgb')
bp.set_attribute('image_size_x', '1280'); bp.set_attribute('image_size_y', '720')
q = queue.Queue(maxsize=6)
cam = world.spawn_actor(bp, carla.Transform(carla.Location(x=-7.5, z=3.4),
                        carla.Rotation(pitch=-12.0)), attach_to=hero)
def cb(img):
    try: q.put_nowait(img)
    except Exception: pass
cam.listen(cb)
n = 0; last = 0.0
while True:
    try:
        img = q.get(timeout=90.0)  # 주차 전환 틱 정지(A* 30s+GPU 경합)에도 녹화 유지
    except queue.Empty:
        break
    now = time.time()
    if now - last < 0.12: continue
    last = now
    a = np.frombuffer(img.raw_data, dtype=np.uint8).reshape(img.height, img.width, 4)
    Image.fromarray(a[:, :, [2, 1, 0]]).save(f"{OUT}/s{seg}_f{n:06d}.jpg", quality=88)
    n += 1
print(f"segment s{seg} frames={n}")
