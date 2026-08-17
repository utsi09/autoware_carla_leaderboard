# -*- coding: utf-8 -*-
"""thesis v5 figure common style: Korean serif font + consistent visual language.

모든 논문 그림이 공유하는 시각 언어(선 굵기·서체·색)를 한 곳에서 정의한다.
한글 폰트는 나눔명조를 명시 등록한다(미등록 시 □ 렌더링 사고 이력).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

_FONTS = [
    '/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf',
    '/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf',
    '/usr/share/fonts/truetype/nanum/NanumMyeongjo-YetHangul.ttf',
]
for p in _FONTS:
    try:
        fm.fontManager.addfont(p)
    except Exception as e:
        print('font register failed:', p, e)

FONT = 'NanumMyeongjo'

# 색: 검증 팔레트(validate_palette.js ALL PASS) + 중립 잉크/보조색
INK = '#1f2430'          # 본문 잉크(스트로크·텍스트)
GRID = '#d5d8de'         # 보조선(recessive)
C_NF = '#2f6bb0'         # 무고장(청)
C_MID = '#d97a12'        # 중강도(주황)
C_HIGH = '#a50f15'       # 고강도(암적)
FILL_BLUE = '#dde7f2'    # 상자: 순정/파이프라인
FILL_GREEN = '#dcead8'   # 상자: 제안 계층(감시·대피)
FILL_RED = '#f4dcda'     # 상자: 정지/위임
FILL_GRAY = '#ececec'    # 상자: 중립/외부
FILL_AMBER = '#f6ead2'   # 상자: 상태/주의

LW_BOX = 1.3             # 상자 스트로크
LW_ARROW = 1.3           # 화살표
LW_LINE = 1.8            # 데이터 라인


def apply(rc_extra=None):
    plt.rcParams.update({
        'font.family': FONT,
        'font.size': 10,
        'axes.edgecolor': INK,
        'axes.labelcolor': INK,
        'axes.linewidth': 0.9,
        'text.color': INK,
        'xtick.color': INK,
        'ytick.color': INK,
        'axes.grid': True,
        'grid.color': GRID,
        'grid.linewidth': 0.6,
        'axes.axisbelow': True,
        'axes.unicode_minus': False,
        'figure.facecolor': 'white',
        'savefig.facecolor': 'white',
        'savefig.dpi': 220,
        'savefig.bbox': 'tight',
    })
    if rc_extra:
        plt.rcParams.update(rc_extra)
