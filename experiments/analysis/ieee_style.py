# IEEE T-ITS/TIV 계열 논문 그림 공통 스타일 (v19+ 전 그림 적용)
# 원칙: 세리프(Times/STIX), 절제된 색, 그림 내 제목 없음(캡션이 설명),
# 가는 검정 축, 옅은 격자, (a)(b) 패널 라벨, 회색조 인쇄에도 판독 가능.
import matplotlib
from matplotlib import font_manager

# 한글 세리프: 나눔명조 에코 (라틴/숫자는 STIX가 선점)
for f in ("/usr/share/fonts/truetype/nanum/NanumMyeongjoEcoR.ttf",
          "/usr/share/fonts/truetype/nanum/NanumSquare_acR.ttf"):
    try:
        font_manager.fontManager.addfont(f)
    except Exception:
        pass

matplotlib.rcParams.update({
    # matplotlib 3.5는 글리프 단위 폴백이 없어 한글 폰트를 첫 순위로 둔다
    # (나눔명조 에코의 라틴 글리프도 세리프 — 수식은 mathtext STIX가 담당)
    "font.family": ["NanumMyeongjo Eco", "STIXGeneral"],
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "grid.linewidth": 0.4, "lines.linewidth": 1.0,
    "grid.alpha": 0.25, "legend.frameon": False,
    "figure.dpi": 200, "savefig.dpi": 300, "savefig.bbox": "tight",
})

# 절제된 팔레트 (경로 강조는 RED 단색, 보조는 무채색 계열)
RED   = "#c0392b"   # 경로/강조
BLUE  = "#2c5f8a"   # 보조 계열 1
GRAY  = "#666666"   # 보조 계열 2
LGRAY = "#bbbbbb"   # 배경 요소

def panel_label(ax, s, x=0.02, y=0.97):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=9, fontweight="bold",
            va="top", ha="left")

def clean_axes(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
