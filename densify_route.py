import math, xml.etree.ElementTree as ET

SRC="resources/routes/town07_perimeter_fixed.xml"
DST="resources/routes/town07_perimeter_dense.xml"
STEP=15.0  # m

tree=ET.parse(SRC); root=tree.getroot(); route=root.find('route')
wpe=route.find('waypoints')
wps=[(float(p.get('x')),float(p.get('y')),float(p.get('z'))) for p in wpe.findall('position')]

# densify by linear interpolation, max spacing STEP
dense=[]
for i in range(len(wps)-1):
    x0,y0,z0=wps[i]; x1,y1,z1=wps[i+1]
    d=math.hypot(x1-x0,y1-y0)
    n=max(1,int(d//STEP))
    for k in range(n):
        t=k/n
        dense.append((x0+(x1-x0)*t, y0+(y1-y0)*t, z0+(z1-z0)*t))
dense.append(wps[-1])

# verify nearest lanelet road (lanelet local = (carla_x, -carla_y))
r=ET.parse('/home/taewook/awcl_maps/Town07/lanelet2_map.osm').getroot()
nodes=[]
for n in r.findall('node'):
    dd={t.get('k'):t.get('v') for t in n.findall('tag')}
    if 'local_x' in dd: nodes.append((float(dd['local_x']),float(dd['local_y'])))
def nearest(cx,cy):
    lx,ly=cx,-cy
    return min(math.hypot(lx-x,ly-y) for x,y in nodes)
ds=[nearest(x,y) for x,y,_ in dense]
print(f"original wp={len(wps)} -> dense wp={len(dense)} (step {STEP}m)")
print(f"nearest-road dist: avg {sum(ds)/len(ds):.1f}m  max {max(ds):.1f}m")
bad=[(i,round(dense[i][0],1),round(dense[i][1],1),round(ds[i],1)) for i in range(len(ds)) if ds[i]>8]
print(f"points >8m off road: {len(bad)}", bad[:8])

# write new file
for p in list(wpe): wpe.remove(p)
for x,y,z in dense:
    e=ET.SubElement(wpe,'position'); e.set('x',f"{x:.4f}"); e.set('y',f"{y:.4f}"); e.set('z',f"{z:.2f}")
ET.indent(tree, space="    ")
tree.write(DST, encoding="UTF-8", xml_declaration=True)
print("wrote",DST)
