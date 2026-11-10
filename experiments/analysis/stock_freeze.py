#!/usr/bin/env python3
"""순정(mrm-off) 매트릭스 결말 분류기 (계획: fs_failsafe/docs/stock_freeze_plan.md 5절).

입력: results/gt/stock-*.csv (GT 20 Hz, 신호등 열), results/bags/<tag> (Autoware MRM 상태), results/results_*.csv (judge 행)
출력: results/stock_outcomes.csv (케이스당 한 줄) + 조건별 분류 표(stdout, markdown)

분류 (우선순위 순):
  collision    judge 충돌(차량/보행자; 목적지 구조물 layout 만이면 제외)
  stock_mrm    고장 뒤 Autoware 자체 MRM 작동(/system/fail_safe/mrm_state OPERATING)
  drove_on     목적지 30 m 이내 도달(고장 난 채 완주)
  queued       최종 정지 때 앞 15 m 안에 정지/저속 차량
  frozen_light 신호 앞 정지 뒤 초록이 5 s 이상 켜졌는데도 못 출발
  red_wait     신호 앞 정지, 초록이 오기 전에 케이스 종료(판단 불가)
  crawl        고장→최종 정지 사이(적신호 정차 시간 제외) 30 s 이상이면서 평균 속도 < 1 m/s, 2 m 이상 전진 (정상 ≈ 1.3~2 m/s)
  frozen       신호·앞차 없이 서서 케이스 끝까지(≥60 s) 안 움직임, MRM 없음
  other        그 밖
부가 플래그: injected_at_standstill(주입 순간 정지 상태), stutter(정지→재출발 3회 이상), missed_green,
            xte_max/p95(정상 경로 이탈 m, 기준 = 같은 교통의 가장 긴 nf 궤적), off_road(이탈 > 3.5 m), yaw_rate_max(1 s 당 방향 변화 deg)
"""
import csv, glob, math, os, sys, collections
from pathlib import Path

RES = Path("/home/taewook/autoware_carla_leaderboard/experiments/results")
GOAL = (-102.0, 95.0)
STOP_V, SLOW_V, LEAD_M, FROZEN_S, CRAWL_S = 0.15, 1.0, 15.0, 100.0, 30.0


def mrm_after_fault(bag_dir):
    """고장 뒤 Autoware MRM 상태가 OPERATING(2) 이 된 시각(초, 고장 기준) 또는 None. bag 없으면 ''."""
    try:
        import rosbag2_py
        from rclpy.serialization import deserialize_message
        from rosidl_runtime_py.utilities import get_message
    except Exception:
        return ""
    if not (Path(bag_dir) / "metadata.yaml").exists():
        return ""
    r = rosbag2_py.SequentialReader()
    try:
        r.open(rosbag2_py.StorageOptions(uri=str(bag_dir), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
    except Exception:
        return ""
    f = rosbag2_py.StorageFilter(topics=["/fault_injection/active", "/system/fail_safe/mrm_state"])
    try:
        r.set_filter(f)
    except Exception:
        pass
    types = {t.name: t.type for t in r.get_all_topics_and_types()}
    tf = None; first = None
    while r.has_next():
        topic, data, t = r.read_next()
        if topic == "/fault_injection/active":
            if tf is None: tf = t
        elif topic == "/system/fail_safe/mrm_state" and tf is not None and t > tf:
            try:
                m = deserialize_message(data, get_message(types[topic]))
            except Exception:
                return ""
            if m.state == 2:
                first = (t - tf) * 1e-9; break
    return first


_REF = {}
def ref_path(npc):
    """기준 경로: 같은 교통의 가장 긴 nf(고장 없음) 자차 궤적을 0.2 m 간격 폴리라인으로."""
    if npc in _REF: return _REF[npc]
    import glob as _g
    cands = sorted(_g.glob(str(RES / "gt" / f"stock-nf-mid-{npc}-*.csv")),
                   key=lambda f: sum(1 for r in csv.DictReader(open(f, newline="")) if r["kind"] == "ego"))
    pts = []
    if cands:
        for r in csv.DictReader(open(cands[-1], newline="")):
            if r["kind"] != "ego": continue
            p = (float(r["x"]), float(r["y"]))
            if not pts or math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) > 0.2: pts.append(p)
    _REF[npc] = pts
    return pts


def xte(p, ref):
    """점 p 에서 기준 폴리라인까지 최단 거리 (경로 이탈량)."""
    best = 1e9
    for a, b in zip(ref, ref[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) if L > 0 else 0.0
        best = min(best, math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy)))
    return best


_LIVE = None
def live_metrics(fault, sev, npc, rep):
    """stock_matrix.log 의 [live] 줄(러너가 케이스 끝에 noise_capability 로 계산)에서 인지·측위 지표를 가져온다.
    열: idx fault sev rep outcome wall R_h R_far D_det FP S_front S_perc e_lat ATE NVTL ndt_hz s_loc n_pairs n_frames npc t_stop deg_dist lane_pct min_gap"""
    global _LIVE
    if _LIVE is None:
        _LIVE = {}
        p = RES / "stock_matrix.log"
        if p.exists():
            for ln in open(p, errors="replace"):
                if not ln.startswith("[live]"): continue
                f = [x.strip() for x in ln.split("|")[1:-1]]
                if len(f) < 24: continue
                _LIVE[(f[1], f[2], f[19], int(f[3]))] = dict(R_h=f[6], R_far=f[7], D_det=f[8], FP_s=f[9], S_front=f[10], S_perc=f[11],
                                                            e_lat_p95=f[12], ATE=f[13], NVTL=f[14], ndt_hz=f[15], n_pairs=f[17])
    return _LIVE.get((fault, sev, npc, rep), {})


def judge_row(fault, sev, npc, rep, stamp):
    """results_<stamp>.csv 의 해당 행"""
    p = RES / f"results_{stamp}.csv"
    if not p.exists():
        return {}
    for r in csv.DictReader(open(p, newline="")):
        if r["fault"] == fault and r["severity"] == sev and r["npc"] == npc and r["rep"] == str(rep):
            return r
    return {}


def analyse(gt_path):
    tag = Path(gt_path).stem                     # stock-<fault>-<sev>-<npc>-r<rep>-<MMDD_HHMM>
    parts = tag.split("-")
    fault, sev, npc = parts[1], parts[2], parts[3]
    rep = int(parts[4][1:]); stamp = parts[5]
    rows = list(csv.DictReader(open(gt_path, newline="")))
    by = collections.defaultdict(list)
    for r in rows:
        by[r["aw_sec"]].append(r)
    ego = [r for r in rows if r["kind"] == "ego"]
    post = [r for r in ego if r["fault"] == "1"]
    out = {"tag": tag, "fault": fault, "sev": sev, "npc": npc, "rep": rep}
    jr = judge_row(fault, sev, npc, rep, stamp)
    out["judge"] = jr.get("outcome", "")
    out["coll_types"] = jr.get("collision_types", "")
    out["deg_dist_m"] = jr.get("deg_dist_m", "")
    out["lane_pct"] = jr.get("lane_block_pct", "")
    out["min_gap_m"] = jr.get("min_gap_m", "")
    # [2026-11-08] 하네스 실패 제외: 출발 직후 Autoware 비상정지에서 못 풀려 한 번도 안 움직이고(최대 변위 < 1 m) 고장도 안 걸린 케이스
    if not post and ego and max(math.hypot(float(r["x"]) - float(ego[0]["x"]), float(r["y"]) - float(ego[0]["y"])) for r in ego) < 1.0:
        raise ValueError("harness flake (ego never moved, fault never injected) — excluded")
    if not post:                                  # nf 등 고장 없음
        post = ego[len(ego) // 2:]                # 후반부를 '고장 뒤' 대용으로
        out["no_fault"] = 1
    tf = float(post[0]["aw_sec"])
    out["t_fault"] = round(tf, 1)
    out["v_at_fault"] = float(post[0]["speed"]); out["tl_at_fault"] = post[0]["tl"]
    out["injected_at_standstill"] = "" if out.get("no_fault") else int(out["v_at_fault"] < STOP_V)
    sp = [float(r["speed"]) for r in post]
    out["post_s"] = round(len(post) / 20.0, 1)
    out["v_max"] = round(max(sp), 2); out["v_mean"] = round(sum(sp) / len(sp), 2)
    dist = 0.0
    for a, b in zip(post, post[1:]):
        dist += math.hypot(float(b["x"]) - float(a["x"]), float(b["y"]) - float(a["y"]))
    out["moved_m"] = round(dist, 1)
    # 기어감 판정용: 고장 → 최종 정지 사이('활동 구간')에서 적신호 대기(빨강+정지)를 뺀 시간과 이동 거리
    slow = [r for r in post if STOP_V <= float(r["speed"]) < SLOW_V and r["tl"] != "R"]
    out["slow_s"] = round(len(slow) / 20.0, 1)
    # 최종 정지
    t_stop = None
    for i in range(len(ego) - 1, -1, -1):
        if float(ego[i]["speed"]) > STOP_V:
            t_stop = ego[i + 1]["aw_sec"] if i + 1 < len(ego) else None; break
    last = ego[-1]
    out["goal_dist_m"] = round(math.hypot(float(last["x"]) - GOAL[0], float(last["y"]) - GOAL[1]), 1)
    out["final_stop_after_fault_s"] = round(float(t_stop) - tf, 1) if t_stop else ""
    stopped_s = (float(ego[-1]["aw_sec"]) - float(t_stop)) if t_stop else 0.0
    out["final_stopped_s"] = round(stopped_s, 1)
    tl_stop = ""; lead = None; rear = None; missed_green = 0
    if t_stop:
        e = [x for x in by[t_stop] if x["kind"] == "ego"]
        tl_stop = e[0]["tl"] if e else ""
        for x in by[t_stop]:
            if x["kind"] != "ego" and float(x["dist"]) < LEAD_M:
                b = float(x["bearing_deg"])
                if abs(b) < 25: lead = (float(x["dist"]), float(x["speed"]))
                elif abs(abs(b) - 180) < 30: rear = float(x["dist"])
        after = [x for x in ego if float(x["aw_sec"]) >= float(t_stop)]
        g = 0
        for x in after:
            g = g + 1 if x["tl"] == "G" else 0
            if g >= 100: missed_green = 1; break      # 초록 5 s 이상인데 안 움직임
    out["tl_at_stop"] = tl_stop; out["lead_m"] = lead[0] if lead else ""; out["rear_m"] = rear if rear else ""
    out["missed_green"] = missed_green
    # 활동 구간 평균 속도 (적신호 정차 시간 제외): 정상 주행 ≈ 1.3~2 m/s, 기어감 < 1 m/s
    act = [r for r in post if (float(r["aw_sec"]) < float(t_stop) if t_stop else True)]
    act_move = 0.0
    for a, b in zip(act, act[1:]):
        act_move += math.hypot(float(b["x"]) - float(a["x"]), float(b["y"]) - float(a["y"]))
    red_wait_s = sum(1 for r in act if r["tl"] == "R" and float(r["speed"]) < STOP_V) / 20.0
    act_s = max(0.0, len(act) / 20.0 - red_wait_s)
    out["active_s"] = round(act_s, 1); out["active_v_mean"] = round(act_move / act_s, 2) if act_s > 0 else ""
    is_crawl = act_s >= CRAWL_S and act_move >= 2 and act_move / act_s < SLOW_V
    # 이상 거동: 정상 경로에서 벗어난 거리(최대·P95; 정상 주행 ≤ 1.5 m, 차로 폭 3.5 m) 와 1 s 당 최대 방향 변화(정상 교차로 ≈ 20 deg)
    ref = ref_path(npc)
    if ref and not out.get("no_fault"):
        ev = sorted(xte((float(r["x"]), float(r["y"])), ref) for r in post[::4])
        out["xte_max_m"] = round(ev[-1], 1); out["xte_p95_m"] = round(ev[max(0, int(0.95 * len(ev)) - 1)], 1)
        out["off_road"] = int(ev[-1] > 3.5)
    else:
        out["xte_max_m"] = out["xte_p95_m"] = out["off_road"] = ""
    yaw = [float(r["yaw_deg"]) for r in post]
    out["yaw_rate_max_deg_s"] = round(max((abs((yaw[i + 20] - yaw[i] + 180) % 360 - 180) for i in range(0, len(yaw) - 20)), default=0), 1)
    # 신호 위반: 자차 신호가 R 인 구간(GT tl 열, 교차로 정지선 영역) 을 1 m/s 넘는 속도로 통과한 횟수
    red_runs = 0; in_r = []
    for r in post + [None]:
        if r is not None and r.get("tl", "-") == "R": in_r.append(float(r["speed"])); continue
        if in_r:
            if len(in_r) >= 10 and min(in_r) > 1.0: red_runs += 1          # 0.5 s 이상 빨강 구간을 한 번도 서지 않고 통과
            in_r = []
    out["red_light_runs"] = red_runs
    # [2026-11-05] 신호등 전수 기록(<tag>_tl.csv)이 있으면 정지선 기준으로 다시 센다:
    # 자차가 어떤 신호등의 정지선(2.5 m 안, 진행방향 ±45°)을 1 m/s 넘는 속도로 지나는 순간 그 신호등이 R 이면 위반 1회
    tlp = Path(gt_path).with_name(Path(gt_path).stem + "_tl.csv")
    if tlp.exists():
        try:
            stops = []; events = collections.defaultdict(list)
            for r in csv.DictReader(open(tlp, newline="")):
                if r["kind"] == "stop": stops.append((int(r["tl_id"]), float(r["x"]), float(r["y"]), float(r["yaw_deg"])))
                elif r["kind"] == "state": events[int(r["tl_id"])].append((float(r["aw_sec"]), r["state"]))
            def state_at(tl_id, t):
                st = "-"
                for ts_, s_ in events.get(tl_id, []):
                    if ts_ <= t: st = s_
                    else: break
                return st
            # [2026-11-05b] "통과" = 정지선을 실제로 넘는 순간(정지선 진행방향 좌표가 0 이하 -> 0 초과)으로만 센다.
            # 예전 2.5 m 반경 판정은 선 앞에서 멈추는 접근(감속 중 1~1.4 m/s)도 통과로 셌다 (cn-high none r7).
            runs = 0; crossed = set(); prev_along = {}
            for r in post:
                rx, ry, ryaw, rt = float(r["x"]), float(r["y"]), float(r["yaw_deg"]), float(r["aw_sec"])
                for (tid, sx, sy, syaw) in stops:
                    key = (tid, sx, sy)
                    if math.hypot(rx - sx, ry - sy) > 6.0:
                        prev_along.pop(key, None); continue
                    c_, s_ = math.cos(math.radians(syaw)), math.sin(math.radians(syaw))
                    along = (rx - sx) * c_ + (ry - sy) * s_            # + 면 정지선을 지나친 쪽
                    lat = -(rx - sx) * s_ + (ry - sy) * c_
                    pa = prev_along.get(key); prev_along[key] = along
                    if key in crossed or pa is None or not (pa <= 0.0 < along): continue
                    if abs(lat) > 3.5: continue
                    d = (ryaw - syaw + 180.0) % 360.0 - 180.0
                    if abs(d) > 45.0: continue
                    if float(r["speed"]) <= 1.0: continue                 # 선을 1 m/s 넘는 속도로 넘어야 통과
                    crossed.add(key)
                    if state_at(tid, rt) == "R": runs += 1
            out["red_light_runs_tl"] = runs; out["red_light_runs"] = runs      # 정지선 기준이 더 정확 → 덮어씀
            out["stoplines_crossed"] = len(crossed)
        except Exception as e:
            out["red_light_runs_tl"] = ""
    # stutter: 정지(2 s 이상) -> 재출발 횟수
    stops = 0; in_stop = 0
    for r in post:
        if float(r["speed"]) < STOP_V: in_stop += 1
        else:
            if in_stop >= 40: stops += 1
            in_stop = 0
    out["stop_go_cycles"] = stops
    out.update(live_metrics(fault, sev, npc, rep))
    mrm = mrm_after_fault(RES / "bags" / tag)
    out["aw_mrm_after_s"] = round(mrm, 1) if isinstance(mrm, float) else ""
    # 분류
    coll = out["coll_types"]
    if out["judge"] == "HAZARD_COLLISION" and coll and coll.replace("layout:1", "").strip("+") not in ("", ):
        cls = "collision"
    elif isinstance(mrm, float):
        cls = "stock_mrm"
    elif out["goal_dist_m"] <= 30:
        cls = "drove_on"
    elif t_stop and lead and lead[1] < 1.0:
        cls = "queued"
    elif is_crawl:
        cls = "crawl"                         # 활동 구간 평균 < 1 m/s 로 꾸물거림 (뒤에 굳었더라도 기어감으로 센다)
    elif t_stop and tl_stop in ("R", "Y") and missed_green:
        cls = "frozen_light"
    elif t_stop and tl_stop in ("R", "Y"):
        cls = "red_wait"                      # 초록이 오기 전에 케이스가 끝남 → 판단 불가
    elif t_stop and (out["judge"] == "HAZARD_STOPPED" or stopped_s >= 60) and tl_stop in ("-", "G", ""):
        cls = "frozen"                        # 신호·앞차 없이 서서 케이스 끝까지 안 움직임
    else:
        cls = "other"
    out["crawl_flag"] = int(is_crawl)
    out["frozen_flag"] = int(bool(t_stop) and stopped_s >= 60 and tl_stop in ("-", "G", "") and out["goal_dist_m"] > 30)
    if out.get("no_fault"): cls = "drove_on" if out["goal_dist_m"] <= 30 else cls
    out["cls"] = cls
    return out


def main():
    paths = [p for p in sorted(glob.glob(str(RES / "gt" / "stock-*.csv"))) if not p.endswith("_tl.csv")]
    if len(sys.argv) > 1:
        paths = [p for p in paths if any(a in p for a in sys.argv[1:])]
    # 같은 셀을 두 번 돌린 경우(중단·재실행) 가장 최근 파일만 (파일명 끝 stamp 가 시간순)
    latest = {}
    for p in paths:
        latest["-".join(Path(p).stem.split("-")[:5])] = p
    paths = sorted(latest.values())
    rows = []
    for p in paths:
        try:
            rows.append(analyse(p))
        except Exception as e:
            print("[fail]", Path(p).stem, e, file=sys.stderr)
    if not rows: return
    keys = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(RES / "stock_outcomes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    order = ["drove_on", "queued", "red_wait", "stock_mrm", "frozen", "frozen_light", "crawl", "collision", "other"]
    cond = collections.OrderedDict()
    for r in rows:
        cond.setdefault((r["fault"], r["sev"], r["npc"]), collections.Counter())[r["cls"]] += 1
    print("| fault | sev | npc | n | " + " | ".join(order) + " | standstill-inj | red-light runs (cases/events) |")
    print("|" + "---|" * (4 + len(order) + 2))
    for (f, s, n), c in cond.items():
        st = sum(1 for r in rows if (r["fault"], r["sev"], r["npc"]) == (f, s, n) and r["injected_at_standstill"] == 1)
        rr = [r.get("red_light_runs", 0) for r in rows if (r["fault"], r["sev"], r["npc"]) == (f, s, n)]
        print(f"| {f} | {s} | {n} | {sum(c.values())} | " + " | ".join(str(c.get(o, 0)) for o in order) + f" | {st} | {sum(1 for x in rr if x)}/{sum(rr)} |")
    def fnum(x):
        try: return float(x)
        except Exception: return None
    def mean(xs):
        xs = [x for x in xs if x is not None]; return (sum(xs) / len(xs)) if xs else None
    def fmt(x, d=1): return "–" if x is None else f"{x:.{d}f}"
    print("\n증거 표 (조건별 평균; 유효 케이스만)")
    print("| fault | sev | npc | n | 고장 뒤 주행 m | 근거리 검출 | 원거리 검출 | 첫 검출 m | 경로 이탈 max m | 도로 이탈 n | 최대 yaw deg/s | 굳음 n | 기어감 n | MRM 지연 s |")
    print("|" + "---|" * 14)
    for (f, sv, n_), c in cond.items():
        rr = [r for r in rows if (r["fault"], r["sev"], r["npc"]) == (f, sv, n_) and r["judge"] not in ("CARLA_DIED", "SETUP_FAIL", "")]
        if not rr: continue
        print(f"| {f} | {sv} | {n_} | {len(rr)} | {fmt(mean([fnum(r['deg_dist_m']) for r in rr]),0)} | {fmt(mean([fnum(r.get('R_h')) for r in rr]),2)} | {fmt(mean([fnum(r.get('R_far')) for r in rr]),2)} | "
              f"{fmt(mean([fnum(r.get('D_det')) for r in rr]),0)} | {fmt(mean([fnum(r['xte_max_m']) for r in rr]))} | {sum(1 for r in rr if r['off_road'] == 1)} | {fmt(mean([fnum(r['yaw_rate_max_deg_s']) for r in rr]),0)} | "
              f"{sum(1 for r in rr if r['cls'] in ('frozen', 'frozen_light'))} | {sum(1 for r in rr if r['cls'] == 'crawl')} | {fmt(mean([fnum(r['aw_mrm_after_s']) for r in rr]),0)} |")
    print(f"\n-> {RES/'stock_outcomes.csv'} ({len(rows)} cases)")


if __name__ == "__main__":
    main()
