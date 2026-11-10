#!/usr/bin/env python3
"""조우 블록 그림: 고장 4종 × (순정, 제안) — 보행자(고장+5 s, 8 m 앞, 2.5 m/s 횡단) 반응.
GT(20 Hz) 로 등장 2 s 내 제동 여부, 정지까지 시간, 차체 최소 거리; results csv 로 보행자 접촉·결말.
출력: results/figs/fig_encounter.png"""
import csv, glob, math, os, collections, statistics as st
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = ["NanumGothic", "DejaVu Sans"]; matplotlib.rcParams["axes.unicode_minus"] = False
RES = os.path.join(os.path.dirname(__file__), "..", "results")
FAULTS = [("nf","고장 없음"),("lso","라이다 성김"),("lcl","비 클러터"),("cn","카메라 잡음")]
done = set(l.strip() for l in open(os.path.join(RES,"encounter_done.txt")))
res = {}
STAMP_MAX = "1108_1111"   # [2026-11-08] 조우 블록 마지막 보충(11/08 11:10 ours-lso r7)까지. 그 뒤 lcl 검증 런은 같은 꼴(lcl·def·t=10)이라 제외
for f in sorted(glob.glob(os.path.join(RES,"results_11*_*.csv"))):   # 정렬: 같은 셀은 나중 실행이 덮어씀
    if not ("1106_0000" <= os.path.basename(f)[8:-4] <= STAMP_MAX): continue
    for r in csv.DictReader(open(f)):
        if r.get("npc")=="def" and r.get("trigger_s")=="10" and r.get("fault") in ("nf","lso","lcl","cn"):
            res[(r["method"],r["fault"],r["rep"])] = r
data = collections.defaultdict(list)
cand = collections.defaultdict(list)   # [2026-11-08] 셀마다 보행자가 나온 가장 최근 GT 하나만 (중단·재실행 중복 방지)
for g in glob.glob(os.path.join(RES,"gt","*-def-r*-11*_*.csv")):
    if g.endswith("_tl.csv"): continue
    b = os.path.basename(g)[:-4]; p = b.split("-"); method = "stock" if p[0]=="stock" else "ours"
    if not ("1106_0000" <= p[-1] <= STAMP_MAX): continue
    if method=="stock": p = p[1:]
    fault, sev, rep = p[0], p[1], p[3].lstrip("r").split("_")[0]
    if fault not in dict(FAULTS) or f"{fault} {sev.replace('_',':')} {method} {rep}" not in done: continue
    cand[(method, fault, rep)].append((p[-1], g))
def _pick():
    for k in sorted(cand):
        for _, g in sorted(cand[k], reverse=True):
            rows = list(csv.DictReader(open(g)))
            if any(r["kind"]=="walker" for r in rows): yield (*k, g, rows); break
for method, fault, rep, g, rows in _pick():
    ego=[r for r in rows if r["kind"]=="ego"]; w=[r for r in rows if r["kind"]=="walker"]
    eg = {round(float(r["aw_sec"]),2): r for r in ego}; ts = float(w[0]["aw_sec"])
    # 차체(GT length/width) 외곽과 보행자 반경 사이 거리; <=0 이면 접촉. 리더보드 json 은 러너가 시나리오
    # 끝 전에 케이스를 끊으면(완주 근접·정지 판정) 기록이 비어 접촉이 빠진다(11/08 확인) → 접촉은 GT 로만 센다.
    hl = float(ego[0]["length"])/2; hw = float(ego[0]["width"])/2; wr = max(float(w[0]["length"]), float(w[0]["width"]))/2
    gap = None; vhit = None
    for r in w:
        e = eg.get(round(float(r["aw_sec"]),2))
        if not e: continue
        yaw = math.radians(float(e["yaw_deg"])); dx=float(r["x"])-float(e["x"]); dy=float(r["y"])-float(e["y"])
        fx = dx*math.cos(yaw)+dy*math.sin(yaw); fy = -dx*math.sin(yaw)+dy*math.cos(yaw)
        d = math.hypot(max(abs(fx)-hl,0), max(abs(fy)-hw,0)) - wr
        if d <= 0 and vhit is None: vhit = float(e["speed"])
        gap = d if gap is None else min(gap,d)
    gap = max(gap, 0.0) if gap is not None else None
    seg = [r for r in ego if ts <= float(r["aw_sec"]) <= ts+15]
    e0 = eg.get(round(ts,2)); v0 = float(e0["speed"]); e2 = min(ego, key=lambda r: abs(float(r["aw_sec"])-(ts+2))); v2=float(e2["speed"])
    tstop = next((float(r["aw_sec"])-ts for r in seg if float(r["speed"])<0.15), None)
    rr = res.get((method,fault,rep)); ped = 1 if vhit is not None else 0
    out = rr["outcome"] if rr else "?"
    data[(fault,method)].append(dict(braked=v2 < v0-1.0, tstop=tstop, gap=gap, ped=ped, vhit=vhit, out=out))
fig, ax = plt.subplots(1, 4, figsize=(15, 3.9))
x = list(range(len(FAULTS))); wbar = 0.36; col = {"stock":"#999999","ours":"#1f77b4"}; lab={"stock":"순정 Autoware","ours":"제안(감독자)"}
for k,(m) in enumerate(("stock","ours")):
    off = (-wbar/2 if m=="stock" else wbar/2)
    br = [100*sum(d["braked"] for d in data[(f,m)])/max(1,len(data[(f,m)])) for f,_ in FAULTS]
    ax[0].bar([i+off for i in x], br, wbar, color=col[m], label=lab[m])
    for i,(f,_) in enumerate(FAULTS):
        L=[d["tstop"] for d in data[(f,m)] if d["tstop"] is not None]; G=[d["gap"] for d in data[(f,m)] if d["gap"] is not None]
        if L: ax[1].boxplot(L, positions=[i+off], widths=wbar*0.8, patch_artist=True, boxprops=dict(facecolor=col[m]), medianprops=dict(color="k"), showfliers=False)
        if G: ax[2].boxplot(G, positions=[i+off], widths=wbar*0.8, patch_artist=True, boxprops=dict(facecolor=col[m]), medianprops=dict(color="k"), showfliers=False)
    pc = [100*sum(1 for d in data[(f,m)] if d["ped"]>0)/max(1,len(data[(f,m)])) for f,_ in FAULTS]
    ax[3].bar([i+off for i in x], pc, wbar, color=col[m])
    for i,(f,_) in enumerate(FAULTS):
        V=sorted(d["vhit"] for d in data[(f,m)] if d["vhit"] is not None)
        if V: ax[3].text(i+off, pc[i]+1.5, f"{V[len(V)//2]:.1f}", ha="center", fontsize=7)
for i,(f,name) in enumerate(FAULTS):
    for m,off in (("stock",-wbar/2),("ours",wbar/2)):
        n=len(data[(f,m)]); ax[0].text(i+off, 2, f"n={n}", ha="center", fontsize=7, color="w" if m=="ours" else "k")
ax[0].set_title("(a) 등장 2 s 안에 제동한 비율 [%]"); ax[0].set_ylim(0,105)
ax[1].set_title("(b) 등장→정지 시간 [s]"); ax[1].axhline(0, color="none")
ax[2].set_title("(c) 보행자-차체 최소 거리 [m]")
ax[3].set_title("(d) 보행자 접촉 비율 [%] (GT 차체 겹침)"); ax[3].set_ylim(0,112); ax[3].set_xlabel("막대 위 숫자 = 접촉 순간 속도 중앙값 [m/s]", fontsize=8)
for a in ax:
    a.set_xticks(x); a.set_xticklabels([n for _,n in FAULTS], fontsize=9); a.grid(axis="y", alpha=0.3)
h,l = ax[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5,0.0))
fig.suptitle("조우 블록: 고장 5 s 뒤 4 m/s 주행 중 8 m 앞 보행자 횡단 (교차로 30 m 전, 교통 def)", fontsize=11)
fig.tight_layout(rect=(0,0.07,1,0.95))
out = os.path.join(RES,"figs","fig_encounter.png"); os.makedirs(os.path.dirname(out), exist_ok=True); fig.savefig(out, dpi=140); print(out)
for (f,m),L in sorted(data.items()):
    V=sorted(d["vhit"] for d in L if d["vhit"] is not None); print(f, m, len(L), "braked", sum(d["braked"] for d in L), "contact", len(V), "v_hit_med", V[len(V)//2] if V else None, collections.Counter(d["out"] for d in L))
