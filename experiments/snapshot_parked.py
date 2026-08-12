#!/usr/bin/env python3
"""실측 주차 완료 지점 (-40.0, -8.6) 재현 촬영 — PARKED_SUCCESS 케이스."""
import math, os, queue, time
import carla
import numpy as np
from PIL import Image
OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/snapshots_v2"
client = carla.Client("localhost", 2000); client.set_timeout(120.0)
world = client.get_world()
if "Town07" not in world.get_map().name:
    world = client.load_world("Town07"); time.sleep(5.0)
world.set_weather(carla.WeatherParameters(cloudiness=25.0, sun_altitude_angle=45.0, sun_azimuth_angle=210.0))
bp = world.get_blueprint_library().find("vehicle.tesla.model3")
bp.set_attribute("color", "17,37,103")
x, y, yaw = -42.5, 8.6, -90.0   # map(-40,-8.6, 북향) -> CARLA(y반전)
veh = None
for z in (1.5, 2.5, 0.6):
    veh = world.try_spawn_actor(bp, carla.Transform(carla.Location(x=x, y=y, z=z), carla.Rotation(yaw=yaw)))
    if veh: break
time.sleep(2.5)
veh.set_simulate_physics(False)
loc = veh.get_location(); x, y = loc.x, loc.y
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
car = carla.Location(x=x, y=y, z=0.8)
views = [
    ("rear34", carla.Location(x=x + 7.0, y=y - 6.0, z=3.0)),      # 도로 쪽에서 내려다보기
    ("road",   carla.Location(x=x + 2.0, y=y - 7.5, z=2.2)),      # 도로에서 본 진입 방향... 
    ("top",    None),
]
for name, loc2 in views:
    tf = (carla.Transform(carla.Location(x=x, y=y, z=30.0), carla.Rotation(pitch=-90.0, yaw=yaw)) if loc2 is None
          else carla.Transform(loc2, aim(loc2, car)))
    arr = grab(tf)
    p = f"{OUT}/parked_success_900000_{name}.png"
    for _ in range(3):
        Image.fromarray(arr).save(p)
        if os.path.getsize(p) > 100000: break
    print(os.path.basename(p), os.path.getsize(p))
veh.destroy()
