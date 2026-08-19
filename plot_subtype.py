#!/usr/bin/env python3
"""Plot lanelets of a specific subtype (e.g. road_shoulder) from a lanelet2 .osm map.

Usage:
    python3 plot_subtype.py <map.osm> [--subtype road_shoulder] [--out fig.png]
                            [--no-context] [--pdf]
"""
import argparse
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


def parse_osm(path):
    root = ET.parse(path).getroot()

    nodes = {}
    for n in root.findall("node"):
        tags = {t.get("k"): t.get("v") for t in n.findall("tag")}
        if "local_x" in tags and "local_y" in tags:
            xy = (float(tags["local_x"]), float(tags["local_y"]))
        else:
            xy = (float(n.get("lon")), float(n.get("lat")))
        nodes[n.get("id")] = xy

    ways = {}
    for w in root.findall("way"):
        ways[w.get("id")] = [nodes[nd.get("ref")] for nd in w.findall("nd")
                             if nd.get("ref") in nodes]

    lanelets = []
    for r in root.findall("relation"):
        tags = {t.get("k"): t.get("v") for t in r.findall("tag")}
        if tags.get("type") != "lanelet":
            continue
        left = right = None
        for m in r.findall("member"):
            if m.get("type") != "way":
                continue
            if m.get("role") == "left":
                left = ways.get(m.get("ref"))
            elif m.get("role") == "right":
                right = ways.get(m.get("ref"))
        if left and right:
            lanelets.append({"id": r.get("id"),
                             "subtype": tags.get("subtype", ""),
                             "left": left, "right": right})
    return lanelets


def lanelet_polygon(ll):
    return ll["left"] + ll["right"][::-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("osm")
    ap.add_argument("--subtype", default="road_shoulder")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-context", action="store_true",
                    help="hide non-matching lanelets")
    ap.add_argument("--pdf", action="store_true", help="also save a .pdf")
    args = ap.parse_args()

    lanelets = parse_osm(args.osm)
    matched = [ll for ll in lanelets if ll["subtype"] == args.subtype]
    others = [ll for ll in lanelets if ll["subtype"] != args.subtype]
    print(f"lanelets: {len(lanelets)} total, {len(matched)} subtype={args.subtype}")
    if not matched:
        subtypes = sorted({ll['subtype'] or '(none)' for ll in lanelets})
        print("available subtypes:", ", ".join(subtypes))
        return

    fig, ax = plt.subplots(figsize=(10, 10))
    if not args.no_context:
        for ll in others:
            ax.add_patch(MplPolygon(lanelet_polygon(ll), closed=True,
                                    facecolor="0.88", edgecolor="0.65",
                                    linewidth=0.3, zorder=1))
    for ll in matched:
        ax.add_patch(MplPolygon(lanelet_polygon(ll), closed=True,
                                facecolor="tab:orange", edgecolor="darkred",
                                linewidth=0.6, alpha=0.9, zorder=2))

    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(f"subtype: {args.subtype} ({len(matched)} lanelets)")

    out = args.out or f"{args.subtype}_map.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print("saved:", out)
    if args.pdf:
        pdf = out.rsplit(".", 1)[0] + ".pdf"
        fig.savefig(pdf, bbox_inches="tight")
        print("saved:", pdf)


if __name__ == "__main__":
    main()
