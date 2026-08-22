#!/usr/bin/env python3
"""그림용 1프레임 캡처: Town07에 차량+라이다+카메라 스폰, 스캔 1회 저장.
컨테이너(0.9.16 클라이언트)에서 실행. 출력: experiments/results/figframe_*"""
import carla, numpy as np, time, sys

OUT = "/home/taewook/autoware_carla_leaderboard/experiments/results"

c = carla.Client("localhost", 2000); c.set_timeout(30.0)
w = c.get_world()
# 비동기 안전 리셋 (직전 캠페인이 동기모드로 남겼을 수 있음)
s = w.get_settings(); s.synchronous_mode = False; s.fixed_delta_seconds = None
w.apply_settings(s)
if "Town07" not in w.get_map().name:
    print("loading Town07..."); w = c.load_world("Town07"); time.sleep(5.0)

bp = w.get_blueprint_library()
sp = w.get_map().get_spawn_points()[10]
veh = w.spawn_actor(bp.filter("vehicle.tesla.model3")[0], sp)
time.sleep(1.0)

lbp = bp.find("sensor.lidar.ray_cast")
lbp.set_attribute("range", "100"); lbp.set_attribute("channels", "32")
lbp.set_attribute("points_per_second", "600000")
lbp.set_attribute("rotation_frequency", "10")
lidar = w.spawn_actor(lbp, carla.Transform(carla.Location(z=2.0)), attach_to=veh)

cbp = bp.find("sensor.camera.rgb")
cbp.set_attribute("image_size_x", "800"); cbp.set_attribute("image_size_y", "400")
cam = w.spawn_actor(cbp, carla.Transform(carla.Location(x=1.5, z=1.8)), attach_to=veh)

got = {"l": False, "c": False}
acc = []
def on_lidar(d):
    if got["l"]: return
    pts = np.frombuffer(d.raw_data, np.float32).reshape(-1, 4)  # x,y,z,intensity
    acc.append(pts.copy())                     # 비동기라 부분 회전으로 옴 — 누적
    total = sum(len(a) for a in acc)
    if total > 55000:                          # ~1회전 분량 모이면 저장
        np.save(f"{OUT}/figframe_lidar.npy", np.concatenate(acc))
        got["l"] = True
        print("lidar saved:", total)
def on_cam(img):
    if got["c"]: return
    a = np.frombuffer(img.raw_data, np.uint8).reshape(img.height, img.width, 4)[:, :, :3][:, :, ::-1]
    np.save(f"{OUT}/figframe_cam.npy", a.copy()); got["c"] = True
    print("cam saved:", a.shape)

lidar.listen(on_lidar); cam.listen(on_cam)
t0 = time.time()
while not (got["l"] and got["c"]) and time.time() - t0 < 20:
    time.sleep(0.2)
lidar.stop(); cam.stop()
for a in (lidar, cam, veh): a.destroy()
print("DONE" if got["l"] and got["c"] else "TIMEOUT", flush=True)
sys.exit(0 if got["l"] and got["c"] else 1)
