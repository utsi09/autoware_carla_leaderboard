# -*- coding: utf-8 -*-
import json, os, re, subprocess
HERE=os.path.dirname(os.path.abspath(__file__))
PDF='/home/taewook/autoware_carla_leaderboard/doc/thesis_bonsim_v3_0831.pdf'
txt=subprocess.run(['pdftotext','-layout',PDF,'-'],capture_output=True,text=True).stdout
pages=txt.split('\f')
norm=lambda s: re.sub(r'\s+','',s)
np_=[norm(p) for p in pages]
keys=json.load(open(os.path.join(HERE,'keys_final.json')))
# 기준점
def page_of(needle, frm=0):
    n=norm(needle)
    for i in range(frm,len(np_)):
        if n in np_[i]: return i
    return None
toc_p=page_of('TableofContents')
body_p=page_of('Chapter1.INTRODUCTION', toc_p+1)
ROMANS=['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi','xii']
def disp(pdf_i):
    if pdf_i>=body_p: return str(pdf_i-body_p+1)
    if pdf_i>=toc_p: return ROMANS[pdf_i-toc_p]
    return '?'
out={}; missing=[]
for key,needle in keys.items():
    i=page_of(needle, toc_p+1 if key!='abstract' else toc_p)
    # 목차 자체에 같은 문자열이 있으므로 본문 우선: abstract는 front, 나머지는 body부터 탐색
    if key in ('abstract',):
        i=page_of('Keywords:', toc_p)  # abstract 본문 페이지
        # abstract 제목 페이지 = 첫 키워드 페이지 앞쪽; 제목 페이지 찾기
        j=page_of('Fail-SafeOperationofAutonomousVehicles', toc_p)
        i=j if j is not None else i
    else:
        i=page_of(needle, body_p) or page_of(needle, toc_p)
    if i is None: missing.append(key); continue
    out[key]=disp(i)
json.dump(out, open(os.path.join(HERE,'pagemap_final.json'),'w'), ensure_ascii=False, indent=1)
print('toc pdf-page',toc_p+1,'body pdf-page',body_p+1)
print('mapped',len(out),'missing',missing)
