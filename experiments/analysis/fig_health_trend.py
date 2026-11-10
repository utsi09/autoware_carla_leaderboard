import glob, os, re, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
for p in ["/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"]:
    try: font_manager.fontManager.addfont(p)
    except Exception: pass
plt.rcParams["font.family"] = "NanumBarunGothic"; plt.rcParams["axes.unicode_minus"] = False
ORANGE, ORANGE_L, BLUE = "#eb6834", "#f3a98a", "#2a78d6"
INK, INK2, SURF, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e6e4df"
SC = "/home/taewook/autoware_carla_leaderboard/experiments/results/derived/series"
BAND, FLOOR, TICKS = 0.7, 0.3, 10

def load(tag):
    z = np.load(f"{SC}/{tag}.npz"); tf = float(z["t_fault"])
    t = z["perc"][:, 0] - tf; y = z["perc"][:, 1].copy(); y[y < 0.05] = np.nan
    return t, y
def band_entry(t, y):
    below = np.nan_to_num(y, nan=1.0) < BAND
    for k in range(len(y) - TICKS):
        if t[k] > 0.5 and below[k:k + TICKS].all(): return t[k + TICKS - 1]
    return None
def resample(t, y, grid):
    m = ~np.isnan(y); return np.interp(grid, t[m], y[m], left=np.nan, right=np.nan)
def mor(R): return 3 / (0.01 * R ** 0.6)

groups = []  # (title, tags, xmax)
for lv in [1, 2, 5, 10, 15, 25, 40]:
    tags = sorted(os.path.basename(p)[:-4] for p in glob.glob(f"{SC}/stock-lcl-{lv}_*-def-r4[0-3]-*.npz"))
    groups.append((f"사다리 R={lv} (시정 ≈{mor(lv):.0f} m), MRM off", tags, 120))
groups.append(("재튜닝 A 폐루프: R=5 (시정 ≈114 m), ours+baseline", sorted(os.path.basename(p)[:-4] for p in glob.glob(f"{SC}/lcl-mid-*-1109_*.npz")), 180))
groups.append(("재튜닝 B 폐루프: R=25 (시정 ≈43 m), ours+baseline", sorted(os.path.basename(p)[:-4] for p in glob.glob(f"{SC}/lcl-high-*-1109_*.npz")), 30))

fig, axes = plt.subplots(3, 3, figsize=(18, 11.5), facecolor=SURF)
fig.subplots_adjust(left=0.05, right=0.97, top=0.9, bottom=0.11, hspace=0.42, wspace=0.22)
fig.suptitle("열화 세기별 인지 건강도 추이 — 주입 시각 기준, 개별 런(얇은 선)과 중앙값(굵은 선)", x=0.05, ha="left", fontsize=16, color=INK, weight="bold")
fig.text(0.05, 0.925, "감독기 규칙: 건강도 < 0.7 이 10틱(1 s) 지속 → 띠 진입(MRM 검토). 삼각형 = 런별 띠 진입 시각. 1–2틱 0 값(점수 토픽 순간 결측)은 가림.", fontsize=10.5, color=INK2)
summary = []
for ax, (title, tags, xmax) in zip(axes.flat, groups):
    grid = np.arange(-10, xmax, 0.2); Y = []; entries = []
    for tag in tags:
        t, y = load(tag); m = (t >= -10) & (t <= xmax)
        ax.plot(t[m], y[m], color=ORANGE_L, lw=0.7, alpha=0.6 if len(tags) > 10 else 0.9)
        Y.append(resample(t, y, grid)); e = band_entry(t, y); entries.append(e)
    if Y:
        med = np.nanmedian(np.array(Y), axis=0); ax.plot(grid, med, color=ORANGE, lw=2.4)
    n_e = sum(e is not None for e in entries)
    for e in entries:
        if e is not None and e <= xmax: ax.plot(e, 0.04, marker="^", color=BLUE, ms=7, clip_on=False)
    ax.axhline(BAND, color=INK, lw=1, ls="--", alpha=0.7); ax.axhline(FLOOR, color=INK, lw=1, ls=":", alpha=0.7)
    ax.axvline(0, color=INK2, lw=0.8, alpha=0.6)
    ax.text(1.005, BAND, "경보 띠\n0.7", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=8, color=INK2)
    ax.text(1.005, FLOOR, "바닥\n0.3", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=8, color=INK2)
    post = np.array(Y)[:, grid > 10] if Y else np.array([[np.nan]])
    med_post = np.nanmedian(post); 
    etxt = f"띠 진입 {n_e}/{len(tags)}" + (f", 중앙 {np.median([e for e in entries if e is not None]):.1f} s" if n_e else "")
    ax.text(0.03, 0.22, f"{etxt}\n주입 후 건강도 중앙값 {med_post:.2f}", transform=ax.transAxes, va="top", fontsize=10, color=INK, weight="bold")
    ax.set_title(title, loc="left", fontsize=11.5, color=INK, pad=8)
    ax.set_xlim(-10, xmax); ax.set_ylim(0, 1.0); ax.set_facecolor(SURF)
    ax.tick_params(colors=INK2, labelsize=9); ax.grid(axis="y", color=GRID, lw=0.6)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color(GRID)
    summary.append((title, len(tags), n_e, round(float(med_post), 3)))
for ax in axes[-1]: ax.set_xlabel("고장 주입 기준 시간 (시뮬 s; 세로선 = 주입 시각)", color=INK2, fontsize=10)
for ax in axes[:, 0]: ax.set_ylabel("인지 건강도", color=INK2, fontsize=10)
fig.legend(handles=[Line2D([], [], color=ORANGE_L, lw=1, label="개별 런"), Line2D([], [], color=ORANGE, lw=2.4, label="중앙값"),
                    Line2D([], [], marker="^", color=BLUE, lw=0, ms=7, label="띠 진입 시각")],
           loc="upper right", bbox_to_anchor=(0.985, 0.965), ncol=3, frameon=False, fontsize=10)
fig.text(0.05, 0.052, "자료: 사다리 rep 40–43(각 4런, MRM off, 주입 후 120 s), 재튜닝 A(R=5, 86런)·B(R=25, 45런; 러너 분석에서 주입 시각 정렬이 실패한 16런 제외) — ours·baseline 합산(같은 모니터라 건강도 분포 동일). B 는 주입 ≈15 s 뒤 차선 내 정지로 런이 끝나 창이 짧다.",
         fontsize=9.2, color=INK2)
fig.text(0.05, 0.033, "R=1 의 삼각형 3개는 정상 상태가 아니라 주입 직후 1~2 s 과도 하강(세기 경로가 켜지기 전 기존 품질식 구간)이다. 모든 패널의 0 s 직후 뾰족한 하강이 같은 현상이며, R≥5 에서는 1 s 안에 끝나 띠 진입으로 안 잡힌다.", fontsize=9.2, color=INK2)
fig.text(0.05, 0.014, "시정 = WMO MOR(대비 5 %) = 3/α, α = 0.01·R^0.6 — 감쇠 기준 등가값. 주입 전 하강(사다리)은 출발 직후 장면 변화.", fontsize=9.2, color=INK2)
out = "/home/taewook/autoware_carla_leaderboard/experiments/results/retune_ext/fig_health_trend_1109.png"
fig.savefig(out, dpi=150, facecolor=SURF)
for s in summary: print(s)
print(out)
