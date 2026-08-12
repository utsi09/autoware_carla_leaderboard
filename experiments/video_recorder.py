#!/usr/bin/env python3
"""ego 추적 체이스캠 프레임 녹화 (성공 판 영상용). LB 컨테이너에서 실행."""
import math, os, queue, time, sys
import carla
import numpy as np
from PIL import Image
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/taewook/autoware_carla_leaderboard/experiments/results/frames"
os.makedirs(OUT, exist_ok=True); os.chmod(OUT, 0o777)
client = carla.Client("localhost", 2000); client.set_timeout(30.0)

def find_hero(world):
    for a in world.get_actors().filter('vehicle.audi.etron'):
        return a
    return None

n_frame = 0
t_end = time.time() + 1500
while time.time() < t_end:
    try:
        world = client.get_world()
        hero = find_hero(world)
        if hero is None:
            time.sleep(2); continue
        bp = world.get_blueprint_library().find('sensor.camera.rgb')
        bp.set_attribute('image_size_x', '1280'); bp.set_attribute('image_size_y', '720')
        q = queue.Queue(maxsize=4)
        cam = world.spawn_actor(
            bp, carla.Transform(carla.Location(x=-7.5, z=3.4), carla.Rotation(pitch=-12.0)),
            attach_to=hero)
        cam.listen(lambda img: (not q.full()) and q.put(img))
        last_save = 0.0
        try:
            while True:
                try:
                    img = q.get(timeout=3.0)
                except queue.Empty:
                    break   # 월드 리셋/ego 소멸
                if time.time() - last_save < 0.12:   # ~8fps
                    continue
                last_save = time.time()
                a = np.frombuffer(img.raw_data, dtype=np.uint8).reshape(img.height, img.width, 4)
                Image.fromarray(a[:, :, [2, 1, 0]]).save(f"{OUT}/f{n_frame:06d}.jpg", quality=88)
                n_frame += 1
        finally:
            try: cam.stop(); cam.destroy()
            except Exception: pass
        print(f"segment end, frames={n_frame}", flush=True)
    except Exception as e:
        print("retry:", e, flush=True); time.sleep(3)
print("done", n_frame)
