#!/usr/bin/env python3
"""에고-보행자 최근접 순간 캡처. 거리 추적하다가 (a) 6 m 미만이거나
(b) 최근접 통과(거리 재증가) 순간, 두 액터 중간 지점 상공에서 촬영."""
import math, queue, time
import carla

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results"
client = carla.Client("localhost", 2000); client.set_timeout(8.0)

def pair(world):
    h = None
    for a in world.get_actors().filter("vehicle.*"):
        if a.attributes.get("role_name") in ("hero", "ego_vehicle"):
            h = a; break
    ws = list(world.get_actors().filter("walker.*"))
    return h, (ws[0] if ws else None)

world = client.get_world()
min_d = 1e9
while True:
    h, w = pair(world)
    if h is None or w is None:
        time.sleep(0.5); min_d = 1e9; continue
    hl, wl = h.get_transform().location, w.get_transform().location
    d = math.hypot(hl.x - wl.x, hl.y - wl.y)
    if d < min_d:
        min_d = d
    fire = (d < 6.0) or (min_d < 20.0 and d > min_d + 1.0)
    if not fire:
        time.sleep(0.1); continue
    # 최근접! 중간 지점 상공에서 두 액터 프레임인
    mx, my = (hl.x + wl.x) / 2.0, (hl.y + wl.y) / 2.0
    z = max(12.0, d * 1.6)
    bp = world.get_blueprint_library().find("sensor.camera.rgb")
    bp.set_attribute("image_size_x", "1600"); bp.set_attribute("image_size_y", "900")
    cam = world.spawn_actor(bp, carla.Transform(
        carla.Location(x=mx, y=my, z=hl.z + z), carla.Rotation(pitch=-90.0)))
    q = queue.Queue(); cam.listen(q.put)
    img = q.get(timeout=5.0)
    img.save_to_disk(f"{OUT}/ped_closest_{int(time.time())}.png")
    cam.destroy()
    print(f"CLOSEST captured d={d:.1f}m (min {min_d:.1f}) ego({hl.x:.1f},{hl.y:.1f}) "
          f"ped({wl.x:.1f},{wl.y:.1f})", flush=True)
    # 이 케이스는 완료 — 보행자 소멸까지 대기 후 다음 케이스로
    while pair(world)[1] is not None:
        time.sleep(2.0)
    min_d = 1e9
