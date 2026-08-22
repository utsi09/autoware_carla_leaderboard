#!/usr/bin/env python3
"""Town07 탑다운 정사영급 캡처: z=250 fov 90 → 500m 스팬, 2000px."""
import carla, numpy as np, time, sys
c = carla.Client("localhost", 2000); c.set_timeout(30.0)
w = c.get_world()
s = w.get_settings(); s.synchronous_mode = False; w.apply_settings(s)
if "Town07" not in w.get_map().name:
    w = c.load_world("Town07"); time.sleep(5)
CX, CY, Z, FOV, PX = -100.0, -90.0, 250.0, 90.0, 2000   # CARLA 좌표 (y부호 주의)
bp = w.get_blueprint_library().find("sensor.camera.rgb")
bp.set_attribute("image_size_x", str(PX)); bp.set_attribute("image_size_y", str(PX))
bp.set_attribute("fov", str(FOV))
tf = carla.Transform(carla.Location(x=CX, y=CY, z=Z), carla.Rotation(pitch=-90))
cam = w.spawn_actor(bp, tf)
done = {"ok": False}
def cb(img):
    if done["ok"]: return
    a = np.frombuffer(img.raw_data, np.uint8).reshape(img.height, img.width, 4)[:, :, :3][:, :, ::-1]
    np.save("/home/taewook/autoware_carla_leaderboard/experiments/results/town07_topdown.npy", a.copy())
    np.save("/home/taewook/autoware_carla_leaderboard/experiments/results/town07_topdown_meta.npy",
            np.array([CX, CY, Z, FOV, PX]))
    done["ok"] = True; print("saved", a.shape)
cam.listen(cb)
t0 = time.time()
while not done["ok"] and time.time() - t0 < 15: time.sleep(0.2)
cam.stop(); cam.destroy()
print("DONE" if done["ok"] else "TIMEOUT")
