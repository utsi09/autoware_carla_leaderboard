import lanelet2
from lanelet2.projection import LocalCartesianProjector
from lanelet2.core import BasicPoint2d
from lanelet2 import traffic_rules, routing
proj = LocalCartesianProjector(lanelet2.io.Origin(0, 0, 0))
m = lanelet2.io.load("/home/taewook/awcl_maps/Town07/lanelet2_map.osm", proj)
tr = traffic_rules.create(traffic_rules.Locations.Germany, traffic_rules.Participants.Vehicle)
rg = routing.RoutingGraph(m, tr)
def near(x, y, n=4):
    return lanelet2.geometry.findNearest(m.laneletLayer, BasicPoint2d(x, y), n)
print("--- near goal (-42.2, 69.4):")
for d, ll in near(-42.2, 69.4):
    sub = ll.attributes["subtype"] if "subtype" in ll.attributes else "?"
    print("  ll", ll.id, "d=%.1f" % d, sub)
ego = near(-94.5, 3.3, 1)[0][1]
print("--- ego ll", ego.id)
for d, ll in near(-42.2, 69.4):
    r = rg.getRoute(ego, ll)
    print("  route ego ->", ll.id, ":", ("OK %.0fm" % r.length2d()) if r else "NONE")
# 회랑 체인 연결 상태
for lid in [1002570, 1002575, 1002580, 1271]:
    ll = m.laneletLayer.get(lid)
    prev = rg.previous(ll); nxt = rg.following(ll)
    print("ll", lid, "prev", [p.id for p in prev], "next", [p.id for p in nxt],
          "left", getattr(rg.left(ll), "id", None), "right", getattr(rg.right(ll), "id", None))
