#!/usr/bin/env python3
"""fig_dualchannel_arch_en.png — dual-channel architecture (English).
Regenerated 0826: no mid-word hyphenation (Perception/Localization/Mission/Behavior/Motion on one line)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
})

W, H = 1850, 990
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
    ax.add_patch(FancyArrowPatch((x0, T(421)), (x0 + 10, T(421)),
                 arrowstyle="-|>", mutation_scale=18, color=INK, lw=2))

# Planning group
rbox(570, 220, 335, 340, fc=LIGHT, lw=1.8)
txt(737, 258, "Planning", 17, "bold")
rbox(584, 338, 99, 167); rbox(690, 338, 99, 167); rbox(796, 338, 99, 167)
txt(633, 421, "Mission", 12.5, "bold")
txt(739, 421, "Behavior", 12.5, "bold")
txt(845, 421, "Motion", 12.5, "bold")
for x0 in (683, 789):
    ax.add_patch(FancyArrowPatch((x0, T(421)), (x0 + 8, T(421)),
                 arrowstyle="-|>", mutation_scale=15, color=INK, lw=2))
ax.add_patch(FancyArrowPatch((563, T(421)), (585, T(421)),
             arrowstyle="-|>", mutation_scale=18, color=INK, lw=2))

# Control group
rbox(910, 220, 172, 340, fc=LIGHT, lw=1.8)
txt(996, 258, "Control", 17, "bold")
rbox(925, 338, 142, 167)
txt(996, 400, "Vehicle\ncontrol", 14, "bold")
txt(996, 460, "+ stock\nMRM", 11.5, color="#444455")
ax.add_patch(FancyArrowPatch((905, T(421)), (926, T(421)),
             arrowstyle="-|>", mutation_scale=18, color=INK, lw=2))

# ---------------- right panel: fail-safe channel ----------------
rbox(1140, 95, 670, 840, fc="white", lw=2.4, r=18)
txt(1475, 130, "Fail-Safe Channel  (proposed add-on)", 20, "bold")

# Monitoring
rbox(1165, 160, 620, 235, fc=GREEN, lw=1.8)
txt(1475, 188, "Monitoring — cdr_monitor (BT, 10 Hz)", 16, "bold")
rbox(1188, 215, 282, 88); rbox(1480, 215, 282, 88)
txt(1329, 259, "Freshness · quality\n· physics checks", 12.5)
txt(1621, 259, "Sector → capability\nhealth scores", 12.5)
ax.add_patch(FancyArrowPatch((1470, T(259)), (1481, T(259)),
             arrowstyle="-|>", mutation_scale=16, color=INK, lw=2))
rbox(1188, 320, 574, 57, fc=ORANGE)
txt(1475, 348, "Dead-sensor fast check (freshness deadline)", 12.5)

# Monitoring -> Decision
ax.add_patch(FancyArrowPatch((1475, T(395)), (1475, T(418)),
             arrowstyle="-|>", mutation_scale=22, color=INK, lw=2.6))

# Decision
rbox(1165, 420, 620, 245, fc=GREEN, lw=1.8)
txt(1475, 448, "Decision — mrm_supervisor (state machine)", 16, "bold")
rbox(1188, 472, 282, 88); rbox(1480, 472, 282, 88)
txt(1329, 516, "Dual-threshold\ncheck ($\\theta_\\mathrm{H}$ / $\\theta_\\mathrm{L}$)", 12.5)
txt(1621, 516, "Refuge candidate\nsearch · cost fn.", 12.5)
ax.add_patch(FancyArrowPatch((1470, T(516)), (1481, T(516)),
             arrowstyle="-|>", mutation_scale=16, color=INK, lw=2))
rbox(1188, 577, 574, 72)
txt(1475, 598, "MRM selection", 13.5, "bold")
txt(1475, 628, "MOVE (evacuate) / DEFER (delegate stop)", 12.5, "bold")

# Decision -> MRC
ax.add_patch(FancyArrowPatch((1475, T(665)), (1475, T(700)),
             arrowstyle="-|>", mutation_scale=22, color=INK, lw=2.6))

# MRC
rbox(1165, 703, 620, 205, fc=LIGHT, lw=1.8)
txt(1475, 733, "Minimal-Risk Condition (MRC)", 17, "bold")
rbox(1188, 758, 282, 128); rbox(1480, 758, 282, 128)
txt(1329, 793, "Shoulder /\nparking-lot stop", 13, "bold")
txt(1329, 852, "off active lane\n(speed-capped)", 11, color="#444455")
txt(1621, 797, "In-lane stop", 13, "bold")
txt(1621, 850, "delegated via\ndiagnostic ERROR", 11, color="#444455")

# ---------------- hard-fail fast path ----------------
rbox(75, 705, 850, 155, fc=ORANGE, lw=2.2)
txt(500, 738, "Hard-fail fast path (dead sensor)", 15.5, "bold")
txt(500, 800, "freshness deadline exceeded → skip band debounce · recovery holds · retries;\n"
              "precomputed refuge candidates → detection-to-decision within the deadline", 12)
txt(90, 892, "$\\theta_\\mathrm{H}$: intervention-entry (upper) threshold · "
             "$\\theta_\\mathrm{L}$: minimum-capability (lower, floor) threshold", 12.5, ha="left")

# ---------------- inter-channel arrows ----------------
# sensor topics tap (dashed gray, over the top)
ax.plot([175, 175, 1192, 1192], [T(95), T(52), T(52), T(80)],
        color=GRAY, lw=2, ls=(0, (5, 4)))
ax.add_patch(FancyArrowPatch((1192, T(80)), (1192, T(158)),
             arrowstyle="-|>", mutation_scale=20, color=GRAY, lw=2, ls=(0, (5, 4))))
ax.add_patch(FancyArrowPatch((175, T(100)), (175, T(93)),
             arrowstyle="-|>", mutation_scale=18, color=GRAY, lw=0.1))
txt(730, 40, "sensor topics (read-only tap)", 13, color="#6d7688")

# MOVE: MRM selection -> Planning & Control (solid)
ax.plot([1188, 665], [T(630), T(630)], color=INK, lw=2.2)
ax.add_patch(FancyArrowPatch((665, T(630)), (665, T(563)),
             arrowstyle="-|>", mutation_scale=20, color=INK, lw=2.2))
ax.plot([995, 995], [T(630), T(600)], color=INK, lw=2.2)
ax.add_patch(FancyArrowPatch((995, T(600)), (995, T(563)),
             arrowstyle="-|>", mutation_scale=20, color=INK, lw=2.2))
txt(830, 603, "MOVE: reroute (AD API) · speed cap", 11.5)

# hard-fail -> MRM selection (dashed olive)
ax.add_patch(FancyArrowPatch((925, T(775)), (1186, T(640)),
             arrowstyle="-|>", mutation_scale=18, color=OLIVE, lw=2, ls=(0, (5, 4))))

# DEFER: in-lane stop -> stock MRM (dashed black, along the bottom)
ax.plot([1621, 1621, 1010, 1010], [T(886), T(950), T(950), T(640)],
        color=INK, lw=1.8, ls=(0, (6, 4)))
ax.add_patch(FancyArrowPatch((1010, T(640)), (1010, T(563)),
             arrowstyle="-|>", mutation_scale=18, color=INK, lw=1.8, ls=(0, (6, 4))))
txt(1300, 968, "DEFER: diagnostic ERROR → stock in-lane stop MRM", 13)

fig.savefig("/home/taewook/autoware_carla_leaderboard/doc/figs/en/fig_dualchannel_arch_en.png",
            bbox_inches="tight", pad_inches=0.15, facecolor="white")
print("saved")
