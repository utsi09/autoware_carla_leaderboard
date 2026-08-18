# -*- coding: utf-8 -*-
# round 6: ch2/ch3 3행 고아 꼬리 제거
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = []


def op(fname, anchor, old, new):
    OPS.append((fname, anchor, old, new))


# ---------------- 2장 ----------------
op('content1.py', "표 2-1은 관련 연구 계열을 여섯 개 축(고장 감지",
   "표 2-1은 관련 연구 계열을 여섯 개 축(고장 감지, 연속 건강도, 잔여능력 평가, 단계적 MRM 선택, 속도 제한 이동, 조우 수준 폐루프 실증)으로 본 연구와 비교한다.",
   "표 2-1은 관련 연구 계열을 여섯 개 축으로 본 연구와 비교한다.")
op('content1.py', "AWCL[52](TUM 공개; C++ 브리지·차량 디지털트윈·Town07 지도 자산)",
   "AWCL[52](TUM 공개; C++ 브리지·차량 디지털트윈·Town07 지도 자산)",
   "AWCL[52](TUM 자동차공학연구소 공개)")
op('content1.py', "['센서 열화 모델·정량화 [20-29][53-59]'",
   "'센서 열화 모델·정량화 [20-29][53-59]'",
   "'센서 열화 모델 [20-29][53-59]'")
op('content1.py', "본 연구의 위치는 개별 축의 새 알고리즘이 아니라 이 통합",
   "본 연구의 위치는 개별 축의 새 알고리즘이 아니라 이 통합 — 감지부터 선택·속도까지의 감독 계층 — 과 그 실증에 있다.",
   "본 연구의 위치는 개별 축의 새 알고리즘이 아니라 감지부터 선택·속도까지의 통합 감독 계층과 그 실증에 있다.")

# ---------------- 3장 ----------------
op('content2.py', "식 (3-6)의 τ_fresh와 min(·, TTC_cons)는",
   "식 (3-6)의 τ_fresh와 min(·, TTC_cons)는 식 (3-1)의 신선도 점수 감쇠에 쓰이는 시간상수이며, TTC가 짧아질수록 감쇠를 조여 같은 수신 공백에도 점수가 더 빨리 떨어지게 — 위험에 근접할수록 감지 기준을 보수적으로 강화하게 — 하는 구현이다.",
   "식 (3-6)의 τ_fresh와 min(·, TTC_cons)는 식 (3-1)의 신선도 감쇠 시간상수이며, TTC가 짧아질수록 감쇠를 조여 위험에 근접할수록 감지 기준을 보수적으로 강화하는 구현이다.")
op('content2.py', "이중 임계는 채터링 방지와 등급 구분을 겸하며",
   "이중 임계는 채터링 방지와 등급 구분을 겸하며, 고장 시 능력 점수와 정상 주행 점수 사이에 넓은 무감 구간이 존재하도록 채널 감쇠 상수를 설계했으므로, 임계의 미세 위치보다 두 임계가 만드는 3구간 구조(정상/대피/위임)가 거동을 결정한다.",
   "이중 임계는 채터링 방지와 등급 구분을 겸하며, 고장 시 점수와 정상 점수 사이에 넓은 무감 구간이 있도록 감쇠 상수를 설계했으므로 임계의 미세 위치보다 3구간 구조(정상/대피/위임)가 거동을 결정한다.")
op('content2.py', "실효 감속도 a≈3.5 m/s²와 함께 대입하면",
   "실효 감속도 a≈3.5 m/s²와 함께 대입하면 제한속도 주행(v=4.2 m/s)의 필요 거리는 8.82 m, v=3.0 m/s의 필요 거리는 5.79 m이다(d_margin=0 기준).",
   "실효 감속도 a≈3.5 m/s²로 제한속도 주행(v=4.2 m/s)의 필요 거리는 8.82 m, v=3.0 m/s는 5.79 m이다(d_margin=0).")
op('content2.py', "MRM_MOVE에서는 대피 목표 지점(pose)을 AD API",
   "MRM_MOVE에서는 대피 목표 지점(pose)을 AD API 경로 재설정으로 전달하고",
   "MRM_MOVE에서는 대피 목표를 AD API 경로 재설정으로 전달하고")


def apply():
    byfile = {}
    for fname, anchor, old, new in OPS:
        byfile.setdefault(fname, []).append((anchor, old, new))
    for fname, ops in byfile.items():
        path = os.path.join(HERE, fname)
        with open(path, encoding='utf-8') as f:
            lines = f.read().split('\n')
        for anchor, old, new in ops:
            hits = [i for i, l in enumerate(lines) if anchor in l]
            assert len(hits) == 1, f'{fname}: anchor {len(hits)} != 1: {anchor[:50]}'
            i = hits[0]
            assert lines[i].count(old) == 1, f'{fname}: sub != 1: {old[:50]}'
            lines[i] = lines[i].replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f'{fname}: {len(ops)} ops applied')


if __name__ == '__main__':
    apply()
    sys.path.insert(0, HERE)
    import importlib
    for m in ['content1', 'content2', 'content3']:
        importlib.import_module(m)
    print('syntax OK')
