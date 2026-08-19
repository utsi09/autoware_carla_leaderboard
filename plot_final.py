import csv,xml.etree.ElementTree as ET
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
def lanelet(p):
    r=ET.parse(p).getroot(); nd={}
    for n in r.findall('node'):
        d={t.get('k'):t.get('v') for t in n.findall('tag')}
        if 'local_x' in d: nd[n.get('id')]=(float(d['local_x']),float(d['local_y']))
    L=[]
    for w in r.findall('way'):
        pts=[nd[a.get('ref')] for a in w.findall('nd') if a.get('ref') in nd]
        if len(pts)>=2: L.append(pts)
    return L
# lanelet local = (carla_x, -carla_y) -> draw in CARLA: (x, -y)
lines=lanelet('/home/taewook/awcl_maps/Town07/lanelet2_map.osm')
lr=[(float(r['x']),float(r['y'])) for r in csv.DictReader(open('lb_route_keep.csv'))]
ego=[(float(r['x']),-float(r['y'])) for r in csv.DictReader(open('ego_path.csv')) if r['src']=='gnss']
wps=[(float(p.get('x')),float(p.get('y'))) for p in ET.parse("resources/routes/town07_perimeter_fixed.xml").getroot().find('route').find('waypoints').findall('position')]
fig,ax=plt.subplots(figsize=(12,13))
for i,pl in enumerate(lines):
    ax.plot([p[0] for p in pl],[-p[1] for p in pl],color="0.85",lw=0.4,zorder=1,label="map" if i==0 else None)
ax.plot([p[0] for p in lr],[p[1] for p in lr],color="crimson",lw=2.5,label="따라가야 할 경로 (채점 루트)",zorder=3)
ax.plot([p[0] for p in ego],[p[1] for p in ego],color="royalblue",lw=2.5,label="실제 주행 궤적 (직전 기록 run)",zorder=4)
ax.scatter([p[0] for p in wps],[p[1] for p in wps],c="black",s=55,marker="s",label="너의 웨이포인트",zorder=5)
ax.scatter([ego[0][0]],[ego[0][1]],c="lime",s=160,ec="black",label="출발",zorder=6)
ax.scatter([ego[-1][0]],[ego[-1][1]],c="orange",s=160,marker="X",ec="black",label="기록 궤적 끝",zorder=6)
ax.set_aspect("equal"); ax.grid(True,ls=":",alpha=0.4); ax.legend(loc="upper right",fontsize=9)
ax.set_xlabel("x [m] CARLA"); ax.set_ylabel("y [m] CARLA")
ax.set_title("Town07: 채점 루트(빨강) vs 실제 궤적(파랑)")
fig.tight_layout(); fig.savefig("final.png",dpi=115); print("saved final.png")
