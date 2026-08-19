#!/usr/bin/env python3
"""Overlay a leaderboard route onto the Town07 lanelet2 map and save a PNG.

The route XML (CARLA world coords) and the lanelet2 map local_x/local_y are in
the same frame for these CARLA-built maps, so no axis flip is needed.
"""
import argparse
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_lanelet(osm_path):
    """Return list of polylines (each a list of (x, y)) from lanelet2 ways."""
    root = ET.parse(osm_path).getroot()
    nodes = {}
    for n in root.findall("node"):
        tags = {t.get("k"): t.get("v") for t in n.findall("tag")}
        if "local_x" in tags and "local_y" in tags:
            nodes[n.get("id")] = (float(tags["local_x"]), float(tags["local_y"]))
    lines = []
    for w in root.findall("way"):
        pts = [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes]
        if len(pts) >= 2:
            lines.append(pts)
    return lines


def load_route(route_path):
    """Return list of (x, y) waypoints from the leaderboard route XML."""
    root = ET.parse(route_path).getroot()
    route = root.find("route")
    wps = route.find("waypoints")
    return [(float(p.get("x")), float(p.get("y"))) for p in wps.findall("position")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osm", default="/home/taewook/awcl_maps/Town07/lanelet2_map.osm")
    ap.add_argument("--route", default="resources/routes/town07_perimeter.xml")
    ap.add_argument("--out", default="route_town07_perimeter.png")
    args = ap.parse_args()

    lines = load_lanelet(args.osm)
    wps = load_route(args.route)
    rx = [p[0] for p in wps]
    ry = [p[1] for p in wps]

    # Deviation points observed in the two leaderboard runs (CARLA coords).
    deviations = [
        ("run1 deviation (1.85%)", -78.711, 122.37),
        ("run2 deviation (4.62%)", -149.444, 18.719),
    ]

    fig, ax = plt.subplots(figsize=(11, 13))

    # Road network (lanelet boundaries) as light gray.
    for i, pl in enumerate(lines):
        xs = [p[0] for p in pl]
        ys = [p[1] for p in pl]
        ax.plot(xs, ys, color="0.78", linewidth=0.5,
                label="Lanelet map" if i == 0 else None, zorder=1)

    # Route polyline + numbered waypoints.
    ax.plot(rx, ry, color="crimson", linewidth=2.2, label="Route", zorder=3)
    ax.scatter(rx, ry, color="crimson", s=28, zorder=4)
    for i, (x, y) in enumerate(wps):
        ax.annotate(f"{i}", (x, y), textcoords="offset points", xytext=(5, 4),
                    fontsize=8, color="darkred", zorder=5)

    # Start (green) and end (blue).
    ax.scatter([rx[0]], [ry[0]], color="green", s=140, marker="o",
               edgecolors="black", label="Start (wp0)", zorder=6)
    ax.scatter([rx[-1]], [ry[-1]], color="royalblue", s=140, marker="s",
               edgecolors="black", label="Goal (wp%d)" % (len(wps) - 1), zorder=6)

    # Deviation points (orange X).
    for j, (lbl, x, y) in enumerate(deviations):
        ax.scatter([x], [y], color="orange", s=200, marker="X",
                   edgecolors="black", linewidths=1.2,
                   label="Deviation point" if j == 0 else None, zorder=7)
        ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(8, -12),
                    fontsize=9, color="darkorange", weight="bold", zorder=8)

    ax.set_aspect("equal")
    ax.set_xlabel("x [m]  (CARLA / map frame)")
    ax.set_ylabel("y [m]")
    ax.set_title("Town07 perimeter route over lanelet2 map")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.4)

    fig.tight_layout()
    fig.savefig(args.out, dpi=130)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
