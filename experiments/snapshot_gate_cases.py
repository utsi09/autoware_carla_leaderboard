#!/usr/bin/env python3
"""게이트 배터리 각 케이스의 최종 MRM 정차 상태를 staged 캡처.

CSV의 실측 정차 좌표(stop_x/stop_y, AW map frame)에 차량을 배치해 촬영.
AW->CARLA: x 동일, y 부호 반전, yaw 부호 반전.
yaw 결정: PARKED(주차 완료)는 goal 축(AW -90도, 북향 후진주차)=CARLA +90.
그 외(도로 정차)는 맵에서 최근접 way 세그먼트 방향을 도로 진행방향으로 사용.
사용: (lb 컨테이너 안에서) python3 snapshot_gate_cases.py <results.csv>
"""
import csv
import math
import os
import queue
import sys
import time
import xml.etree.ElementTree as ET

import carla
import numpy as np
from PIL import Image

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results/snapshots_v45_gate"
MAP_OSM = "/home/taewook/autoware_carla_leaderboard/experiments/results/lanelet2_map_for_snapshot.osm"
MIN_BYTES = 100_000


def load_map_segments():
    r = ET.parse(MAP_OSM).getroot()
    nodes = {}
    for n in r.findall("node"):
        lx = ly = None
        for tg in n.findall("tag"):
            if tg.get("k") == "local_x":
                lx = float(tg.get("v"))
            if tg.get("k") == "local_y":
                ly = float(tg.get("v"))
        if lx is not None:
            nodes[n.get("id")] = (lx, ly)
    segs = []
    for w in r.findall("way"):
        refs = [nd.get("ref") for nd in w.findall("nd")]
        pts = [nodes[x] for x in refs if x in nodes]
        for a, b in zip(pts, pts[1:]):
            segs.append((a, b))
    return segs


def road_yaw_aw(segs, x, y):
    best_d, best_ang = 1e9, 0.0
    for (ax, ay), (bx, by) in segs:
        abx, aby = bx - ax, by - ay
        ln2 = abx * abx + aby * aby
        if ln2 < 1e-6:
            continue
        t = max(0.0, min(1.0, ((x - ax) * abx + (y - ay) * aby) / ln2))
        d = math.hypot(x - (ax + t * abx), y - (ay + t * aby))
        if d < best_d:
            best_d, best_ang = d, math.atan2(aby, abx)
    return math.degrees(best_ang)


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
    rows = list(csv.DictReader(open(sys.argv[1])))
    segs = load_map_segments()
    os.makedirs(OUT, exist_ok=True)
    os.chmod(OUT, 0o777)

    client = carla.Client("localhost", 2000)
    client.set_timeout(120.0)
    world = client.get_world()
    if "Town07" not in world.get_map().name:
        world = client.load_world("Town07")
        time.sleep(5.0)
    for a in world.get_actors().filter("vehicle.*"):
        a.destroy()
    time.sleep(1.0)
    world.set_weather(carla.WeatherParameters(
        cloudiness=25.0, precipitation=0.0, sun_altitude_angle=45.0,
        sun_azimuth_angle=210.0, wind_intensity=5.0))

    bp = world.get_blueprint_library().find("vehicle.tesla.model3")
    bp.set_attribute("color", "17,37,103")
    for row in rows:
        if not row.get("stop_x"):
            print(f"case{row['idx']}: no stop pose ({row['outcome']}) — skip")
            continue
        ax, ay = float(row["stop_x"]), float(row["stop_y"])
        parked = row["outcome"] == "PARKED_SUCCESS"
        lot = row["final_state"].split(":")[-1] if ":" in row["final_state"] else ""
        lot_yaw = {"parking_1002367": 90.0, "parking_1003001": 90.0,
                   "parking_1003002": 90.0, "parking_1003003": -90.0}
        yaw_aw = lot_yaw.get(lot, -90.0) if parked else road_yaw_aw(segs, ax, ay)
        x, y, yaw = ax, -ay, -yaw_aw
        name = (f"case{int(row['idx'])+1:02d}_{row['fault']}{row['severity']}"
                f"_t{row['trigger_s']}_{row['npc']}{row['rep']}"
                f"_{lot.replace('parking_', 'lot')}_{row['outcome']}")
        tf = carla.Transform(carla.Location(x=x, y=y, z=0.3),
                             carla.Rotation(yaw=yaw))
        veh = world.try_spawn_actor(bp, tf)
        if veh is None:
            tf.location.z = 0.7
            veh = world.try_spawn_actor(bp, tf)
        if veh is None:
            print(name, "SPAWN FAILED")
            continue
        time.sleep(2.5)
        veh.set_simulate_physics(False)
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
                continue
            ok = save_verified(arr, path)
            print(path, "OK" if ok else "TOO SMALL")
        veh.destroy()
    print("SNAPSHOT_DONE")


if __name__ == "__main__":
    main()
