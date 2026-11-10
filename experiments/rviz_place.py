#!/usr/bin/env python3
"""RViz 창을 지정 위치로 옮기고 '항상 위' (_NET_WM_STATE_ABOVE) 로 올린다 — x11grab 영역 캡처가 다른 창(터미널)에 가려지는 사고 방지(2026-11-09).
사용: rviz_place.py <window_id(int)> <x> <y>"""
import sys, os
os.environ.setdefault("DISPLAY", ":0")
from Xlib import display, X, protocol
wid, x, y = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
d = display.Display(":0"); root = d.screen().root; w = d.create_resource_object("window", wid)
# 프레임이 있으면 WM 이 재배치하므로 _NET_MOVERESIZE_WINDOW 로 요청
NET_MR = d.intern_atom("_NET_MOVERESIZE_WINDOW"); NET_STATE = d.intern_atom("_NET_WM_STATE"); ABOVE = d.intern_atom("_NET_WM_STATE_ABOVE")
grav_flags = (1 << 8) | (1 << 9) | (X.NorthWestGravity)   # x,y 지정
ev = protocol.event.ClientMessage(window=w, client_type=NET_MR, data=(32, [grav_flags, x, y, 0, 0]))
root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
ev2 = protocol.event.ClientMessage(window=w, client_type=NET_STATE, data=(32, [1, ABOVE, 0, 1, 0]))   # 1 = _NET_WM_STATE_ADD, source 1
root.send_event(ev2, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
try: w.configure(x=x, y=y)
except Exception: pass
d.flush(); d.sync()
g = w.get_geometry(); t = w.translate_coords(root, 0, 0)
print(f"placed wid={wid} at root({-t.x},{-t.y}) size {g.width}x{g.height}")
