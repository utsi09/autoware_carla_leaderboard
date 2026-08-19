import csv,xml.etree.ElementTree as ET
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
lr=[(float(r['x']),float(r['y'])) for r in csv.DictReader(open('lb_route_keep.csv'))]
wps=[(float(p.get('x')),float(p.get('y'))) for p in ET.parse("resources/routes/town07_perimeter_fixed.xml").getroot().find('route').find('waypoints').findall('position')]
fig,ax=plt.subplots(figsize=(11,12))
# color lb_route by progress to see direction/order
xs=[p[0] for p in lr]; ys=[p[1] for p in lr]
ax.scatter(xs,ys,c=range(len(lr)),cmap='viridis',s=6,label='lb_route (color=progress)',zorder=3)
ax.plot([p[0] for p in wps],[p[1] for p in wps],'r--',lw=1,alpha=0.5,zorder=2)
for i,(x,y) in enumerate(wps):
    ax.scatter([x],[y],c='red',s=80,marker='s',zorder=4)
    ax.annotate(f"wp{i}",(x,y),fontsize=9,color='darkred',weight='bold')
ax.set_aspect('equal'); ax.grid(True,ls=':',alpha=0.4); ax.legend()
ax.set_title("Leaderboard SCORED route order (your waypoints in red)")
fig.tight_layout(); fig.savefig("lbroute.png",dpi=110); print("saved lbroute.png")
