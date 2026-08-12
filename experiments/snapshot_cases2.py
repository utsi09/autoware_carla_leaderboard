#!/usr/bin/env python3
"""논문용 스냅샷 v2 — 최근접 실측 갓길 4케이스 + 주차장 연출(staged) 2케이스.

갓길 4곳은 캠페인 CSV 실측 정차 좌표 그대로, 주차장 2곳은 후보 위치에
차량을 배치한 '연출' 캡처(파일명에 staged_ 명시). 1920x1080, 3앵글.
"""
import math
import os
import queue
import time

import carla
import numpy as np
from PIL import Image

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/snapshots_v2"
MIN_BYTES = 100_000

# (이름, CARLA x, y, yaw)
CASES = [
    ("caseA_gn_mid_t45_agg_shoulder1002323_d2.3m", -107.2, -35.9, 179.6),
    ("caseB_ln_mid_t26_agg_shoulder1002445_d2.4m", -57.2, -5.2, 179.5),
    ("caseC_ln_high_t45_agg_shoulder1002455_d2.8m", -94.0, -3.1, -160.5),
    ("caseD_lf_mid_t36_def_shoulder1002284_d2.9m", -1.9, 7.8, -89.5),
    ("staged_parking_space_1002367", -22.4, -8.6, -88.0),
    ("staged_parking_lot_1002178", -52.7, -70.1, 179.4),
]


def aim(cam, tgt):
    dx, dy, dz = tgt.x - cam.x, tgt.y - cam.y, tgt.z - cam.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return carla.Rotation(pitch=pitch, yaw=yaw)


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
        tf = carla.Transform(carla.Location(x=x, y=y, z=0.3), carla.Rotation(yaw=yaw))
        veh = world.try_spawn_actor(bp, tf)
        if veh is None:
            tf.location.z = 0.7
            veh = world.try_spawn_actor(bp, tf)
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
        front = carla.Location(x=x + 9.0 * f[0] - 4.5 * rt[0],
                               y=y + 9.0 * f[1] - 4.5 * rt[1], z=2.6)
        views = [
            ("rear34", carla.Transform(rear, aim(rear, car))),
            ("front34", carla.Transform(front, aim(front, car))),
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
