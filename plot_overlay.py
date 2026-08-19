import csv, xml.etree.ElementTree as ET
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

def col(fn,xc,yc,flipy=False):
    xs,ys=[],[]
    for r in csv.DictReader(open(fn)):
        xs.append(float(r[xc])); ys.append(-float(r[yc]) if flipy else float(r[yc]))
    return xs,ys

# leaderboard scored route (CARLA)
lrx,lry=col("lb_route_keep.csv","x","y")
# ego actual path: gnss is ROS -> flip y to CARLA
ex,ey=[],[]
for r in csv.DictReader(open("ego_path.csv")):
    if r["src"]=="gnss": ex.append(float(r["x"])); ey.append(-float(r["y"]))
# sparse fixed waypoints
wps=[(float(p.get('x')),float(p.get('y'))) for p in ET.parse("resources/routes/town07_perimeter_fixed.xml").getroot().find('route').find('waypoints').findall('position')]

fig,axes=plt.subplots(1,2,figsize=(18,11))
for ax,zoom in [(axes[0],False),(axes[1],True)]:
    ax.plot(lrx,lry,color="crimson",lw=3,label="Leaderboard SCORED route (1m interp)",zorder=3,alpha=0.7)
    ax.plot(ex,ey,color="royalblue",lw=2,label="ACTUAL ego path",zorder=4)
    ax.scatter([p[0] for p in wps],[p[1] for p in wps],c="black",s=60,marker="s",label="your waypoints",zorder=5)
    ax.scatter([ex[0]],[ey[0]],c="lime",s=150,ec="black",label="spawn",zorder=6)
    ax.scatter([-201.49],[-130.1],c="orange",s=220,marker="X",ec="black",label="deviated",zorder=7)
    ax.set_aspect("equal"); ax.grid(True,ls=":",alpha=0.4); ax.legend(loc="upper right",fontsize=8)
    if zoom:
        ax.set_xlim(-215,-150); ax.set_ylim(-250,-100); ax.set_title("ZOOM @ deviation")
    else:
        ax.set_title("full")
fig.tight_layout(); fig.savefig("overlay.png",dpi=110); print("saved overlay.png")
