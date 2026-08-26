#!/usr/bin/env python3
"""fig_candidates_map_en.png — MRM candidate map drawn from the actual lanelet2 map
(0826: real road geometry instead of the CARLA aerial capture; shoulder/parking
candidates distinguished by fill color; junction markers dropped; route kept)."""
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
sh_ids = {c.name.split("_", 1)[1] for c in cands if c.kind == "shoulder"}
n_sh = len([c for c in cands if c.kind == "shoulder"])
n_pk = len([c for c in cands if c.kind == "parking_lot"])

rows = [r for r in csv.DictReader(open(f"{R}/ego_path_nf.csv")) if r["src"] == "kin"]
px = np.array([float(r["x"]) for r in rows])
py = np.array([float(r["y"]) for r in rows])

C_ROAD = "#e2e4e8"; C_ROAD_EC = "#c8cbd2"
C_SH = "#c65b4e"; C_SH_OTHER = "#d8b8b2"
C_PK = "#5b7fa6"

fig, ax = plt.subplots(figsize=(3.5, 4.2))
for lid, ll in mm.lanelets.items():
    lp, rp = mm._ways.get(ll["left"]), mm._ways.get(ll["right"])
    if not lp or not rp:
        continue
    poly = list(lp) + list(reversed(rp))
    if ll["subtype"] == "road":
        ax.add_patch(MPoly(poly, closed=True, fc=C_ROAD, ec=C_ROAD_EC, lw=0.3, zorder=1))
    elif ll["subtype"] == "road_shoulder":
        cand = lid in sh_ids
        ax.add_patch(MPoly(poly, closed=True,
                           fc=(C_SH if cand else C_SH_OTHER),
                           ec="black", lw=0.35 if cand else 0.2,
                           alpha=0.95, zorder=2))
for wid, pts in mm.parking_lots.items():
    ax.add_patch(MPoly(pts, closed=True, fc=C_PK, ec="black", lw=0.4, alpha=0.75, zorder=2))
# parking_space는 2점 축선 — 실제 주차선처럼 폭 2.5 m 칸 사각형 외곽선으로 그린다
BAY_HALF_W = 1.25
for wid, pts in mm.parking_spaces.items():
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    L = np.hypot(x1 - x0, y1 - y0)
    if L < 0.5:
        continue
    nx, ny = -(y1 - y0) / L * BAY_HALF_W, (x1 - x0) / L * BAY_HALF_W
    bay = [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
           (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]
    ax.add_patch(MPoly(bay, closed=True, fc="none", ec="white", lw=0.55,
                       alpha=0.95, zorder=3))

ax.plot(px, py, color="#3a3a44", lw=1.0, ls=(0, (4, 2)), zorder=4)

m = 25
ax.set_xlim(px.min() - m, px.max() + m)
ax.set_ylim(py.min() - m, py.max() + m)
ax.set_aspect("equal")
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")

h = [MPoly([(0, 0)] * 3, fc=C_ROAD, ec=C_ROAD_EC, label="road lanelets"),
     MPoly([(0, 0)] * 3, fc=C_SH, ec="black", label=f"shoulder candidates ({n_sh})"),
     MPoly([(0, 0)] * 3, fc=C_PK, ec="black", alpha=0.75, label=f"parking-lot candidates ({n_pk})"),
     plt.Line2D([], [], color="#3a3a44", lw=1.0, ls=(0, (4, 2)), label="reference route")]
ax.legend(handles=h, loc="lower left", fontsize=6.2, handletextpad=0.5, framealpha=0.9)

sx, sy = px.max() + m - 62, py.min() - m + 9
ax.plot([sx, sx + 50], [sy, sy], color="black", lw=1.6)
ax.text(sx + 25, sy + 4, "50 m", ha="center", fontsize=6.5)
st.clean_axes(ax)
plt.savefig(OUT)
print("saved", n_sh, "shoulder,", n_pk, "parking")
