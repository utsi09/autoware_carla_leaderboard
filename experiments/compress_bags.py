#!/usr/bin/env python3
"""[2026-11-08] bag 무손실 재압축: mcap 청크 zstd(storage preset zstd_fast). 읽는 쪽(rosbag2_py SequentialReader)은 그대로.
사용: compress_bags.py BAGS_DIR [--apply] [--limit N] [--min-age-min 60] [--only SUBSTR]
  각 bag → BAGS_DIR/.zstd_tmp/<name> 변환 → 원본과 메시지 전수 비교(토픽·형식 목록, 순서대로 (토픽, 시각, sha1(바이트)))
  --apply 일 때만, 완전히 같으면 원본을 새 것으로 교체(원본 삭제). 다르거나 오류면 원본 유지.
  최근 min-age 분 안에 바뀐 bag(기록·분석 중일 수 있음)은 건너뜀. 끝난 bag 은 BAGS_DIR/../bag_compress_done.txt 에 기록(재실행 시 skip).
"""
import sys, os, time, shutil, hashlib, subprocess, argparse
import rosbag2_py
ap = argparse.ArgumentParser(); ap.add_argument("bags"); ap.add_argument("--apply", action="store_true")
ap.add_argument("--limit", type=int, default=0); ap.add_argument("--min-age-min", type=float, default=60.0); ap.add_argument("--only", default="")
a = ap.parse_args()
B = os.path.abspath(a.bags); TMP = os.path.join(B, ".zstd_tmp"); os.makedirs(TMP, exist_ok=True)
LEDGER = os.path.join(os.path.dirname(B), "bag_compress_done.txt"); LOG = os.path.join(os.path.dirname(B), "bag_compress.log")
done = set(l.strip() for l in open(LEDGER)) if os.path.exists(LEDGER) else set()
def size(p): return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)
def reader(p):
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=p, storage_id="mcap"), rosbag2_py.ConverterOptions("", "")); return r
def same(p, q):
    r1, r2 = reader(p), reader(q)
    t1 = sorted((t.name, t.type) for t in r1.get_all_topics_and_types()); t2 = sorted((t.name, t.type) for t in r2.get_all_topics_and_types())
    if t1 != t2: return False, "topic list differs"
    n = 0
    while r1.has_next():
        if not r2.has_next(): return False, f"q shorter at {n}"
        x, y = r1.read_next(), r2.read_next()
        if x[0] != y[0] or x[2] != y[2] or hashlib.sha1(x[1]).digest() != hashlib.sha1(y[1]).digest():
            return False, f"msg {n} differs"
        n += 1
    if r2.has_next(): return False, "q longer"
    return True, n
def log(s):
    print(s, flush=True); open(LOG, "a").write(time.strftime("%F %T ") + s + "\n")
# 심볼릭 링크(/media/win_c 로 옮긴 bag)는 건너뜀 — rmtree 가 링크를 못 지워 배치가 죽었음(11/08 18:50)
names = sorted(d for d in os.listdir(B) if not d.startswith(".") and os.path.isdir(os.path.join(B, d)) and not os.path.islink(os.path.join(B, d)) and a.only in d)
k = 0; saved = 0
for nm in names:
    src = os.path.join(B, nm)
    if nm in done or not os.path.exists(os.path.join(src, "metadata.yaml")): continue
    if time.time() - max(os.path.getmtime(os.path.join(src, f)) for f in os.listdir(src)) < a.min_age_min * 60: continue
    if a.limit and k >= a.limit: break
    k += 1
    out = os.path.join(TMP, nm); shutil.rmtree(out, ignore_errors=True)
    yml = os.path.join(TMP, nm + ".yaml")
    open(yml, "w").write(f"output_bags:\n- uri: {out}\n  storage_id: mcap\n  storage_preset_profile: zstd_fast\n  all: true\n")
    s0 = size(src)
    r = subprocess.run(["ros2", "bag", "convert", "-i", src, "-o", yml], capture_output=True, text=True)
    os.remove(yml)
    if r.returncode != 0 or not os.path.isdir(out):
        log(f"FAIL convert {nm}: {r.stderr.strip().splitlines()[-1:]}"); shutil.rmtree(out, ignore_errors=True); continue
    ok, info = same(src, out); s1 = size(out)
    if not ok:
        log(f"FAIL verify {nm}: {info} — original kept"); shutil.rmtree(out, ignore_errors=True); continue
    if not a.apply:
        log(f"DRY ok {nm}: {info} msgs, {s0/1e6:.0f} MB -> {s1/1e6:.0f} MB"); shutil.rmtree(out, ignore_errors=True); saved += s0 - s1; continue
    old = os.path.join(TMP, nm + ".orig"); os.rename(src, old); os.rename(out, src); shutil.rmtree(old)
    open(LEDGER, "a").write(nm + "\n"); saved += s0 - s1
    log(f"OK {nm}: {info} msgs, {s0/1e6:.0f} MB -> {s1/1e6:.0f} MB")
log(f"summary: {k} bags, saved {saved/1e9:.2f} GB ({'applied' if a.apply else 'dry run'})")
