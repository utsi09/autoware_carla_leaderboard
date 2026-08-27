# -*- coding: utf-8 -*-
"""English thesis builder (SKKU EN template conventions, mirrors v20 KO build).
Body from translated.json (workflow output); titles/refs/abstract/KO-summary
reused from thesis_build_v20 content modules. Front matter order per EN template:
covers -> approval -> Table of Contents -> List of Tables -> List of Figures ->
Abstract -> body -> References -> 논문요약(KO)."""
import json, os, sys
from docx import Document
from docx.shared import Pt, Cm, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'thesis_build_v20'))
from content1 import (TITLE_KO_L1, TITLE_KO_L2, TITLE_KO_L3,
                      TITLE_EN_L1, TITLE_EN_L2, TITLE_EN_L3,
                      SUMMARY_KO, SUMMARY_KEYWORDS)
from content3 import REFS, ABSTRACT_EN, ABSTRACT_KEYWORDS

TEMPLATE = '/home/taewook/autoware_carla_leaderboard/doc/templates/skku_ko_template.docx'
OUT = '/home/taewook/autoware_carla_leaderboard/doc/thesis_en_v28_0827.docx'
FONT_EA = 'HY신명조'
FONT_LAT = 'Times New Roman'

tr = json.load(open(os.path.join(HERE, 'translated.json')))
CHAPS = []
for name in ('ch1', 'ch2', 'ch3', 'ch4', 'ch5a', 'ch5b', 'ch6', 'ch7'):
    blocks = [tuple([it['kind']] + it['fields']) for it in tr[name]['items']]
    if name == 'ch5b':
        CHAPS[-1] = CHAPS[-1] + blocks
    else:
        CHAPS.append(blocks)

pagemap = {}
pm_path = os.path.join(HERE, 'pagemap.json')
if os.path.exists(pm_path):
    pagemap = json.load(open(pm_path))
keys = {}

def style_run(r, size=11, bold=False):
    r.font.name = FONT_LAT
    r.font.size = Pt(size)
    r.font.bold = bold
    rPr = r._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rPr.insert(0, rf)
    rf.set(qn('w:eastAsia'), FONT_EA)
    return r

GRID = Pt(25.05)

def para(doc, text='', size=11, bold=False, align=None, spacing=2.0, page_break=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = GRID if spacing == 2.0 else spacing
    pf.space_before = Pt(0); pf.space_after = Pt(0)
    if align is not None:
        p.alignment = align
    if page_break:
        pf.page_break_before = True
    if text:
        style_run(p.add_run(text), size=size, bold=bold)
    return p

def body_para(doc, text):
    return para(doc, '   ' + text, size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

def section(doc, title, key=None):
    if key:
        keys[key] = title
    para(doc); para(doc, title, size=14, bold=True); para(doc)

def subsection(doc, title):
    para(doc, title, size=11, bold=True)

def equation(doc, text, num):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = GRID
    p.paragraph_format.tab_stops.add_tab_stop(Cm(15.0), WD_TAB_ALIGNMENT.RIGHT)
    p.paragraph_format.left_indent = Cm(1.0)
    style_run(p.add_run(text), size=11)
    style_run(p.add_run('\t' + num), size=11)

def caption_para(doc, caption):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.3
    pf.space_before = Pt(2); pf.space_after = Pt(0)
    head, sep, rest = caption.partition('. ')
    style_run(p.add_run(head + sep), size=9.0, bold=True)
    if rest:
        style_run(p.add_run(rest), size=9.0)
    return p

ALLOW_SPLIT = {'tbl2_1', 'tbl5_0', 'tbl4_3'}

def add_table(doc, caption, key, rows, note):
    keys[key] = caption.split('. ')[0]
    cap = caption_para(doc, caption)
    cap.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = 'Table Grid'
    t.alignment = 1
    keep_whole = (len(rows) <= 15) and key not in ALLOW_SPLIT
    for ri, trr in enumerate(t.rows):
        trPr = trr._tr.get_or_add_trPr()
        trPr.append(OxmlElement('w:cantSplit'))
        if ri == 0:
            trPr.append(OxmlElement('w:tblHeader'))
    for ri, row in enumerate(rows):
        for ci, cell_text in enumerate(row):
            cell = t.cell(ri, ci)
            cell.text = ''
            first = True
            for line in str(cell_text).split('\n'):
                cp = cell.paragraphs[0] if first else cell.add_paragraph()
                first = False
                cp.paragraph_format.line_spacing = 1.2
                cp.paragraph_format.space_before = Pt(1)
                cp.paragraph_format.space_after = Pt(1)
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER if ri == 0 else WD_ALIGN_PARAGRAPH.LEFT
                if keep_whole and ri < len(rows) - 1:
                    cp.paragraph_format.keep_with_next = True
                style_run(cp.add_run(line), size=9.0, bold=(ri == 0))
    if note:
        n = para(doc, note, size=9.0)
        n.paragraph_format.line_spacing = 1.3
    para(doc)

def drop_last_blank(doc):
    last = doc.paragraphs[-1]
    if not last.text.strip():
        last._element.getparent().remove(last._element)

def add_figure(doc, caption, key, path, note, width_cm=None):
    keys[key] = caption.split('. ')[0]
    if path and os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Cm(width_cm if width_cm else 14.5))
    cap = caption_para(doc, caption)
    cap.paragraph_format.keep_together = True
    if note:
        n = para(doc, note, size=9.0)
        n.paragraph_format.line_spacing = 1.3
    para(doc)

def set_pgnum(sec, fmt=None, start=None):
    sectPr = sec._sectPr
    pg = sectPr.find(qn('w:pgNumType'))
    if pg is None:
        pg = OxmlElement('w:pgNumType')
        cols = sectPr.find(qn('w:cols'))
        if cols is not None:
            cols.addprevious(pg)
        else:
            sectPr.append(pg)
    if fmt:
        pg.set(qn('w:fmt'), fmt)
    if start is not None:
        pg.set(qn('w:start'), str(start))

def footer_pagenum(sec, size=11):
    sec.footer.is_linked_to_previous = False
    p = sec.footer.paragraphs[0]
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.0
    r1 = p.add_run(); style_run(r1, size=size)
    fld = OxmlElement('w:fldChar'); fld.set(qn('w:fldCharType'), 'begin')
    r1._element.append(fld)
    r2 = p.add_run(); style_run(r2, size=size)
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve')
    instr.text = ' PAGE '
    r2._element.append(instr)
    r3 = p.add_run(); style_run(r3, size=size)
    fld2 = OxmlElement('w:fldChar'); fld2.set(qn('w:fldCharType'), 'end')
    r3._element.append(fld2)

def empty_footer(sec):
    sec.footer.is_linked_to_previous = False
    p = sec.footer.paragraphs[0]
    for r in list(p.runs):
        r._element.getparent().remove(r._element)

def toc_line(doc, text, page_label, indent=0, size=11):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = GRID
    pf.left_indent = Cm(indent)
    pf.tab_stops.add_tab_stop(Cm(15.0 - indent), WD_TAB_ALIGNMENT.RIGHT,
                              WD_TAB_LEADER.DOTS)
    style_run(p.add_run(text), size=size)
    style_run(p.add_run('\t' + (page_label or '')), size=size)

# ---------- document ----------
doc = Document(TEMPLATE)
body = doc.element.body
for child in list(body):
    if child.tag != qn('w:sectPr'):
        body.remove(child)
sec0 = doc.sections[0]
sec0.top_margin = Twips(3005); sec0.bottom_margin = Twips(3005)
sec0.left_margin = Twips(1701); sec0.right_margin = Twips(1701)
sec0.header_distance = Twips(851); sec0.footer_distance = Twips(851)
empty_footer(sec0)

CENTER = WD_ALIGN_PARAGRAPH.CENTER
RIGHT = WD_ALIGN_PARAGRAPH.RIGHT
LEFT = WD_ALIGN_PARAGRAPH.LEFT

def cover_page(doc, korean_sub=False, submit=False):
    para(doc, "Master's Thesis", size=16, bold=True, align=LEFT, spacing=1.5)
    para(doc, 'Advisor: ○ ○ ○', size=14, align=RIGHT, spacing=1.5)
    for _ in range(2 if submit else 3):
        para(doc, spacing=1.5)
    para(doc, TITLE_EN_L1, size=20, bold=True, align=CENTER, spacing=1.5)
    para(doc, TITLE_EN_L2, size=20, bold=True, align=CENTER, spacing=1.5)
    para(doc, TITLE_EN_L3, size=20, bold=True, align=CENTER, spacing=1.5)
    if korean_sub:
        para(doc, spacing=1.5)
        para(doc, TITLE_KO_L1 + ' ' + TITLE_KO_L2, size=14, align=CENTER, spacing=1.5)
        para(doc, TITLE_KO_L3, size=14, align=CENTER, spacing=1.5)
    if submit:
        para(doc, spacing=1.5)
        para(doc, 'A thesis submitted to the Graduate School of Sungkyunkwan University',
             size=13, align=CENTER, spacing=1.5)
        para(doc, 'in partial fulfillment of the requirements for the degree of',
             size=13, align=CENTER, spacing=1.5)
        para(doc, 'Master of Science in Engineering', size=13, align=CENTER, spacing=1.5)
        para(doc, spacing=1.5)
        para(doc, 'April 2026', size=14, align=CENTER, spacing=1.5)
    n_blank = 1 if submit else (4 if korean_sub else 6)
    for _ in range(n_blank):
        para(doc, spacing=1.5)
    para(doc, 'The Graduate School', size=15, bold=True, align=CENTER, spacing=1.5)
    para(doc, 'Sungkyunkwan University', size=15, bold=True, align=CENTER, spacing=1.5)
    para(doc, 'Department of Electrical and Computer Engineering', size=13,
         align=CENTER, spacing=1.5)
    para(doc, '○ ○ ○', size=15, bold=True, align=CENTER, spacing=1.5)

# 1) cover / 2) inner cover / 3) submission page
cover_page(doc)
doc.add_section(WD_SECTION.NEW_PAGE); cover_page(doc, korean_sub=True)
doc.add_section(WD_SECTION.NEW_PAGE); cover_page(doc, korean_sub=True, submit=True)

# 4) approval page
doc.add_section(WD_SECTION.NEW_PAGE)
for _ in range(2):
    para(doc, spacing=1.5)
para(doc, "This certifies that the master's thesis", size=16, bold=True, align=CENTER)
para(doc, 'of ○ ○ ○ is approved.', size=16, bold=True, align=CENTER)
for _ in range(2):
    para(doc, spacing=1.5)
para(doc, 'June 2026', size=16, align=CENTER)
for _ in range(3):
    para(doc, spacing=1.5)
for role in ['Committee Chair', 'Committee Member', 'Committee Member']:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = GRID
    p.alignment = RIGHT
    style_run(p.add_run(role + '                              (Seal)'), size=14)
    para(doc, spacing=1.5)

# 5) front matter (roman numerals): ToC, LoT, LoF, Abstract
sec = doc.add_section(WD_SECTION.NEW_PAGE)
set_pgnum(sec, fmt='lowerRoman', start=1)
footer_pagenum(sec)

para(doc, 'Table of Contents', size=16, bold=True, align=CENTER)
para(doc)
ALL_BLOCKS = [b for chap in CHAPS for b in chap]
for b in ALL_BLOCKS:
    if b[0] == 'ch':
        toc_line(doc, b[1], pagemap.get(b[2], ''))
    elif b[0] == 'sec':
        toc_line(doc, b[1], pagemap.get(b[2], ''), indent=1.0)
toc_line(doc, 'References', pagemap.get('refs', ''))
toc_line(doc, '논문요약', pagemap.get('kosum', ''))

para(doc, 'List of Tables', size=14, bold=True, align=CENTER, page_break=True)
para(doc)
for b in ALL_BLOCKS:
    if b[0] == 'tbl':
        parts = b[1].split('. ', 1)
        title = parts[0] + '. ' + parts[1].split('. ')[0] if len(parts) > 1 else b[1]
        toc_line(doc, title, pagemap.get(b[2], ''))

para(doc, 'List of Figures', size=14, bold=True, align=CENTER, page_break=True)
para(doc)
for b in ALL_BLOCKS:
    if b[0] == 'fig':
        parts = b[1].split('. ', 1)
        title = parts[0] + '. ' + parts[1].split('. ')[0] if len(parts) > 1 else b[1]
        toc_line(doc, title, pagemap.get(b[2], ''))

para(doc, 'Abstract', size=14, bold=True, page_break=True)
para(doc)
para(doc, TITLE_EN_L1, size=16, bold=True, align=CENTER, spacing=1.5)
para(doc, TITLE_EN_L2, size=16, bold=True, align=CENTER, spacing=1.5)
para(doc, TITLE_EN_L3, size=16, bold=True, align=CENTER, spacing=1.5)
para(doc)
for t in ABSTRACT_EN:
    body_para(doc, '  ' + t.strip())
para(doc)
para(doc, ABSTRACT_KEYWORDS, size=11, bold=True)

# 6) body (arabic from 1)
sec = doc.add_section(WD_SECTION.NEW_PAGE)
set_pgnum(sec, fmt='decimal', start=1)
footer_pagenum(sec)

first = True
for chap in CHAPS:
    for i, b in enumerate(chap):
        if b[0] == 'ch':
            keys[b[2]] = b[1]
            para(doc, b[1], size=16, bold=True, align=CENTER, page_break=not first)
            para(doc)
            first = False
        elif b[0] == 'sec':
            section(doc, b[1], b[2])
        elif b[0] == 'sub':
            subsection(doc, b[1])
        elif b[0] == 'p':
            body_para(doc, b[1])
        elif b[0] == 'eq':
            equation(doc, b[1], b[2])
        elif b[0] == 'tbl':
            add_table(doc, b[1], b[2], b[3], b[4])
            if i == len(chap) - 1:
                drop_last_blank(doc)
        elif b[0] == 'fig':
            add_figure(doc, b[1], b[2], b[3], b[4], b[5] if len(b) > 5 else None)
            if i == len(chap) - 1:
                drop_last_blank(doc)

# References (list preserved verbatim from the Korean thesis)
keys['refs'] = 'References'
para(doc, 'References', size=16, bold=True, align=CENTER, page_break=True)
para(doc)
REF_KO2EN = {'평가 버전': 'evaluated version', '개발 중': 'under development'}
for i, ref in enumerate(REFS, 1):
    for k, v in REF_KO2EN.items():
        ref = ref.replace(k, v)
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.left_indent = Cm(0.9)
    pf.first_line_indent = Cm(-0.9)
    pf.space_after = Pt(4)
    style_run(p.add_run(f'[{i}] {ref}'), size=11)

# 논문요약 (Korean abstract, per SKKU EN-thesis back matter)
keys['kosum'] = '논문요약'
para(doc, '논문요약', size=14, bold=True, page_break=True)
para(doc)
para(doc, TITLE_KO_L1 + ' ' + TITLE_KO_L2, size=16, bold=True, align=CENTER, spacing=1.5)
para(doc, TITLE_KO_L3, size=16, bold=True, align=CENTER, spacing=1.5)
para(doc)
para(doc, '○ ○ ○', size=11, align=RIGHT, spacing=1.5)
para(doc, '성균관대학교 일반대학원', size=11, align=RIGHT, spacing=1.5)
para(doc, '전자전기컴퓨터공학과', size=11, align=RIGHT, spacing=1.5)
para(doc)
for t in SUMMARY_KO:
    body_para(doc, t)
para(doc)
para(doc, SUMMARY_KEYWORDS, size=11, bold=True)

doc.save(OUT)
json.dump(keys, open(os.path.join(HERE, 'keys.json'), 'w'), ensure_ascii=False, indent=1)
print('saved', OUT)
