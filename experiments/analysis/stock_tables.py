import csv, collections, statistics as st
R = "/home/taewook/autoware_carla_leaderboard/experiments/results"
O = [r for r in csv.DictReader(open(f"{R}/stock_outcomes.csv")) if r["judge"] not in ("CARLA_DIED", "INTERRUPTED", "DRY")]
tags = {r["tag"] for r in O}
hit = collections.defaultdict(set)
for l in open(f"{R}/collision_live.log"):
    p = l.split()
    if len(p) < 4 or p[1] not in tags: continue
    t = p[3]
    c = "veh" if t.startswith("vehicle.") else "parked" if t in ("static.car", "static.truck", "static.bus", "static.motorcycle", "static.bicycle") else "ped" if t.startswith("walker.") else "static"
    hit[p[1]].add(c)
def fl(x):
    try: v = float(x); return v if v == v else None
    except: return None
def md(v):
    v = [x for x in v if x is not None]; return f"{st.median(v):.0f}" if v else "–"
FO = ["nf", "lf", "lso", "lcl", "cf", "cn", "gn", "imn", "gb", "gm", "imb", "imd"]
G = collections.defaultdict(list)
for r in O: G[(r["fault"], r["sev"])].append(r)
cls_order = ["drove_on", "stock_mrm", "frozen", "frozen_light", "crawl", "queued", "red_wait", "collision", "other"]
print("| fault | sev | n | " + " | ".join(cls_order) + " | deg med m | red-run cases | off-road | veh contact | parked-car | ped |")
print("|" + "---|" * (3 + len(cls_order) + 6))
tot = collections.Counter(); N = 0
for k in sorted(G, key=lambda k: (FO.index(k[0]) if k[0] in FO else 99, {"nf": 0, "mid": 1, "high": 2}.get(k[1], 3))):
    L = G[k]; c = collections.Counter(r["cls"] for r in L); N += len(L)
    for x in c: tot[x] += c[x]
    rr = sum(1 for r in L if (fl(r["red_light_runs"]) or 0) > 0); orr = sum(1 for r in L if r["off_road"] in ("1", "True", "1.0"))
    veh = sum(1 for r in L if "veh" in hit[r["tag"]]); pk = sum(1 for r in L if "parked" in hit[r["tag"]]); pd = sum(1 for r in L if "ped" in hit[r["tag"]])
    print(f"| {k[0]} | {k[1]} | {len(L)} | " + " | ".join(str(c.get(x, 0)) for x in cls_order) +
          f" | {md(fl(r['deg_dist_m']) for r in L)} | {rr} | {orr} | {veh} | {pk} | {pd} |")
print("total", N, dict(tot))
