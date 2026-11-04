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
  frozen       신호·앞차 없이 100 s 이상 정지, MRM 없음
  crawl        고장 뒤 1 m/s 미만(적신호 제외) 누적 30 s 이상 + 2 m 이상 전진, 위 어디에도 안 들어감
  other        그 밖
부가 플래그: injected_at_standstill(주입 순간 정지 상태), stutter(정지→재출발 3회 이상), missed_green
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
    slow = [r for r in post if float(r["speed"]) < SLOW_V and r["tl"] != "R"]
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
    # stutter: 정지(2 s 이상) -> 재출발 횟수
    stops = 0; in_stop = 0
    for r in post:
        if float(r["speed"]) < STOP_V: in_stop += 1
        else:
            if in_stop >= 40: stops += 1
            in_stop = 0
    out["stop_go_cycles"] = stops
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
    elif t_stop and tl_stop in ("R", "Y") and missed_green:
        cls = "frozen_light"
    elif t_stop and tl_stop in ("R", "Y") and stopped_s < FROZEN_S:
        cls = "red_wait"
    elif t_stop and stopped_s >= FROZEN_S and tl_stop in ("-", "G", ""):
        cls = "frozen"
    elif t_stop and tl_stop in ("R", "Y"):
        cls = "red_wait"
    elif out["slow_s"] >= CRAWL_S and out["moved_m"] >= 2:
        cls = "crawl"
    else:
        cls = "other"
    if out.get("no_fault"): cls = "drove_on" if out["goal_dist_m"] <= 30 else cls
    out["cls"] = cls
    return out


def main():
    paths = sorted(glob.glob(str(RES / "gt" / "stock-*.csv")))
    if len(sys.argv) > 1:
        paths = [p for p in paths if any(a in p for a in sys.argv[1:])]
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
    print("| fault | sev | npc | n | " + " | ".join(order) + " | standstill-inj |")
    print("|" + "---|" * (4 + len(order) + 1))
    for (f, s, n), c in cond.items():
        st = sum(1 for r in rows if (r["fault"], r["sev"], r["npc"]) == (f, s, n) and r["injected_at_standstill"] == 1)
        print(f"| {f} | {s} | {n} | {sum(c.values())} | " + " | ".join(str(c.get(o, 0)) for o in order) + f" | {st} |")
    print(f"\n-> {RES/'stock_outcomes.csv'} ({len(rows)} cases)")


if __name__ == "__main__":
    main()
