#!/usr/bin/env python3
"""fig_candidates_map_en.png — MRM candidate map on the CARLA aerial capture.
0826: back to the aerial-background version, but shoulder candidates are drawn as
their actual lanelet polygons (red) instead of dot markers; parking lots as in the
initial version (blue polygon + square marker); junction markers removed."""
import sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, "/home/taewook/autoware_carla_leaderboard/experiments/analysis")
sys.path.insert(0, "/home/taewook/fs_ws/src/mrm_supervisor/mrm_supervisor")
import ieee_style as st
matplotlib.rcParams["font.family"] = ["STIXGeneral"]
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
from map_model import MapModel

R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
OUT = "/home/taewook/autoware_carla_leaderboard/doc/figs/en/fig_candidates_map_en.png"

mm = MapModel("/home/taewook/awcl_maps/Town07/lanelet2_map.osm")
cands = mm.extract_candidates(["F", "FR"], ["F", "FL", "FR", "B", "RL", "RR"])
shc = [c for c in cands if c.kind == "shoulder"]
pkc = [c for c in cands if c.kind == "parking_lot"]
sh_ids = {c.name.split("_", 1)[1] for c in shc}

mp = np.load(f"{R}/town07_ros_aligned.npz")
T = mp["img"]; ext = list(mp["extent"])
Tl = (T.astype(float) * 0.60 + 255 * 0.40).astype(np.uint8)

rows = [r for r in csv.DictReader(open(f"{R}/ego_path_nf.csv")) if r["src"] == "kin"]
px = np.array([float(r["x"]) for r in rows])
py = np.array([float(r["y"]) for r in rows])

fig, ax = plt.subplots(figsize=(3.5, 4.5))
ax.imshow(Tl, extent=ext, origin="lower", interpolation="bilinear")
ax.plot(px, py, color=st.GRAY, lw=0.9, ls=(0, (4, 2)))
for name, pts in mm.parking_lots.items():
    ax.add_patch(MPoly(np.array(pts), closed=True, facecolor=st.BLUE, alpha=0.25,
                       edgecolor=st.BLUE, lw=0.7))
# shoulder candidates: actual lanelet polygons (left bound + reversed right bound)
for lid in sh_ids:
    ll = mm.lanelets[lid]
    lp, rp = mm._ways.get(ll["left"]), mm._ways.get(ll["right"])
    if not lp or not rp:
        continue
    ax.add_patch(MPoly(list(lp) + list(reversed(rp)), closed=True,
                       facecolor=st.RED, alpha=0.85, edgecolor="black", lw=0.4, zorder=3))
for c in pkc:
    ax.plot(c.x, c.y, marker="s", ms=4, mfc=st.BLUE, mec="black", mew=0.5, ls="none")

allx = np.concatenate([px, [c.x for c in cands]])
ally = np.concatenate([py, [c.y for c in cands]])
m = 22
ax.set_xlim(allx.min() - m, allx.max() + m)
ax.set_ylim(ally.min() - m, ally.max() + m)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
route_len = float(np.hypot(np.diff(px), np.diff(py)).sum())
h = [MPoly([(0, 0)] * 3, fc=st.RED, alpha=0.85, ec="black",
           label=f"shoulder candidates ({len(shc)}, lanelets)"),
     plt.Line2D([], [], marker="s", ls="none", ms=4.5, mfc=st.BLUE, mec="black",
                label=f"parking-lot candidates ({len(pkc)}, polygons)"),
     plt.Line2D([], [], color=st.GRAY, lw=0.9, ls=(0, (4, 2)),
                label=f"reference route ({route_len:.0f} m)")]
ax.legend(handles=h, loc="lower left", fontsize=5.6)
st.clean_axes(ax)
plt.savefig(OUT)
print("saved", len(shc), "shoulder,", len(pkc), "parking")
