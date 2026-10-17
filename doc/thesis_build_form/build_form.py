# -*- coding: utf-8 -*-
"""본심 양식(form.docx) 기반 영문 학위논문 빌더.
사용자의 양식 파일을 베이스로: 표지/인정서/섹션 구조는 그대로 두고,
안내문·예시 자리에 실제 내용(영문 v30 미러 + OMML 수식)을 채운다.
2-pass: build → pdf → map_form_pages.py → build (목차 쪽수)."""
import json, os, sys, copy
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree
import latex2mathml.converter, mathml2omml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from content_en1 import (TITLE_EN, ABSTRACT_EN, ABSTRACT_KEYWORDS,
                         SUMMARY_KO_TITLE, SUMMARY_KO, SUMMARY_KO_KEYWORDS, CH1, CH2)
from content_en2 import CH3, CH4
from content_en3 import CH5, CH6, CH7, REFS

FORM = os.path.join(HERE, 'form_base.docx')
OUT = '/home/taewook/autoware_carla_leaderboard/doc/thesis_bonsim_v1_0828.docx'
FONT = 'HY신명조'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

pagemap = {}
pm = os.path.join(HERE, 'pagemap_form.json')
if os.path.exists(pm):
    pagemap = json.load(open(pm))
keys = {}

KO_TITLE_L = ['자율주행 차량의 페일세이프 운행을 위한', '연속 센서 건강도 감시와',
              '위험·잔여능력 기반 단계적 최소위험기동 감독']
EN_TITLE_L = ['Continuous Sensor Health Monitoring and',
              'Risk/Capability-aware Graded MRM Supervision',
              'for Fail-Safe Operation of Autonomous Vehicles']

doc = Document(FORM)
body = doc.element.body
paras = doc.paragraphs

def styled(r, size=11, bold=False):
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    rPr = r._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rPr.insert(0, rf)
    rf.set(qn('w:eastAsia'), FONT)
    return r

def find_para(text, start=0):
    for i, p in enumerate(doc.paragraphs):
        if i >= start and text in p.text:
            return i, p
    raise KeyError(text)

def delete_p(p):
    p._element.getparent().remove(p._element)

# ---------------- 새 요소 생성 (문서 끝에 만들고 앵커 앞으로 이동) ----------------
def new_para(text='', size=11, bold=False, align=None, ls=1.45, fi=None,
             page_break=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = ls
    pf.space_before = Pt(0); pf.space_after = Pt(0)
    if align is not None: p.alignment = align
    if fi is not None: pf.first_line_indent = Pt(fi)
    if page_break:
        r = p.add_run(); r.add_break(WD_BREAK.PAGE)
    if text:
        styled(p.add_run(text), size=size, bold=bold)
    return p

def new_eq(latex, num):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.45
    pf.tab_stops.add_tab_stop(Cm(7.25), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Cm(14.5), WD_TAB_ALIGNMENT.RIGHT)
    styled(p.add_run('\t'), 11)
    mml = latex2mathml.converter.convert(latex)
    omml = mathml2omml.convert(mml).replace('<m:oMath>', f'<m:oMath xmlns:m="{M_NS}">', 1)
    p._p.append(etree.fromstring(omml))
    styled(p.add_run('\t' + num), 11)
    return p

def new_figure(caption, key, path, width_cm):
    out = []
    if path and os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Cm(width_cm or 14.5))
        out.append(p)
    cap = new_para(caption, size=11, bold=True, ls=1.3)
    cap.paragraph_format.keep_together = True
    out.append(cap)
    out.append(new_para(''))
    keys[key] = caption[:38]
    return out

def new_table(caption, key, rows, note):
    out = [new_para(caption, size=11, bold=True, ls=1.3)]
    out[0].paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = 'Table Grid'
    t.alignment = 1
    for ri, tr in enumerate(t.rows):
        trPr = tr._tr.get_or_add_trPr()
        trPr.append(OxmlElement('w:cantSplit'))
        if ri == 0:
            trPr.append(OxmlElement('w:tblHeader'))
    for ri, row in enumerate(rows):
        for ci, cell_text in enumerate(row):
            cell = t.cell(ri, ci); cell.text = ''
            first = True
            for line in str(cell_text).split('\n'):
                cp = cell.paragraphs[0] if first else cell.add_paragraph()
                first = False
                cp.paragraph_format.line_spacing = 1.2
                cp.paragraph_format.space_before = Pt(1)
                cp.paragraph_format.space_after = Pt(1)
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER if ri == 0 else WD_ALIGN_PARAGRAPH.LEFT
                styled(cp.add_run(line), size=9.0, bold=(ri == 0))
    out.append(t)
    if note:
        out.append(new_para(note, size=9.0, ls=1.3))
    out.append(new_para(''))
    keys[key] = caption[:38]
    return out

def render_chapter(blocks, first=False):
    out = []
    for b in blocks:
        kind = b[0]
        if kind == 'ch':
            keys[b[2]] = b[1]
            p = new_para('', ls=1.45)
            if not first:
                r = p.add_run(); r.add_break(WD_BREAK.PAGE)
                styled(r, 16, True)
            styled(p.add_run(b[1]), 16, True)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            out.append(p)
            out.append(new_para(''))
            first = False
        elif kind == 'sec':
            keys[b[2]] = b[1]
            out.append(new_para(''))
            sp = new_para(b[1], size=14, bold=True)
            sp.paragraph_format.keep_with_next = True
            out.append(sp)
            out.append(new_para(''))
        elif kind == 'sub':
            sp = new_para(b[1], size=11, bold=False, fi=11.0)
            sp.paragraph_format.keep_with_next = True
            out.append(sp)
        elif kind == 'p':
            out.append(new_para(b[1], size=11, fi=16.5))
            out[-1].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif kind == 'eq':
            out.append(new_eq(b[1], b[2]))
        elif kind == 'fig':
            out.extend(new_figure(b[1], b[2], b[3], b[5] if len(b) > 5 else None))
        elif kind == 'tbl':
            out.extend(new_table(b[1], b[2], b[3], b[4]))
    return out

def move_before(anchor_el, elements):
    for el in elements:
        node = el._element if hasattr(el, '_element') else el._p
        anchor_el.addprevious(node)

# ================= 1) 안내 페이지 삭제 (첫 페이지: 유의사항 + 규격 표들) =================
i, p = find_para('학위논문 작성 유의사항')
# 해당 페이지 요소들: 이 문단부터 '※ 본 페이지는 전자전기컴퓨터공학과' 직전까지
j, stop = find_para('본 페이지는 전자전기컴퓨터공학과')
el = p._element
to_del = []
while el is not None and el is not stop._element:
    nxt = el.getnext()
    to_del.append(el)
    el = nxt
for el in to_del:
    el.getparent().remove(el)

# ================= 2) 본심요약 표 채우기 =================
t_info = doc.tables[0]   # 학위 논문 제목/학과/학번/이름/지도교수
t_info.cell(0, 1).text = ''
cp = t_info.cell(0, 1).paragraphs[0]
cp.paragraph_format.line_spacing = 1.3
styled(cp.add_run(SUMMARY_KO_TITLE), 10)
for ri, val in [(2, ''), (3, '엄태욱'), (4, '국태용')]:
    c = t_info.cell(ri, 1); c.text = ''
    styled(c.paragraphs[0].add_run(val), 11)

# 요약(Abstract) 지시문 아래에 국문 요약 삽입
i, p = find_para('학위 논문의 요약문을 작성해 주십시오')
j, p2 = find_para('key word를 5개 이내로')
summ = []
for t in SUMMARY_KO:
    summ.append(new_para(t, size=11, fi=16.5, ls=1.45))
summ.append(new_para(SUMMARY_KO_KEYWORDS.replace('주제어:', 'Key Words:'), size=11, bold=True, ls=1.45))
move_before(p._element, summ)
delete_p(p); delete_p(p2)

# 기여도 표 채우기
t_prior = doc.tables[1]
t_prior.cell(1, 1).text = ''
styled(t_prior.cell(1, 1).paragraphs[0].add_run(
    'Tang 등(Systems, 2026)은 복수 센서 고장에서 HAZOP 위험 분석과 TTC/THW 평가로 MRM 행동을 적응 선택한다. '
    '본 논문은 고장 상태를 전제하지 않고 온라인 감시로 고장의 발생·종류·심각도 추정부터 수행하며, '
    '잔여 지각·측위 능력을 결합해 대피/정차를 구분하고 대피 이동 속도까지 제한한다.'), 9.5)
t_prior.cell(2, 1).text = ''
styled(t_prior.cell(2, 1).paragraphs[0].add_run(
    'Xue 등(IV 2018, JICV 2019)은 전방 센서 고장을 전제로 MPC 안전 제약 하의 안전 구역 정차 폴백을 제안한다. '
    '본 논문은 실제 오픈소스 스택(Autoware) 위 1,862 유효 케이스의 폐루프 검증과 판정 신뢰성이 확보된 '
    '보행자 조우 실험(용량-반응 120런, exact McNemar p=0.002)으로 검증 수준을 달리한다.'), 9.5)
t_prior.cell(3, 0).text = ''
styled(t_prior.cell(3, 0).paragraphs[0].add_run(
    '[1] J. Tang, C. Yang, H. Nishimura, "Minimum risk maneuver strategy for automated driving system under '
    'multiple conditions of sensor failure," Systems, 14(1), 2026.'), 9)
t_prior.cell(3, 1).text = ''
styled(t_prior.cell(3, 1).paragraphs[0].add_run(
    '[2] W. Xue, B. Yang, T. Kaizuka, K. Nakano, "A fallback approach for an automated vehicle encountering '
    'sensor failure in monitoring environment," IEEE IV, 2018.'), 9)

t_contrib = doc.tables[2]
t_contrib.cell(1, 1).text = ''
styled(t_contrib.cell(1, 1).paragraphs[0].add_run(
    '총 1,862 유효 케이스 단일 폐루프 검증; 검출률 96~100%(감내 설계 1개 조건 제외)·오발동 0/45; '
    '고장 상태 노출 238~275 m → 11~58 m 단축; 하드 페일 판정 1.5 s 마감 내 완료(최대 1.20 s); '
    '속도 상한 인과 효과 검출(8 m 쌍대 불일치 10:0, exact McNemar p=0.002), 회피/충돌 경계 단조 이동(9 m 초과→약 7 m).'), 9.5)
t_contrib.cell(2, 1).text = ''
styled(t_contrib.cell(2, 1).paragraphs[0].add_run(
    '연속 건강도·잔여능력 기반 단계적 MRM 선택이라는 감독 계층 아키텍처(비침습 add-on); '
    '시뮬레이션 충돌 판정의 이중 체계(실시간 원장+물리 오라클)와 판정 함정 규명이라는 방법론적 기여; '
    '감지 후 과도구간에 잔존 위험이 집중됨을 보인 조우 수준 관찰(FTTI 내 여유 확보 필요성의 정량 근거).'), 9.5)

# 실적 채우기: '1) 국제 저널 실적' 아래
i, p = find_para('1) 국제 저널 실적')
pubs = [
 new_para('[1] Tae Wook Eum, Jun Hyeon Choi, Ye Chan An, Jin Ho Kim, and Tae Yong Kuc, '
          '"Visible-Face-Aware Weighted Anchor Refinement with Utility-Guided Selective Correction for '
          'Monocular 3D Object Detection," IEEE Transactions on Intelligent Vehicles (under review, 2026).',
          size=10, ls=1.3),
 new_para('[2] Tae Wook Eum, Jun Hyeon Choi, Ye Chan An, Jin Ho Kim, and Tae Yong Kuc, '
          '"Graded Fault Response for Autonomous Driving via Continuous Sensor Health Monitoring and '
          'Risk/Capability-Aware MRM Supervision," IEEE Robotics and Automation Letters (in preparation, 2026).',
          size=10, ls=1.3),
]
nxt_el = p._element.getnext()
for np_ in pubs:
    nxt_el.addprevious(np_._p)

# 표지(covers)가 새 페이지에서 시작하도록: 첫 표지 표 앞에 페이지 브레이크
for tb in doc.tables:
    if 'Master' in tb.cell(1, 0).text if len(tb.rows) > 1 else False:
        pass
cover_tbl = None
for tb in doc.tables:
    try:
        txt = '\n'.join(c.text for r in tb.rows[:3] for c in r.cells)
    except Exception:
        continue
    if 'Master' in txt and 'Thesis' in txt:
        cover_tbl = tb
        break
if cover_tbl is not None:
    brk = new_para('')
    r = brk.add_run(); r.add_break(WD_BREAK.PAGE)
    cover_tbl._tbl.addprevious(brk._p)

# ================= 3) 목차(ToC/LoT/LoF) 재작성 =================
def _mk_tc(width, span, text, jc, bold=False):
    tc = OxmlElement('w:tc')
    tcPr = OxmlElement('w:tcPr')
    w = OxmlElement('w:tcW'); w.set(qn('w:w'), str(width)); w.set(qn('w:type'), 'dxa'); tcPr.append(w)
    if span > 1:
        gs = OxmlElement('w:gridSpan'); gs.set(qn('w:val'), str(span)); tcPr.append(gs)
    tb = OxmlElement('w:tcBorders')
    for s in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement(f'w:{s}'); e.set(qn('w:val'), 'nil'); tb.append(e)
    tcPr.append(tb)
    tm = OxmlElement('w:tcMar')
    for s, v in (('top', 28), ('left', 102), ('bottom', 28), ('right', 102)):
        e = OxmlElement(f'w:{s}'); e.set(qn('w:w'), str(v)); e.set(qn('w:type'), 'dxa'); tm.append(e)
    tcPr.append(tm)
    va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); tcPr.append(va)
    tc.append(tcPr)
    pel = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    ww = OxmlElement('w:wordWrap'); pPr.append(ww)
    sg = OxmlElement('w:snapToGrid'); sg.set(qn('w:val'), '0'); pPr.append(sg)
    sp = OxmlElement('w:spacing'); sp.set(qn('w:line'), '348'); sp.set(qn('w:lineRule'), 'auto'); pPr.append(sp)
    if jc:
        j = OxmlElement('w:jc'); j.set(qn('w:val'), jc); pPr.append(j)
    pel.append(pPr)
    rel = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    rf = OxmlElement('w:rFonts'); rf.set(qn('w:ascii'), FONT); rf.set(qn('w:eastAsia'), FONT); rPr.append(rf)
    if bold:
        b = OxmlElement('w:b'); rPr.append(b)
    sz = OxmlElement('w:sz'); sz.set(qn('w:val'), '22'); rPr.append(sz)
    rel.append(rPr)
    t_ = OxmlElement('w:t'); t_.set(qn('xml:space'), 'preserve'); t_.text = text; rel.append(t_)
    pel.append(rel)
    tc.append(pel)
    return tc

TOC_GRID = [2450, 849, 426, 1134, 993, 1276, 809, 567]
LO_GRID = [2127, 5811, 567]
DOTS = {7: 28, 6: 24, 5: 20, 4: 18, 3: 13, 2: 9, 1: 4}

def _set_grid_and_borders(te, grid):
    tblPr = te.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr'); te.insert(0, tblPr)
    for tag in ('w:tblW', 'w:tblBorders', 'w:tblLayout', 'w:tblCellMar'):
        e = tblPr.find(qn(tag))
        if e is not None:
            tblPr.remove(e)
    w = OxmlElement('w:tblW'); w.set(qn('w:w'), str(sum(grid))); w.set(qn('w:type'), 'dxa'); tblPr.append(w)
    bd = OxmlElement('w:tblBorders')
    for s in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement(f'w:{s}'); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '2')
        e.set(qn('w:space'), '0'); e.set(qn('w:color'), '000000'); bd.append(e)
    for s in ('insideH', 'insideV'):
        e = OxmlElement(f'w:{s}'); e.set(qn('w:val'), 'nil'); bd.append(e)
    tblPr.append(bd)
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    cm = OxmlElement('w:tblCellMar')
    for s, v in (('top', 15), ('left', 15), ('bottom', 15), ('right', 15)):
        e = OxmlElement(f'w:{s}'); e.set(qn('w:w'), str(v)); e.set(qn('w:type'), 'dxa'); cm.append(e)
    tblPr.append(cm)
    og = te.find(qn('w:tblGrid'))
    if og is not None:
        te.remove(og)
    g = OxmlElement('w:tblGrid')
    for cw in grid:
        c = OxmlElement('w:gridCol'); c.set(qn('w:w'), str(cw)); g.append(c)
    te.insert(list(te).index(tblPr) + 1, g)

def fill_toc_table(tbl, entries):
    """양식 원본과 동일: 고정폭 표, 제목 셀 가변 병합 + 점선 셀 + 쪽수 셀"""
    te = tbl._tbl
    _set_grid_and_borders(te, TOC_GRID)
    for tr in list(te.findall(qn('w:tr'))):
        te.remove(tr)
    cum = [sum(TOC_GRID[:k]) for k in range(1, 8)]
    for text, page in entries:
        est = int(len(text) * 128) + 204
        k = next((i + 1 for i, c in enumerate(cum[:6]) if c >= est), 6)
        dots_span = 7 - k
        tr = OxmlElement('w:tr')
        tr.append(_mk_tc(cum[k - 1], k, text, 'left'))
        tr.append(_mk_tc(sum(TOC_GRID[k:7]), dots_span, '·' * DOTS[dots_span], 'center'))
        tr.append(_mk_tc(567, 1, str(page), 'center'))
        te.append(tr)

def fill_lo_table(tbl, entries):
    """List of Tables/Figures: 양식 원본 3열(라벨|점선|쪽수)"""
    te = tbl._tbl
    _set_grid_and_borders(te, LO_GRID)
    for tr in list(te.findall(qn('w:tr'))):
        te.remove(tr)
    for label, page in entries:
        tr = OxmlElement('w:tr')
        tr.append(_mk_tc(LO_GRID[0], 1, label, 'left'))
        tr.append(_mk_tc(LO_GRID[1], 1, '·' * 25, 'center'))
        tr.append(_mk_tc(567, 1, str(page), 'center'))
        te.append(tr)

def pg(key, default='0'):
    return pagemap.get(key, default)

toc_entries = [
    ('Abstract', pg('abstract', 'i')),
    ('1. Introduction', pg('ch1', '1')),
    ('1.1  Research Background', pg('ch1s1', '1')),
    ('1.2  Research Questions', pg('ch1s2', '3')),
    ('1.3  Contribution', pg('ch1s3', '3')),
    ('1.4  Thesis Organization', pg('ch1s4', '4')),
    ('2. Background and Related Work', pg('ch2', '5')),
    ('2.1  Standards and Regulatory Frameworks', pg('ch2s1', '5')),
    ('2.2  FTTI and the Derivation of Time Budgets', pg('ch2s2', '5')),
    ('2.3  Fault Detection Theory and Sensor Degradation Models', pg('ch2s3', '6')),
    ('2.4  Fallback and MRM Planning', pg('ch2s4', '6')),
    ('2.5  Capability-Based Self-Monitoring and Runtime Monitoring', pg('ch2s5', '7')),
    ('2.6  Simulation-Based Evaluation and Fault Injection', pg('ch2s6', '7')),
    ('2.7  Comparison with Prior Work', pg('ch2s7', '8')),
    ('3. Proposed System', pg('ch3', '9')),
    ('3.1  System Architecture', pg('ch3s1', '9')),
    ('3.2  Sensor Scoring', pg('ch3s2', '10')),
    ('3.3  Spatial Sectors and Capability Synthesis', pg('ch3s3', '11')),
    ('3.4  Risk-Coupled Dynamic Detection Budget', pg('ch3s4', '12')),
    ('3.5  MRM Supervisor', pg('ch3s5', '13')),
    ('3.6  Conservative Low-Speed MRM Movement (Speed Cap)', pg('ch3s6', '15')),
    ('3.7  MRM Candidate Map Annotation', pg('ch3s7', '16')),
    ('3.8  Boundary and Interface with the Execution Layer', pg('ch3s8', '16')),
    ('4. Experimental Environment and Design', pg('ch4', '17')),
    ('4.1  Experimental Environment', pg('ch4s1', '17')),
    ('4.2  Fault Model', pg('ch4s2', '18')),
    ('4.3  Main Campaign Matrix', pg('ch4s3', '19')),
    ('4.4  Pedestrian Dart-out Encounter Injector', pg('ch4s4', '20')),
    ('4.5  Collision Adjudication Methodology', pg('ch4s5', '21')),
    ('4.6  Distance Ladder and 8 m Encounter Experiment Design', pg('ch4s6', '22')),
    ('4.7  Metrics and Statistics', pg('ch4s7', '23')),
    ('4.8  Reproducibility: Key Experimental Parameters', pg('ch4s8', '23')),
    ('5. Experimental Results', pg('ch5', '25')),
    ('5.1  Main Campaign: Detection Performance and Per-Fault Behavior', pg('ch5s1', '25')),
    ('5.2  Exposure Metric: Degraded-State Driving Distance', pg('ch5s2', '28')),
    ('5.3  Distance Ladder: Measuring the Avoid/Collide Boundary', pg('ch5s3', '29')),
    ('5.4  The 8 m Encounter: Low-Speed MRM versus Stock', pg('ch5s4', '30')),
    ('5.5  Low-Speed Ladder: Shift of the Boundary', pg('ch5s5', '31')),
    ('5.6  Causal Verification of the Speed Cap: Dose-Response Experiment', pg('ch5s6', '31')),
    ('5.7  Hard-Fail Decision Latency: Verifying the 1.5 s Deadline', pg('ch5s7', '33')),
    ('6. Limitations and Discussion', pg('ch6', '34')),
    ('6.1  The Temporal Trade-off Between Stopping and Evacuation', pg('ch6s1', '34')),
    ('6.2  The Post-Detection Transient, the Risk Window, and FTTI', pg('ch6s2', '34')),
    ('6.3  The Role of the Speed Cap: Causal Effect and Limits', pg('ch6s3', '35')),
    ('6.4  Lessons for Adjudication Methodology', pg('ch6s4', '35')),
    ('6.5  The Cost of Design Conservatism and the Execution/Map Layers', pg('ch6s5', '36')),
    ('6.6  Limitations', pg('ch6s6', '36')),
    ('7. Conclusion', pg('ch7', '38')),
    ('References', pg('refs', '40')),
    ('논문요약 (Korean Abstract)', pg('summary_ko', '44')),
]
lot_entries = [
    ('Table 2.1. Comparison of prior research lines with this study', pg('tbl2_1', '8')),
    ('Table 4.1. Fault model (v4.6)', pg('tbl4_1', '18')),
    ('Table 4.2. Main-campaign case accounting', pg('tbl4_acct', '19')),
    ('Table 4.3. Summary of key experimental parameters', pg('tbl4_3', '24')),
    ('Table 5.1. Detection rate and median latency per fault condition', pg('tbl5_0', '26')),
    ('Table 5.2. Evacuation behavior in the main campaign', pg('tbl5_1', '27')),
    ('Table 5.3. Distance ladder results', pg('tbl5_2', '29')),
    ('Table 5.4. Dose-response results', pg('tbl5_sd', '32')),
    ('Table 5.5. Hard-fail detection/decision latency', pg('tbl5_7', '33')),
]
lof_entries = [
    ('Figure 1.1. Problem setting', pg('fig1_1', '2')),
    ('Figure 3.1. Dual-channel structure of the proposed system', pg('fig3_1', '9')),
    ('Figure 3.2. Behavior-tree structure of the monitoring module', pg('fig3_bt', '12')),
    ('Figure 3.3. MRM selection policy matrix', pg('fig3_2', '13')),
    ('Figure 3.4. Town07 evacuation candidate map', pg('fig3_4', '14')),
    ('Figure 4.1. Representative execution views', pg('fig4_2', '17')),
    ('Figure 4.2. Sensor-level effects of fault injection', pg('fig4_faults', '19')),
    ('Figure 5.1. Detection-latency distributions per condition', pg('fig5_1dl', '26')),
    ('Figure 5.2. Injection-aligned continuous health traces', pg('fig5_2ht', '27')),
    ('Figure 5.3. Stopping-distance model vs measured boundaries', pg('fig5_2sd', '29')),
    ('Figure 5.4. Dose-response experiment', pg('fig5_6sd', '32')),
]
# 폼의 목차 표: tables 인덱스는 삭제 후 변동 없음(앞쪽 표 3개 삭제됨) → 재탐색
def table_after_para(text):
    i, p = find_para(text)
    el = p._element.getnext()
    while el is not None and not el.tag.endswith('}tbl'):
        el = el.getnext()
    from docx.table import Table
    return Table(el, doc)

toc_tbl = table_after_para('Table of Contents')
fill_toc_table(toc_tbl, toc_entries)
lot_tbl = table_after_para('List of Tables')
fill_lo_table(lot_tbl, [(e[0].split('. ')[0] + '.', e[1]) for e in lot_entries])
lof_tbl = table_after_para('List of Figures')
fill_lo_table(lof_tbl, [(e[0].split('. ')[0] + '.', e[1]) for e in lof_entries])

# ================= 4) Abstract 페이지 =================
iH, pH = find_para('Abstract')
# 'Abstract' 헤딩(목차 항목 아닌 실제 헤딩) 앞 페이지 브레이크
for pp in doc.paragraphs:
    if pp.text.strip() == 'Abstract':
        _b = new_para('')
        _r = _b.add_run(); _r.add_break(WD_BREAK.PAGE)
        pp._element.addprevious(_b._p)
        break
i, p = find_para('Thesis title')
p.text = ''
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.line_spacing = 1.45
for li, line in enumerate(EN_TITLE_L):
    r = styled(p.add_run(line), 16, True)
    if li < 2:
        r.add_break()
keys['abstract'] = 'Abstract'
# placeholder 본문 삭제 & 실제 초록 삽입
i0, p0 = find_para('여기부터 논문요약을 2page')
iK, pK = find_para('Keywords:')
abs_paras = [new_para(t, size=11, fi=16.5, ls=1.45) for t in ABSTRACT_EN]
for ap in abs_paras:
    ap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
move_before(p0._element, abs_paras)
# placeholder 삭제 (p0..pK 직전)
el = p0._element
while el is not None and el is not pK._element:
    nxt = el.getnext()
    if el.tag.endswith('}p'):
        el.getparent().remove(el)
    el = nxt
pK.text = ''
styled(pK.add_run(ABSTRACT_KEYWORDS), 11, True)
pK.paragraph_format.line_spacing = 1.45

# ================= 5) 본문 Chapter 1~7 =================
i, pch = find_para('Chapter 1. INTRODUCTION')
# 예시 블록 전체 삭제: Chapter 1 헤딩부터 References 헤딩 직전까지
iR, pR = find_para('References (16p)')
el = pch._element
while el is not None and el is not pR._element:
    nxt = el.getnext()
    el.getparent().remove(el)
    el = nxt
content = []
for ci, ch in enumerate([CH1, CH2, CH3, CH4, CH5, CH6, CH7]):
    content.extend(render_chapter(ch, first=(ci == 0)))
move_before(pR._element, content)

# ================= 6) References =================
pR.text = ''
pR.alignment = WD_ALIGN_PARAGRAPH.CENTER
pR.paragraph_format.line_spacing = 1.45
r = pR.add_run(); r.add_break(WD_BREAK.PAGE); styled(r, 16, True)
styled(pR.add_run('References'), 16, True)
keys['refs'] = 'References'
# 예시 문단들 삭제: References 헤딩 다음부터 Appendix 직전까지
iA, pA = find_para('Appendix (16p)')
el = pR._element.getnext()
while el is not None and el is not pA._element:
    nxt = el.getnext()
    el.getparent().remove(el)
    el = nxt
ref_paras = []
for n, ref in enumerate(REFS, 1):
    rp = new_para(f'{n}. {ref}', size=11, ls=1.3)
    rp.paragraph_format.left_indent = Cm(0.9)
    rp.paragraph_format.first_line_indent = Cm(-0.9)
    rp.paragraph_format.space_after = Pt(3)
    ref_paras.append(rp)
move_before(pA._element, ref_paras)

# ================= 7) Appendix 삭제 =================
i2, p2 = find_para('논문요약')  # 국문 요약 헤딩 (Appendix 뒤)
# 정확 앵커: '논문제목을 작성하시오' 페이지의 직전 헤딩 '논문요약'
el = pA._element
iH, pH = find_para('논문요약', start=0)
# pH가 pA 이후인지 확인하며 탐색
found = None
for idx, pp in enumerate(doc.paragraphs):
    if pp.text.strip() == '논문요약':
        found = pp
if found is None:
    raise RuntimeError('논문요약 heading not found')
brk2 = new_para('')
_r = brk2.add_run(); _r.add_break(WD_BREAK.PAGE)
found._element.addprevious(brk2._p)
while el is not None and el is not found._element:
    nxt = el.getnext()
    el.getparent().remove(el)
    el = nxt
keys['summary_ko'] = '논문요약'

# ================= 8) 국문 논문요약 =================
i, pT = find_para('논문제목을 작성하시오')
pT.text = ''
pT.alignment = WD_ALIGN_PARAGRAPH.CENTER
pT.paragraph_format.line_spacing = 1.45
for li, line in enumerate(KO_TITLE_L):
    r = styled(pT.add_run(line), 16, True)
    if li < 2:
        r.add_break()
for anchor, val in [('제출자 성명', '엄태욱'), ('OO학과', '전자전기컴퓨터공학과'), ('성균관대학교', '성균관대학교')]:
    i, pp = find_para(anchor)
    pp.text = ''
    pp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pp.paragraph_format.line_spacing = 1.45
    styled(pp.add_run(val), 11)
i0, p0 = find_para('여기부터 본문을 국문으로')
iK, pK = find_para('주제어:')
ko_paras = [new_para(t, size=11, fi=16.5, ls=1.45) for t in SUMMARY_KO]
for kp in ko_paras:
    kp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
move_before(p0._element, ko_paras)
el = p0._element
while el is not None and el is not pK._element:
    nxt = el.getnext()
    if el.tag.endswith('}p'):
        el.getparent().remove(el)
    el = nxt
pK.text = ''
styled(pK.add_run(SUMMARY_KO_KEYWORDS), 11, True)
pK.paragraph_format.line_spacing = 1.45

doc.save(OUT)
json.dump(keys, open(os.path.join(HERE, 'keys_form.json'), 'w'), ensure_ascii=False, indent=1)
print('saved', OUT)
