import glob, os, re, collections, statistics as st, sys
import rosbag2_py
from rclpy.serialization import deserialize_message
from diagnostic_msgs.msg import DiagnosticArray
pats=[("1","stock-lcl-1_1000-def"),("2","stock-lcl-2_1100-def"),("5","stock-lcl-mid-def"),("10","stock-lcl-10_2100-def"),("15","stock-lcl-15_2750-def"),("25","stock-lcl-high-def"),("40","stock-lcl-40_5900-def"),("25-ours","lcl-25_4000-def")]
keys=["sensor/LIDAR_front","sector/F","sector/L","sector/R","sector/B","capability/obstacle","capability/perception"]
print("| rain | n | q 중앙 | q 최소 | q==0.2 비율 | q<0.199 비율 | F | L | R | B | obstacle | perception |")
for name,p in pats:
    bags=sorted(glob.glob(f"bags/{p}-r*"))[:6]; M=collections.defaultdict(list); fr_eq=[]; fr_lo=[]; mn=[]; n=0
    for b in bags:
        try:
            r=rosbag2_py.SequentialReader(); r.open(rosbag2_py.StorageOptions(uri=b,storage_id="mcap"),rosbag2_py.ConverterOptions("",""))
            r.set_filter(rosbag2_py.StorageFilter(topics=["/monitor/scores"]))
        except Exception: continue
        s=collections.defaultdict(list); seq=[]
        while r.has_next():
            _,d,_=r.read_next(); m=deserialize_message(d,DiagnosticArray); row={}
            for x in m.status:
                for kv in x.values:
                    k=x.name if kv.key in("score",) else None
                    if x.name=="sensor/LIDAR_front" and kv.key=="quality_score": row["q"]=float(kv.value)
                    elif kv.key=="score" and x.name in keys: row[x.name]=float(kv.value)
            seq.append(row)
        i=next((i for i,x in enumerate(seq) if x.get("q",1)<0.5 and i>50),None)
        if i is None: continue
        w=seq[i:]; q=[x["q"] for x in w if "q" in x]
        if len(q)<100: continue
        n+=1; fr_eq.append(sum(abs(v-.2)<.0005 for v in q)/len(q)); fr_lo.append(sum(v<.199 for v in q)/len(q)); mn.append(min(q)); M["q"].append(st.median(q))
        for k in keys[1:]: 
            v=[x[k] for x in w if k in x]
            if v: M[k].append(st.median(v))
    if n==0: print(name,"none"); continue
    f=lambda k:f"{st.median(M[k]):.2f}" if M[k] else "-"
    print(f"| {name} | {n} | {st.median(M['q']):.3f} | {min(mn):.3f} | {st.mean(fr_eq):.2f} | {st.mean(fr_lo):.2f} | {f('sector/F')} | {f('sector/L')} | {f('sector/R')} | {f('sector/B')} | {f('capability/obstacle')} | {f('capability/perception')} |")
