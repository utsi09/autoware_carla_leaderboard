#!/usr/bin/env python3
"""fig_dualchannel_arch_en.png — dual-channel architecture (English).
0827: Decision stage gains an en-route re-evaluation row (rear-occupancy /
stall watchdogs -> demote & re-select -> DEFER fallback); hard-fail fast-path
arrow rerouted orthogonally (no diagonals); overall tidy-up."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
})

W, H = 1850, 1080
fig = plt.figure(figsize=(W/100, H/100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

INK = "#1c1c28"
GRAY = "#9aa3b2"
GREEN = "#e4efdc"
ORANGE = "#f9e6c3"
LIGHT = "#f3f5f9"
OLIVE = "#8a7414"

def T(y):  # top-based y -> mpl y
    return H - y

def rbox(x, y_top, w, h, fc="white", ec=INK, lw=2.0, r=14, ls="-"):
    ax.add_patch(FancyBboxPatch((x, T(y_top) - h), w, h,
                 boxstyle=f"round,pad=0,rounding_size={r}",
                 fc=fc, ec=ec, lw=lw, linestyle=ls, mutation_aspect=1))

def txt(x, y_top, s, size=13, weight="normal", color=INK, ha="center", va="center"):
    ax.text(x, T(y_top), s, fontsize=size * 1.10, fontweight=weight, color=color,
            ha=ha, va=va, linespacing=1.35)

def arr(p0, p1, color=INK, lw=2.0, ms=18, ls="-"):
    ax.add_patch(FancyArrowPatch((p0[0], T(p0[1])), (p1[0], T(p1[1])),
                 arrowstyle="-|>", mutation_scale=ms, color=color, lw=lw,
                 linestyle=ls))

# ---------------- left panel: nominal channel ----------------
rbox(45, 95, 1065, 570, fc="white", lw=2.4, r=18)
txt(577, 130, "Nominal Driving Channel  (Autoware 0.39.0 — unmodified)", 20, "bold")

# Perception & Localization group
rbox(75, 220, 488, 340, fc=LIGHT, lw=1.8)
txt(319, 258, "Perception & Localization", 17, "bold")
rbox(90, 338, 150, 167); rbox(248, 338, 150, 167); rbox(406, 338, 150, 167)
txt(165, 400, "Sensors", 14, "bold")
txt(165, 445, "LiDAR·cam\nGNSS·IMU", 11.5, color="#444455")
txt(323, 421, "Perception", 13, "bold")
txt(481, 405, "Localization", 13, "bold")
txt(481, 445, "EKF", 11.5, color="#444455")
for x0 in (240, 398):
    arr((x0, 421), (x0 + 10, 421), ms=18, lw=2)

# Planning group
rbox(570, 220, 335, 340, fc=LIGHT, lw=1.8)
txt(737, 258, "Planning", 17, "bold")
rbox(584, 338, 99, 167); rbox(690, 338, 99, 167); rbox(796, 338, 99, 167)
txt(633, 421, "Mission", 12.5, "bold")
txt(739, 421, "Behavior", 12.5, "bold")
txt(845, 421, "Motion", 12.5, "bold")
for x0 in (683, 789):
    arr((x0, 421), (x0 + 8, 421), ms=15, lw=2)
arr((563, 421), (585, 421), ms=18, lw=2)

# Control group
rbox(910, 220, 172, 340, fc=LIGHT, lw=1.8)
txt(996, 258, "Control", 17, "bold")
rbox(925, 338, 142, 167)
txt(996, 400, "Vehicle\ncontrol", 14, "bold")
txt(996, 460, "+ stock\nMRM", 11.5, color="#444455")
arr((905, 421), (926, 421), ms=18, lw=2)

# ---------------- right panel: fail-safe channel ----------------
rbox(1140, 95, 670, 920, fc="white", lw=2.4, r=18)
txt(1475, 130, "Fail-Safe Channel  (proposed add-on)", 20, "bold")

# Monitoring
rbox(1165, 160, 620, 235, fc=GREEN, lw=1.8)
txt(1475, 190, "Monitoring — CDR Monitor (10 Hz)", 16, "bold")
rbox(1188, 220, 282, 62); rbox(1480, 220, 282, 62)
txt(1329, 251, "sensor health checks", 12.5)
txt(1621, 251, "capability scores", 12.5)
arr((1470, 251), (1481, 251), ms=16, lw=2)
rbox(1188, 305, 574, 62, fc=ORANGE)
txt(1475, 336, "dead-sensor fast check", 12.5)

# Monitoring -> Decision
arr((1475, 395), (1475, 418), ms=22, lw=2.6)

# Decision (3 rows: threshold+search / selection / en-route re-evaluation)
rbox(1165, 420, 620, 330, fc=GREEN, lw=1.8)
txt(1475, 450, "Decision — MRM Supervisor", 16, "bold")
rbox(1188, 480, 282, 62); rbox(1480, 480, 282, 62)
txt(1329, 511, "dual-threshold check", 12.5)
txt(1621, 511, "refuge candidate search", 12.5)
arr((1470, 511), (1481, 511), ms=16, lw=2)
rbox(1188, 565, 574, 76)
txt(1475, 588, "MRM selection", 13.5, "bold")
txt(1475, 619, "MOVE (evacuate)  /  DEFER (delegate stop)", 12.5)
rbox(1188, 658, 574, 76)
txt(1475, 681, "en-route re-evaluation", 13.5, "bold")
txt(1475, 712, "rear occupancy · stall watchdogs → demote / re-select → DEFER",
    11.5)
arr((1475, 641), (1475, 657), ms=16, lw=2)

# Decision -> MRC
arr((1475, 750), (1475, 780), ms=22, lw=2.6)

# MRC
rbox(1165, 783, 620, 205, fc=LIGHT, lw=1.8)
txt(1475, 813, "Minimal-Risk Condition (MRC)", 16, "bold")
rbox(1188, 840, 282, 122); rbox(1480, 840, 282, 122)
txt(1329, 877, "Shoulder /\nparking-lot stop", 13, "bold")
txt(1329, 932, "off active lane", 11, color="#444455")
txt(1621, 882, "In-lane stop", 13, "bold")
txt(1621, 932, "stock Autoware MRM", 11, color="#444455")

# ---------------- hard-fail fast path ----------------
rbox(75, 705, 850, 120, fc=ORANGE, lw=2.2)
txt(500, 740, "Hard-fail fast path (dead sensor)", 15.5, "bold")
txt(500, 787, "sensor silence → immediate MRM, no debounce", 12.5)

# ---------------- inter-channel arrows ----------------
# sensor topics tap (dashed gray, over the top)
ax.plot([175, 175, 1192, 1192], [T(95), T(52), T(52), T(80)],
        color=GRAY, lw=2, ls=(0, (5, 4)))
arr((1192, 80), (1192, 158), color=GRAY, lw=2, ms=20, ls=(0, (5, 4)))
txt(730, 40, "sensor topics (read-only tap)", 13, color="#6d7688")

# MOVE: MRM selection -> Planning & Control (solid, orthogonal)
ax.plot([1188, 665], [T(628), T(628)], color=INK, lw=2.2)
arr((665, 628), (665, 563), lw=2.2, ms=20)
ax.plot([995, 995], [T(628), T(600)], color=INK, lw=2.2)
arr((995, 600), (995, 563), lw=2.2, ms=20)
txt(830, 601, "MOVE: reroute (AD API) · speed cap", 11.5)

# hard-fail -> MRM selection (dashed olive, orthogonal elbows)
ax.plot([925, 1125, 1125], [T(765), T(765), T(602)],
        color=OLIVE, lw=2, ls=(0, (5, 4)))
arr((1125, 602), (1186, 602), color=OLIVE, lw=2, ms=18, ls=(0, (5, 4)))

# DEFER: in-lane stop -> stock MRM (dashed black, along the bottom)
ax.plot([1621, 1621, 1010, 1010], [T(962), T(1035), T(1035), T(640)],
        color=INK, lw=1.8, ls=(0, (6, 4)))
arr((1010, 640), (1010, 563), lw=1.8, ms=18, ls=(0, (6, 4)))
txt(1300, 1058, "DEFER: diagnostic ERROR → stock in-lane stop MRM", 13)

fig.savefig("/home/taewook/autoware_carla_leaderboard/doc/figs/en/fig_dualchannel_arch_en.png",
            bbox_inches="tight", pad_inches=0.15, facecolor="white")
import shutil
shutil.copy("/home/taewook/autoware_carla_leaderboard/doc/figs/en/fig_dualchannel_arch_en.png",
            "/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig2b_dualchannel.png")
print("saved + staged")
