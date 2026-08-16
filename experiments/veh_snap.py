#!/usr/bin/env python3
"""장애물/갓길점유 차량 근접 순간 자동 캡처 (검증용). LB 컨테이너에서 실행.
주입 차량(tesla.model3=장애물, audi.tt=갓길 블로커)이 에고 30 m 안에 들어오면
에고 후방 체이스캠 3프레임 저장. 종류별 1회씩 찍으면 종료."""
import queue, time
import carla

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results"
TARGETS = {"vehicle.tesla.model3": "obstacle", "vehicle.audi.tt": "shoulderblock"}
client = carla.Client("localhost", 2000); client.set_timeout(10.0)
done = set()

while len(done) < len(TARGETS):
    try:
        world = client.get_world()
        hero = None
        for a in world.get_actors().filter("vehicle.*"):
            if a.attributes.get("role_name") in ("hero", "ego_vehicle"):
                hero = a; break
        if hero is None:
            time.sleep(1.0); continue
        shot = None
        for a in world.get_actors().filter("vehicle.*"):
            kind = TARGETS.get(a.type_id)
            if kind and kind not in done:
                d = hero.get_transform().location.distance(a.get_transform().location)
                if d < 30.0:
                    shot = (kind, d); break
        if shot is None:
            time.sleep(0.3); continue
        kind, d = shot
        bp = world.get_blueprint_library().find("sensor.camera.rgb")
        bp.set_attribute("image_size_x", "1600"); bp.set_attribute("image_size_y", "900")
        cam = world.spawn_actor(
            bp, carla.Transform(carla.Location(x=-7.0, z=4.0),
                                carla.Rotation(pitch=-10.0)), attach_to=hero)
        q = queue.Queue(); cam.listen(q.put)
        for i in range(3):
            img = q.get(timeout=5.0)
            img.save_to_disk(f"{OUT}/{kind}_close_{i}.png")
        cam.destroy()
        done.add(kind)
        print(f"captured {kind} at d={d:.1f}m", flush=True)
    except Exception as e:
        print("retry:", e, flush=True); time.sleep(2.0)
print("done", flush=True)
