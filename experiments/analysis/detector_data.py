#!/usr/bin/env python3
"""검출기 비교 공용 로더. cells[(fault, sev, det)] = (k, n, [latencies...]) — fig_detector_matrix.py / fig_detector_compare.py 가 공유.
자료: baseline_fdi/cases.csv(항법·사망, 셀당 45), raw_vision/cases.csv(비전, 5), alibi/cases_v2_maxthr.csv(Online MMD nf-보정 문턱), RADAS 5런(report.md 수치)."""
import csv, os, collections
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
ROWS = [("lso", "mid", "LiDAR sparsification (mid)"), ("lso", "high", "LiDAR sparsification (high)"), ("lcl", "mid", "LiDAR clutter (mid)"), ("lcl", "high", "LiDAR clutter (high)"), ("lf", "mid", "LiDAR death"),
        ("cn", "mid", "Camera noise (mid)"), ("cn", "high", "Camera noise (high)"), ("cf", "mid", "Camera death"),
        ("gn", "mid", "GNSS position noise (mid)"), ("gn", "high", "GNSS position noise (high)"), ("gm", "mid", "GNSS correlated bias (mid)"), ("gm", "high", "GNSS correlated bias (high)"), ("gb", "mid", "GNSS outage"),
        ("imn", "mid", "IMU gyro noise (mid)"), ("imn", "high", "IMU gyro noise (high)"), ("imb", "mid", "IMU gyro bias (mid)"), ("imb", "high", "IMU gyro bias (high)"), ("imd", "mid", "IMU bias ramp (mid)"), ("imd", "high", "IMU bias ramp (high)")]
FAMILY = {"lso": "LiDAR\ndegradation", "lcl": "LiDAR\ndegradation", "lf": "LiDAR\ndeath", "cn": "Camera\ndegradation", "cf": "Camera\ndeath", "gn": "GNSS", "gm": "GNSS", "gb": "GNSS", "imn": "IMU", "imb": "IMU", "imd": "IMU"}
FAMILIES = ["LiDAR\ndegradation", "LiDAR\ndeath", "Camera\ndegradation", "Camera\ndeath", "GNSS", "IMU"]
DETS = [("ours", "Proposed"), ("b0", "Autoware diagnostics"), ("won", "Won 2023 (LiDAR bitmap)"), ("zh", "Zhang 2024 (LiDAR distribution)"), ("lee", "Lee 2022 (camera CNN)"),
        ("yu", "Yu 2021 (state χ²)"), ("gos", "Huang & Su (EKF residual)"), ("radas", "RADAS (stream rate)"), ("mmd", "Alibi online MMD")]

# 검출기가 실제로 소비하는 센서 계열(구조적 적용 범위). 여기 없는 계열은 평가했더라도 "볼 수 없음"(N/A) — 0 이 아니라 빗금.
ALL = set(FAMILIES)
APPLICABLE = {"ours": ALL, "b0": ALL, "radas": ALL, "mmd": ALL,
              "won": {"LiDAR\ndegradation", "LiDAR\ndeath"}, "zh": {"LiDAR\ndegradation", "LiDAR\ndeath"},
              "lee": {"Camera\ndegradation", "Camera\ndeath"},
              "yu": {"GNSS", "IMU", "LiDAR\ndeath"}, "gos": {"GNSS", "IMU", "LiDAR\ndeath"}}   # EKF 잔차 계열: NDT(라이다) 자세는 EKF 입력이라 라이다 사망은 적용, 카메라는 EKF 와 무관
def applicable(det, fault): return FAMILY[fault] in APPLICABLE[det]
def _f(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def load_cells():
    raw = collections.defaultdict(list)   # key -> list of latency-or-None
    for r in csv.DictReader(open(f"{RES}/baseline_fdi/cases.csv")):
        if not r["tag"].startswith("stock-") or r["sev"] not in ("mid", "high"): continue
        k = (r["fault"], r["sev"])
        raw[k + ("yu",)].append(_f(r["det_yu"])); raw[k + ("gos",)].append(_f(r["det_gos_all"])); raw[k + ("ours",)].append(_f(r["det_ours"]))
        if r.get("b0loc_avail") == "1": raw[k + ("b0",)].append(_f(r["det_b0_loc"]))
    for r in csv.DictReader(open(f"{RES}/raw_vision/cases.csv")):
        if r["fault"] == "nf": continue
        k = (r["fault"], r["sev"])
        raw[k + ("won",)].append(_f(r["det_won"])); raw[k + ("zh",)].append(_f(r["det_zh"])); raw[k + ("lee",)].append(_f(r["det_lee"])); raw[k + ("b0",)].append(_f(r["det_b0_perc"]))
        if k + ("ours",) not in raw or k[0] in ("lso", "lcl", "cn"): raw[k + ("ours",)].append(_f(r["det_ours"]))
    for r in csv.DictReader(open(f"{RES}/alibi/cases_v2_maxthr.csv")):
        if r["fault"] == "nf": continue
        raw[(r["fault"], r["sev"], "mmd")].append(_f(r["det"]))
    for f, s, det in (("lf", "mid", 3.8), ("cf", "mid", 2.4), ("lso", "high", None), ("gn", "high", None), ("imn", "mid", None)):
        raw[(f, s, "radas")].append(det)
    # ours for lso/lcl/cn: bag-replay cases in baseline_fdi are nav only; raw_vision rows give ours 5/cell — avoid double counting
    cells = {}
    for key, dets in raw.items():
        lat = [d for d in dets if d is not None]
        cells[key] = (len(lat), len(dets), lat)
    return cells
if __name__ == "__main__":
    c = load_cells()
    for (f, s, _l) in ROWS:
        print(f"{f}-{s}: " + "  ".join(f"{d}={c[(f, s, d)][0]}/{c[(f, s, d)][1]}" for d, _ in DETS if (f, s, d) in c))
