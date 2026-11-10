import csv, glob, os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
for p in ["/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"]:
    try: font_manager.fontManager.addfont(p)
    except Exception: pass
plt.rcParams["font.family"] = "NanumBarunGothic"; plt.rcParams["axes.unicode_minus"] = False
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, SURF, GRID, LIGHT = "#0b0b0b", "#52514e", "#fcfcfb", "#e6e4df", "#d9d7d2"
SC = f"{RES}/derived"   # cam_scores.csv, gb_loc.csv (bag 추출 파생표)

rows = [r for r in csv.DictReader(open(f"{SC}/health_rows.csv")) if r["S_lidar"] not in ("", "nan") and float(r["S_lidar"]) < 0.95]
R = np.array([float(r["R"]) for r in rows]); q = np.array([float(r["S_lidar"]) for r in rows])
h = np.array([float(r["S_perc"]) for r in rows]); ob = np.array([float(r["S_obs"]) for r in rows])
src = np.array([r["key"] == "ladder" for r in rows])
levels = sorted(set(R)); med = {k: [np.median(v[R == L]) for L in levels] for k, v in [("q", q), ("h", h), ("ob", ob)]}
print("n runs", len(rows), "levels", levels, {k: np.round(v, 3).tolist() for k, v in med.items()})

def cross(y, thr):  # R where median series crosses thr (log-linear interpolation)
    lx = np.log10(levels); y = np.array(y)
    for i in range(len(y) - 1):
        if (y[i] - thr) * (y[i + 1] - thr) <= 0:
            return 10 ** (lx[i] + (thr - y[i]) / (y[i + 1] - y[i]) * (lx[i + 1] - lx[i]))
    return np.nan
R_band = cross(med["h"], 0.7); R_floor = cross(med["ob"], 0.4)
print("R at health 0.7:", round(R_band, 2), " R at obstacle 0.4:", round(R_floor, 2))

fig = plt.figure(figsize=(14, 11), facecolor=SURF)
gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.28, left=0.07, right=0.975, top=0.88, bottom=0.19)
fig.suptitle("열화 세기 R (등가 시정) → 라이다 품질 q → 인지 건강도 → MRM 판단", x=0.07, ha="left", fontsize=16, color=INK, weight="bold")
fig.text(0.07, 0.915, f"사다리 28런(rep 40–43, MRM off) + 재튜닝 A·B {int((~src).sum())}런(ours·baseline, MRM on). 점수는 주입 후 중앙값. "
         "감독기 규칙: 건강도 < 0.7 이 10틱 → 띠 진입(MRM 검토), 장애물 인지 < 0.4 이면 이동 보류(차선 내 정지).", fontsize=10.2, color=INK2)

# ---------- A: scores vs R ----------
ax = fig.add_subplot(gs[0, 0]); ax.set_xscale("log")
rng = np.random.default_rng(1)
for arr, col, name in [(q, BLUE, "라이다 품질 q"), (h, ORANGE, "인지 건강도"), (ob, AQUA, "장애물 인지")]:
    jit = R * (1 + rng.uniform(-0.06, 0.06, len(R)))
    ax.scatter(jit[~src], arr[~src], s=9, color=col, alpha=0.25, linewidths=0, zorder=2)
    ax.scatter(R[src], arr[src], s=26, color=col, edgecolor=SURF, linewidths=0.8, zorder=3)
    ax.plot(levels, med["q" if col == BLUE else "h" if col == ORANGE else "ob"], color=col, lw=2, zorder=4)
    ax.text(43, med["q" if col == BLUE else "h" if col == ORANGE else "ob"][-1], name, color=col, fontsize=9.5, va="center", ha="left")
ax.axhline(0.7, color=ORANGE, lw=1, ls="--", alpha=0.8); ax.text(19, 0.712, "띠 진입 문턱 0.7 (건강도)", color=ORANGE, fontsize=8.8, va="bottom")
ax.axhline(0.4, color=AQUA, lw=1, ls="--", alpha=0.8); ax.text(0.82, 0.412, "이동 하한 0.4 (장애물 인지)", color=AQUA, fontsize=8.8, va="bottom")
ax.axvline(R_band, color=INK2, lw=0.8, ls=":"); ax.axvline(R_floor, color=INK2, lw=0.8, ls=":")
for x0, x1, t in [(0.8, R_band, "주행 유지"), (R_band, R_floor, "갓길 대피"), (R_floor, 60, "차선 내 정지")]:
    ax.text(10 ** ((np.log10(x0) + np.log10(x1)) / 2), 0.08, t, ha="center", fontsize=9.5, color=INK, weight="bold")
ax.text(R_band, 0.995, f"{R_band:.1f}", ha="center", va="top", fontsize=8.5, color=INK2)
ax.text(R_floor, 0.995, f"{R_floor:.0f}", ha="center", va="top", fontsize=8.5, color=INK2)
ax.set_xlim(0.8, 70); ax.set_ylim(0, 1.0); ax.set_xticks(levels); ax.set_xticklabels([f"R={int(L)}\n{3/(0.01*L**0.6):.0f} m" for L in levels]); ax.minorticks_off()
ax.set_xlabel("Goodin 열화 파라미터 R (위) · 등가 시정 MOR = 3/α, α = 0.01·R^0.6 (아래)", color=INK2, fontsize=10); ax.set_ylabel("점수 (0–1)", color=INK2, fontsize=10)
ax.set_title("A. 열화 세기에 따른 세 점수와 판단 구간", loc="left", fontsize=12.5, color=INK, pad=10)
ax.tick_params(colors=INK2, labelsize=9.5); ax.set_facecolor(SURF)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
for s in ["left", "bottom"]: ax.spines[s].set_color(GRID)
ax.grid(axis="y", color=GRID, lw=0.6)

# ---------- B: health vs q ----------
ax = fig.add_subplot(gs[0, 1])
ax.scatter(q[~src], h[~src], s=10, color=ORANGE, alpha=0.3, linewidths=0, zorder=2)
ax.scatter(q[src], h[src], s=30, color=ORANGE, edgecolor=SURF, linewidths=0.8, zorder=3)
for L, qq, hh in zip(levels, med["q"], med["h"]):
    ax.annotate(f"R={int(L)} ({3/(0.01*L**0.6):.0f} m)", (qq, hh), xytext=(6, -12), textcoords="offset points", fontsize=8.8, color=INK2)
ax.axhline(0.7, color=ORANGE, lw=1, ls="--", alpha=0.8)
qb = np.interp(0.7, med["h"][::-1], med["q"][::-1]); Rq = 7.6 * 10 ** ((0.5 - qb) / 0.414187)
ax.axvline(qb, color=INK2, lw=0.8, ls=":")
ax.text(qb + 0.01, 0.30, f"건강도 0.7 ↔ q ≈ {qb:.2f}\n모니터 식으로 R ≈ {Rq:.1f} (시정 ≈ {3/(0.01*Rq**0.6):.0f} m)\n(설계 경계 q 0.5 ↔ R 7.6, 시정 ≈ 89 m)", fontsize=9, color=INK)
ax.axvspan(0.5, 1.0, color=GRID, alpha=0.45, lw=0); ax.axvspan(0.4, 0.5, color=LIGHT, alpha=0.45, lw=0); ax.axvspan(0.0, 0.4, color="#c9c6bf", alpha=0.45, lw=0)
for x, t in [(0.75, "q 등급: 주행 유지"), (0.45, "대피"), (0.2, "정지")]:
    ax.text(x, 0.975, t, ha="center", va="top", fontsize=8.8, color=INK2, bbox=dict(facecolor=SURF, edgecolor="none", pad=1.5))
ax.set_xlim(0.1, 1.0); ax.set_ylim(0.25, 1.0)
ax.set_xlabel("라이다 품질 q (주입 후 중앙값)", color=INK2, fontsize=10); ax.set_ylabel("인지 건강도 (융합)", color=INK2, fontsize=10)
ax.set_title("B. 건강도 = f(q) — 융합이 q를 희석해 경계가 R 7.6 → 약 10 (시정 89 → 77 m)", loc="left", fontsize=12.5, color=INK, pad=10)
ax.tick_params(colors=INK2, labelsize=9.5); ax.set_facecolor(SURF)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
for s in ["left", "bottom"]: ax.spines[s].set_color(GRID)

# ---------- C: health(t) ladder ----------
ax = fig.add_subplot(gs[1, 0])
ramp = ["#c9dcf5", "#a3c3ee", "#7daae6", "#5591de", "#2a78d6", "#1d5aa6", "#123d74"]
lad = sorted(glob.glob(f"{SC}/series/stock-lcl-*-r40-*.npz"), key=lambda p: float(os.path.basename(p).split("-")[2].split("_")[0]))
for col, p in zip(ramp, lad):
    z = np.load(p); Rv = float(os.path.basename(p).split("-")[2].split("_")[0]); tf = float(z["t_fault"])
    t = z["perc"][:, 0] - tf; y = z["perc"][:, 1].copy(); y[y < 0.05] = np.nan; m = (t >= -10) & (t <= 120)
    ax.plot(t[m], y[m], color=col, lw=1.6)
    ax.text(121, np.median(y[(t > 60) & (t <= 120)]), f"{int(Rv)}", color=col, fontsize=9, va="center")
ax.text(126, 0.95, "R", color=INK2, fontsize=8.5, va="center")
ax.axhline(0.7, color=ORANGE, lw=1, ls="--", alpha=0.8); ax.axvline(0, color=INK2, lw=0.8, ls=":")
ax.text(1.5, 0.995, "주입", color=INK2, fontsize=8.8, va="top")
ax.set_xlim(-10, 135); ax.set_ylim(0.4, 1.0)
ax.set_xlabel("주입 후 시간 (s)", color=INK2, fontsize=10); ax.set_ylabel("인지 건강도", color=INK2, fontsize=10)
ax.set_title("C. 건강도 시계열 — 사다리 rep 40, 7단계 (MRM off)", loc="left", fontsize=12.5, color=INK, pad=10)
ax.tick_params(colors=INK2, labelsize=9.5); ax.set_facecolor(SURF)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
for s in ["left", "bottom"]: ax.spines[s].set_color(GRID)
ax.grid(axis="y", color=GRID, lw=0.6)

# ---------- D: the two 5 mm/h band entries ----------
ax = fig.add_subplot(gs[1, 1])
pairs = [("lcl-mid-agg-r22-1109_0620", "lcl-mid-agg-r22-1109_0626", "agg r22"), ("lcl-mid-none-r25-1109_0745", "lcl-mid-none-r25-1109_0750", "none r25")]
diag = []
for i, (ours, base, lbl) in enumerate(pairs):
    for tag, col, ls, nm in [(ours, BLUE, "-", "ours"), (base, ORANGE, "-", "baseline")]:
        z = np.load(f"{SC}/series/{tag}.npz"); tf = float(z["t_fault"])
        t = z["perc"][:, 0] - tf; y = z["perc"][:, 1].copy(); y[y < 0.05] = np.nan  # 1–2틱 0 결측은 가림
        m = (t >= -5) & (t <= 150)
        ax.plot(t[m], y[m], color=col, lw=1.4, alpha=0.95 if i == 0 else 0.55, label=f"{nm} ({lbl})")
        if nm == "baseline":
            below = np.nan_to_num(y, nan=1.0) < 0.7; j = None
            for k in range(len(y) - 10):
                if t[k] > 2 and below[k:k + 10].all(): j = k + 9; break
            if j is not None:
                qq = np.interp(t[j], z["qlid"][:, 0] - tf, z["qlid"][:, 1]); oo = np.interp(t[j], z["obs"][:, 0] - tf, z["obs"][:, 1])
                diag.append((lbl, round(t[j], 1), round(float(np.nanmin(y[j-9:j+1])), 3), round(qq, 3), round(oo, 3)))
                ax.annotate(f"{lbl}: 띠 진입 {np.nanmedian(y[j-9:j+1]):.2f} @ +{t[j]:.0f} s", (t[j], y[j]), xytext=(0.06, 0.17 - 0.09 * i), textcoords="axes fraction", fontsize=8.8, color=ORANGE, arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.7, alpha=0.7))
ax.axhline(0.7, color=ORANGE, lw=1, ls="--", alpha=0.8); ax.axvline(0, color=INK2, lw=0.8, ls=":")
ax.set_xlim(-5, 150); ax.set_ylim(0.6, 1.0)
ax.set_xlabel("주입 후 시간 (s)", color=INK2, fontsize=10); ax.set_ylabel("인지 건강도", color=INK2, fontsize=10)
ax.set_title("D. 중강도(R=5) 경계 사례 2건 — baseline 띠 진입 vs 짝 ours", loc="left", fontsize=12.5, color=INK, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.8, ncol=2)
ax.tick_params(colors=INK2, labelsize=9.5); ax.set_facecolor(SURF)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
for s in ["left", "bottom"]: ax.spines[s].set_color(GRID)
ax.grid(axis="y", color=GRID, lw=0.6)
print("band-entry diag (label, t, health, q, obs):", diag)

fig.text(0.07, 0.108, "읽는 법: 세기 모델은 q로 R을 ±0.3 이내로 되살리고(앞 그림 B), 감독기는 q가 아니라 융합 건강도(라이다·카메라·장애물 인지의 결합)로 판단한다."
         , fontsize=9, color=INK2)
fig.text(0.07, 0.086, "시정은 WMO MOR(대비 5 %) = 3/α 로 환산한 '안개 수준의 감쇠' 등가값이며 클러터·거리오차는 포함하지 않는다(Hahner ICCV 2021 의 α 0.03/0.06 ↔ 100/50 m 와 같은 환산).", fontsize=9, color=INK2)
fig.text(0.07, 0.064, "중강도 R=5(시정 ≈110 m)는 건강도 0.77 로 문턱 0.7 위 0.07 여유 → 84/86 주행 유지. 2건은 카메라 품질이 0.97→0.77 로 내려가는 구간(신호등 인식 저하)과 겹쳐 0.68 로 띠 진입(D). 짝 ours 는 같은 구간을 0.70 위로 지남.", fontsize=9, color=INK2)
fig.text(0.07, 0.042, "R=10(시정 ≈75 m)은 건강도 0.70 으로 정확히 경계(사다리 C 블록에서 갓길 대피 확인 예정). 고강도 R=25(시정 ≈45 m)는 0.58, 장애물 인지 0.33 < 0.4 → 이동 보류 → 두 방법 모두 차선 내 정지.", fontsize=9, color=INK2)
fig.text(0.07, 0.020, "시간축은 시뮬 시간. C 의 주입 전 하강은 출발 직후 장면 변화. D 의 1–2틱짜리 0 값(점수 토픽 순간 결측)은 가렸다. A·B 의 옅은 점은 재튜닝 A·B 런(R=5·25 만), 진한 점은 사다리. CARLA_DIED 런 제외.", fontsize=9, color=INK2)
out = "/home/taewook/autoware_carla_leaderboard/experiments/results/retune_ext/fig_health_vs_rain_1109.png"
fig.savefig(out, dpi=150, facecolor=SURF); print(out)
