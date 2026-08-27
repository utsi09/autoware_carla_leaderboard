# -*- coding: utf-8 -*-
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = '/home/taewook/autoware_carla_leaderboard/doc/thesis_en_v23_0827.pdf'

txt = subprocess.run(['pdftotext', '-layout', PDF, '-'],
                     capture_output=True, text=True).stdout
pages = txt.split('\f')

def norm(s):
    return re.sub(r'\s+', '', s)

npages = [norm(p) for p in pages]

# find body start: first page whose footer (last nonempty line) is '1' after page 8
body_start = None
for i, p in enumerate(pages):
    lines = [l.strip() for l in p.splitlines() if l.strip()]
    if i >= 8 and lines and lines[-1] == '1':
        body_start = i
        break
assert body_start is not None, 'body start not found'

with open(os.path.join(HERE, 'keys.json')) as f:
    keys = json.load(f)

pagemap = {}
missing = []
for key, text in keys.items():
    needle = norm(text)
    if key.startswith('tbl') or key.startswith('fig'):
        needle = needle + '.'
    found = None
    for i in range(body_start, len(npages)):
        if needle in npages[i]:
            found = i - body_start + 1
            break
    if found is None and len(needle) > 24:
        # 제목이 페이지 경계에서 갈리는 경우: 앞 24자 접두로 재시도
        pre = needle[:24]
        for i in range(body_start, len(npages)):
            if pre in npages[i]:
                found = i - body_start + 1
                break
    if found:
        pagemap[key] = str(found)
    else:
        missing.append((key, text))

with open(os.path.join(HERE, 'pagemap.json'), 'w') as f:
    json.dump(pagemap, f, ensure_ascii=False, indent=1)
print('body_start pdf page:', body_start + 1)
print('mapped:', len(pagemap), 'missing:', missing)
