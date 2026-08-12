#!/usr/bin/env python3
"""실측 안전대피 완료 지점 스냅샷 캡처.

캠페인 CSV의 stop_x/stop_y(맵 프레임) → CARLA 좌표(y 반전)로 차량을 배치하고
체이스뷰/탑뷰 2장씩 캡처한다. 402바이트 깨진 파일 방지: raw_data를 직접
PNG로 쓰고, 50KB 미만이면 재시도.
"""
import math
import os
import queue
import time

import carla
import numpy as np
from PIL import Image

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/snapshots"

# (이름, CARLA x, y, yaw) — 캠페인 실측 stop 좌표(맵 프레임 y 반전), yaw는 갓길 진행방향
CASES = [
    ("case1_ln_mid_t27_agg_shoulder1002445", -57.9, -5.2, 179.5),
    ("case2_lf_mid_t45_def_shoulder1002450", -89.8, -2.4, 179.5),
    ("case3_gn_mid_t45_agg_shoulder1002323", -107.2, -35.9, 179.6),
    ("case4_ln_mid_t30_def_shoulder1002291", -25.3, -3.2, 179.4),
]

MIN_BYTES = 50_000


def grab(world, cam_tf, tries=3):
    bp = world.get_blueprint_library().find("sensor.camera.rgb")
    bp.set_attribute("image_size_x", "1280")
    bp.set_attribute("image_size_y", "720")
    cam = world.spawn_actor(bp, cam_tf)
    q = queue.Queue()
    cam.listen(q.put)
    img = None
    try:
        # 노출 안정화: 앞 프레임 몇 장 버림
        deadline = time.time() + 10.0
        n = 0
        while time.time() < deadline:
            try:
                img = q.get(timeout=2.0)
            except queue.Empty:
                continue
            n += 1
            if n >= 8:
                break
    finally:
        cam.stop()
        cam.destroy()
    if img is None:
        return None
    arr = np.frombuffer(img.raw_data, dtype=np.uint8).reshape(img.height, img.width, 4)
    return arr[:, :, [2, 1, 0]]  # BGRA -> RGB


def save_verified(arr, path):
    for _ in range(3):
        Image.fromarray(arr).save(path)
        if os.path.getsize(path) >= MIN_BYTES:
            return True
        time.sleep(0.5)
    return False


def main():
    os.makedirs(OUT, exist_ok=True)
    client = carla.Client("localhost", 2000)
    client.set_timeout(120.0)
    world = client.get_world()
    if "Town07" not in world.get_map().name:
        print("loading Town07 ...")
        world = client.load_world("Town07")
        time.sleep(5.0)
    world.set_weather(carla.WeatherParameters.ClearNoon)

    bp = world.get_blueprint_library().find("vehicle.tesla.model3")
    for name, x, y, yaw in CASES:
        tf = carla.Transform(carla.Location(x=x, y=y, z=0.3), carla.Rotation(yaw=yaw))
        veh = world.try_spawn_actor(bp, tf)
        if veh is None:
            tf.location.z = 0.6
            veh = world.try_spawn_actor(bp, tf)
        if veh is None:
            print(name, "SPAWN FAILED")
            continue
        veh.set_simulate_physics(False)
        time.sleep(1.0)
        rad = math.radians(yaw)
        back = carla.Location(x=x - 11.0 * math.cos(rad), y=y - 11.0 * math.sin(rad), z=4.5)
        views = [
            ("chase", carla.Transform(back, carla.Rotation(pitch=-15.0, yaw=yaw))),
            ("top", carla.Transform(carla.Location(x=x, y=y, z=42.0),
                                    carla.Rotation(pitch=-90.0, yaw=yaw))),
        ]
        for vname, cam_tf in views:
            arr = grab(world, cam_tf)
            path = f"{OUT}/{name}_{vname}.png"
            if arr is None:
                print(path, "CAPTURE FAILED")
            elif save_verified(arr, path):
                print(path, os.path.getsize(path), "bytes OK")
            else:
                print(path, "TOO SMALL after retries")
        veh.destroy()
        time.sleep(0.5)
    print("done")


if __name__ == "__main__":
    main()
