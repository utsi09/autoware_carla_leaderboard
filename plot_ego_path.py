#!/usr/bin/env python3
"""Plot the TRUE ego path (gnss, flipped back to CARLA frame) over the route+map."""
import csv
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_lanelet(p):
    root = ET.parse(p).getroot()
    nodes = {}
    for n in root.findall("node"):
        t = {x.get("k"): x.get("v") for x in n.findall("tag")}
        if "local_x" in t and "local_y" in t:
            nodes[n.get("id")] = (float(t["local_x"]), float(t["local_y"]))
    out = []
    for w in root.findall("way"):
        pts = [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes]
        if len(pts) >= 2:
            out.append(pts)
    return out


def load_route(p):
    wps = ET.parse(p).getroot().find("route").find("waypoints")
    return [(float(q.get("x")), float(q.get("y"))) for q in wps.findall("position")]


# gnss = true pose in ROS frame -> flip y back to CARLA frame to compare with route
gx, gy = [], []
for r in csv.DictReader(open("ego_path.csv")):
    if r["src"] == "gnss":
        gx.append(float(r["x"]))
        gy.append(-float(r["y"]))   # ROS -> CARLA

lines = load_lanelet("/home/taewook/awcl_maps/Town07/lanelet2_map.osm")
wps = load_route("resources/routes/town07_perimeter_fixed.xml")

fig, ax = plt.subplots(figsize=(11, 13))
for i, pl in enumerate(lines):
    ax.plot([p[0] for p in pl], [p[1] for p in pl], color="0.8", lw=0.5,
            label="Lanelet map" if i == 0 else None, zorder=1)

ax.plot([p[0] for p in wps], [p[1] for p in wps], color="crimson", lw=2.2,
        label="Route (should drive)", zorder=3)
ax.scatter([wps[0][0]], [wps[0][1]], c="red", s=200, marker="*", ec="black",
           label="Route start wp0 (-193,245)", zorder=6)

ax.plot(gx, gy, color="royalblue", lw=2.4, label="ACTUAL ego path (CARLA truth)", zorder=4)
ax.scatter([gx[0]], [gy[0]], c="lime", s=180, marker="o", ec="black",
           label=f"Ego SPAWN ({gx[0]:.0f},{gy[0]:.0f})", zorder=6)
ax.scatter([gx[-1]], [gy[-1]], c="orange", s=200, marker="X", ec="black",
           label="Deviated / end", zorder=7)

ax.set_aspect("equal")
ax.set_xlabel("x [m] (CARLA)")
ax.set_ylabel("y [m] (CARLA)")
ax.set_title("ACTUAL ego path vs intended route (Town07 perimeter)")
ax.legend(loc="upper right", framealpha=0.9)
ax.grid(True, ls=":", alpha=0.4)
fig.tight_layout()
fig.savefig("ego_vs_route.png", dpi=130)
print("saved ego_vs_route.png  | spawn=(%.1f,%.1f) end=(%.1f,%.1f)" % (gx[0], gy[0], gx[-1], gy[-1]))
