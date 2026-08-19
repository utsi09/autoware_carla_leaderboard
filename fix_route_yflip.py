#!/usr/bin/env python3
"""Fix routes authored from lanelet2 local coords (JOSM) for the CARLA leaderboard.

lanelet2 'local_y' == -(CARLA y).  Routes that used local_y directly have every
y sign wrong, so the ego spawns off-route. This negates y on all <position> and
<trigger_point> elements (x kept, yaw negated). Writes <name>_fixed.xml.
"""
import sys
import re

src = sys.argv[1] if len(sys.argv) > 1 else "resources/routes/town07_perimeter.xml"
dst = src.replace(".xml", "_fixed.xml")

text = open(src).read()


def neg_y(m):
    return f'y="{-float(m.group(1)):.4f}"'


def neg_yaw(m):
    return f'yaw="{(-float(m.group(1))) % 360:.4f}"'


text = re.sub(r'y="(-?[\d.]+)"', neg_y, text)
text = re.sub(r'yaw="(-?[\d.]+)"', neg_yaw, text)

open(dst, "w").write(text)
print("wrote", dst)
