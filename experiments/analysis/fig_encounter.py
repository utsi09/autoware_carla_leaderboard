#!/usr/bin/env python3
"""조우 블록 그림: 고장 4종 × (순정, 제안) — 보행자(고장+5 s, 8 m 앞, 2.5 m/s 횡단) 반응.
GT(20 Hz) 로 등장 2 s 내 제동 여부, 정지까지 시간, 차체 최소 거리; results csv 로 보행자 접촉·결말.
출력: results/figs/fig_encounter.png"""
import csv, glob, math, os, collections, statistics as st
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
RES = os.path.join(os.path.dirname(__file__), "..", "results")
FAULTS = [("nf","고장 없음"),("lso","라이다 성김"),("lcl","비 클러터"),("cn","카메라 잡음")]
done = set(l.strip() for l in open(os.path.join(RES,"encounter_done.txt")))
res = {}
for f in glob.glob(os.path.join(RES,"results_1106_*.csv")):
    for r in csv.DictReader(open(f)):
        if r.get("npc")=="def" and r.get("trigger_s")=="10" and r.get("fault") in ("nf","lso","lcl","cn"):
            res[(r["method"],r["fault"],r["rep"])] = r
data = collections.defaultdict(list)
for g in sorted(glob.glob(os.path.join(RES,"gt","*-def-r*-1106_*.csv"))):
    if g.endswith("_tl.csv"): continue
    b = os.path.basename(g)[:-4]; p = b.split("-"); method = "stock" if p[0]=="stock" else "ours"
    if method=="stock": p = p[1:]
    fault, sev, rep = p[0], p[1], p[3].lstrip("r").split("_")[0]
    if fault not in dict(FAULTS) or f"{fault} {sev.replace('_',':')} {method} {rep}" not in done: continue
    rows = list(csv.DictReader(open(g))); ego=[r for r in rows if r["kind"]=="ego"]; w=[r for r in rows if r["kind"]=="walker"]
    if not w: continue
    eg = {round(float(r["aw_sec"]),2): r for r in ego}; ts = float(w[0]["aw_sec"])
    gap = None
    for r in w:
        e = eg.get(round(float(r["aw_sec"]),2))
        if not e: continue
        yaw = math.radians(float(e["yaw_deg"])); dx=float(r["x"])-float(e["x"]); dy=float(r["y"])-float(e["y"])
        fx = dx*math.cos(yaw)+dy*math.sin(yaw); fy = -dx*math.sin(yaw)+dy*math.cos(yaw)
        d = math.hypot(max(abs(fx)-2.35,0), max(abs(fy)-1.0,0))
        gap = d if gap is None else min(gap,d)
    seg = [r for r in ego if ts <= float(r["aw_sec"]) <= ts+15]
    e0 = eg.get(round(ts,2)); v0 = float(e0["speed"]); e2 = min(ego, key=lambda r: abs(float(r["aw_sec"])-(ts+2))); v2=float(e2["speed"])
    tstop = next((float(r["aw_sec"])-ts for r in seg if float(r["speed"])<0.15), None)
    rr = res.get((method,fault,rep)); ped = 0
    if rr and rr.get("collision_types"):
        ped = sum(int(t.split(":")[1]) for t in rr["collision_types"].split("+") if t.startswith("pedestrian"))
    out = rr["outcome"] if rr else "?"
    data[(fault,method)].append(dict(braked=v2 < v0-1.0, tstop=tstop, gap=gap, ped=ped, out=out))
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
for i,(f,name) in enumerate(FAULTS):
    for m,off in (("stock",-wbar/2),("ours",wbar/2)):
        n=len(data[(f,m)]); ax[0].text(i+off, 2, f"n={n}", ha="center", fontsize=7, color="w" if m=="ours" else "k")
ax[0].set_title("(a) 등장 2 s 안에 제동한 비율 [%]"); ax[0].set_ylim(0,105)
ax[1].set_title("(b) 등장→정지 시간 [s]"); ax[1].axhline(0, color="none")
ax[2].set_title("(c) 보행자-차체 최소 거리 [m]")
ax[3].set_title("(d) 보행자 접촉 사례 비율 [%]"); ax[3].set_ylim(0,105)
for a in ax:
    a.set_xticks(x); a.set_xticklabels([n for _,n in FAULTS], fontsize=9); a.grid(axis="y", alpha=0.3)
ax[0].legend(loc="upper center", bbox_to_anchor=(2.3,-0.18), ncol=2, frameon=False)
fig.suptitle("조우 블록: 고장 5 s 뒤 4 m/s 주행 중 8 m 앞 보행자 횡단 (교차로 30 m 전, 교통 def)", fontsize=11)
fig.tight_layout(rect=(0,0.05,1,0.95))
out = os.path.join(RES,"figs","fig_encounter.png"); os.makedirs(os.path.dirname(out), exist_ok=True); fig.savefig(out, dpi=140); print(out)
for (f,m),L in sorted(data.items()):
    print(f, m, len(L), "braked", sum(d["braked"] for d in L), "ped", sum(1 for d in L if d["ped"]>0), collections.Counter(d["out"] for d in L))
