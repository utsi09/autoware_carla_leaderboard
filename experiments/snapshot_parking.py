#!/usr/bin/env python3
"""주차 후보 전체 연출(staged) 캡처 — 비용함수 후보인 주차공간/주차장 7곳.

전부 연출(staged): 후보 좌표에 차량을 배치해 촬영. rear34 + top 2앵글, 1920x1080.
"""
import math
import os
import queue
import time

import carla
import numpy as np
from PIL import Image

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/snapshots_parking"
MIN_BYTES = 100_000

# (이름, CARLA x, y, yaw)
CASES = [
    ("staged_pspace_1002367_farmpad", -22.4, -8.6, -88.0),
    ("staged_pspace_1002518_farmpad", -45.8, -10.8, -88.0),
    ("staged_plot_1002178_barnlot_stall", -52.7, -70.1, 179.4),
    ("staged_plot_1002178_barnlot_stall2", -40.0, -70.5, -90.0),   # 같은 주차장, 스톨 전면주차
    ("staged_plot_1002192_barnlot2", -45.8, -86.0, 179.6),
    ("staged_plot_1002396_bigfield", -140.5, -156.5, -0.5),
    ("staged_pspace_1002601_westpad", -147.9, -94.0, 1.9),
    ("staged_pspace_1002629_westpad2", -140.1, -109.0, 1.9),
]


def aim(cam, tgt):
    dx, dy, dz = tgt.x - cam.x, tgt.y - cam.y, tgt.z - cam.z
    return carla.Rotation(pitch=math.degrees(math.atan2(dz, math.hypot(dx, dy))),
                          yaw=math.degrees(math.atan2(dy, dx)))


def grab(world, cam_tf):
    bp = world.get_blueprint_library().find("sensor.camera.rgb")
    bp.set_attribute("image_size_x", "1920")
    bp.set_attribute("image_size_y", "1080")
    cam = world.spawn_actor(bp, cam_tf)
    q = queue.Queue()
    cam.listen(q.put)
    img = None
    try:
        deadline = time.time() + 12.0
        n = 0
        while time.time() < deadline:
            try:
                img = q.get(timeout=2.0)
            except queue.Empty:
                continue
            n += 1
            if n >= 10:
                break
    finally:
        cam.stop()
        cam.destroy()
    if img is None:
        return None
    arr = np.frombuffer(img.raw_data, dtype=np.uint8).reshape(img.height, img.width, 4)
    return arr[:, :, [2, 1, 0]]


def save_verified(arr, path):
    for _ in range(3):
        Image.fromarray(arr).save(path)
        if os.path.getsize(path) >= MIN_BYTES:
            return True
        time.sleep(0.5)
    return False


def main():
    os.makedirs(OUT, exist_ok=True)
    os.chmod(OUT, 0o777)
    client = carla.Client("localhost", 2000)
    client.set_timeout(120.0)
    world = client.get_world()
    if "Town07" not in world.get_map().name:
        world = client.load_world("Town07")
        time.sleep(5.0)
    world.set_weather(carla.WeatherParameters(
        cloudiness=25.0, precipitation=0.0, sun_altitude_angle=45.0,
        sun_azimuth_angle=210.0, wind_intensity=5.0))

    bp = world.get_blueprint_library().find("vehicle.tesla.model3")
    bp.set_attribute("color", "17,37,103")
    for name, x, y, yaw in CASES:
        veh = None
        for z in (0.3, 0.7, 1.2):
            tf = carla.Transform(carla.Location(x=x, y=y, z=z), carla.Rotation(yaw=yaw))
            veh = world.try_spawn_actor(bp, tf)
            if veh:
                break
        if veh is None:
            print(name, "SPAWN FAILED")
            continue
        time.sleep(2.5)                    # 물리 켠 채 착지 대기
        veh.set_simulate_physics(False)    # 착지 후 고정
        loc = veh.get_location()
        x, y = loc.x, loc.y
        r = math.radians(yaw)
        f = (math.cos(r), math.sin(r))
        rt = (math.cos(r + math.pi / 2), math.sin(r + math.pi / 2))
        car = carla.Location(x=x, y=y, z=0.8)
        rear = carla.Location(x=x - 8.5 * f[0] - 4.5 * rt[0],
                              y=y - 8.5 * f[1] - 4.5 * rt[1], z=2.8)
        views = [
            ("rear34", carla.Transform(rear, aim(rear, car))),
            ("top", carla.Transform(carla.Location(x=x, y=y, z=26.0),
                                    carla.Rotation(pitch=-90.0, yaw=yaw))),
        ]
        for vname, cam_tf in views:
            arr = grab(world, cam_tf)
            path = f"{OUT}/{name}_{vname}.png"
            if arr is None:
                print(path, "CAPTURE FAILED")
            elif save_verified(arr, path):
                print(os.path.basename(path), os.path.getsize(path), "OK")
            else:
                print(path, "TOO SMALL")
        veh.destroy()
        time.sleep(0.5)
    print("done")


if __name__ == "__main__":
    main()
