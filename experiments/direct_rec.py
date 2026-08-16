#!/usr/bin/env python3
"""동기 1회 녹화: 보행자 등장 대기 -> 에고 추격캠 40s -> 프레임 저장."""
import os, queue, time
import carla

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/directrec"
os.system(f"rm -rf {OUT}")
os.makedirs(OUT, exist_ok=True)
c = carla.Client("localhost", 2000)
c.set_timeout(10.0)

walker = hero = w = None
for _ in range(360):
    try:
        w = c.get_world()
        ws = list(w.get_actors().filter("walker.*"))
        if ws:
            walker = ws[0]
            for a in w.get_actors().filter("vehicle.*"):
                if a.attributes.get("role_name") in ("hero", "ego_vehicle"):
                    hero = a
            if hero:
                break
    except Exception:
        pass
    time.sleep(1.0)
if not (walker and hero):
    print("NO ENCOUNTER WINDOW", flush=True)
    raise SystemExit(1)
print("recording start", flush=True)
bp = w.get_blueprint_library().find("sensor.camera.rgb")
bp.set_attribute("image_size_x", "960")
bp.set_attribute("image_size_y", "540")
bp.set_attribute("sensor_tick", "0.1")
cam = w.spawn_actor(bp, carla.Transform(carla.Location(x=-6.5, z=4.0),
                    carla.Rotation(pitch=-10.0)), attach_to=hero)
q = queue.Queue(maxsize=4)

def cb(im):
    try:
        q.put_nowait(im)
    except Exception:
        pass

cam.listen(cb)
n = 0
t0 = time.time()
while time.time() - t0 < 40.0:
    try:
        im = q.get(timeout=3.0)
        im.save_to_disk(f"{OUT}/f{n:04d}.png")
        n += 1
    except Exception:
        break
try:
    cam.destroy()
except Exception:
    pass
print("frames", n, flush=True)
