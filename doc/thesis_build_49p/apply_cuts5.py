# -*- coding: utf-8 -*-
# round 5: 3~4행 고아 꼬리쪽 제거 (ch2/ch3/ch6)
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = []


def op(fname, kind, anchor, payload=None):
    OPS.append((fname, kind, anchor, payload))


# ---------------- 2장 ----------------
op('content1.py', 'sub', "Xue 등[49][50]은 전방 센서 고장을 전제로 MPC 안전 제약 하에",
   ("Xue 등[49][50]은 전방 센서 고장을 전제로 MPC 안전 제약 하에 지정 안전 구역까지 차로를 이탈·정차하는 폴백과, 미관측 영역에 가상 차량을 두는 적응형 MPC 확장을 제안했다. Tang 등[48]은 복수 센서 고장 조건에서 HAZOP 기반 위험 분석과 가상 객체·TTC·THW 평가로 MRM 행동(감속, 차로 유지 정차, 갓길 지향 정차 등)을 실시간 적응 선택하며 MATLAB-CARLA 폐루프로 검증했다.",
    "Xue 등[49][50]은 전방 센서 고장을 전제로 MPC 안전 제약 하의 안전 구역 정차 폴백과 미관측 영역 가상 차량 기반 적응형 MPC 확장을, Tang 등[48]은 복수 센서 고장에서 HAZOP 위험 분석과 가상 객체·TTC·THW 평가로 MRM 행동(감속, 차로 유지 정차, 갓길 지향 정차 등)을 적응 선택하는 방법을 제안하고 MATLAB-CARLA 폐루프로 검증했다."))
op('content1.py', 'sub', "런타임 모니터 사례[37]·모니터 합성 SMOF[38]·검증 난제 정리[39]",
   ("런타임 모니터 사례[37]·모니터 합성 SMOF[38]·검증 난제 정리[39]가 인접 계열이고",
    "런타임 모니터 사례[37]·SMOF[38]·검증 난제[39]가 인접 계열이고"))

# ---------------- 3장 ----------------
op('content2.py', 'sub', "신호등 관측성 게이트가 핵심 안전장치이다: 경로상 신호등을 관측할 수 있는",
   ("신호등 관측성 게이트가 핵심 안전장치이다: 경로상 신호등을 관측할 수 있는 건강한 카메라가 없으면 해당 후보는 J = ∞로 배제되며, 신호등 상태의 취득원은 고장 유형을 인지해 선택한다(카메라 고장 케이스가 아니면 V2X 릴레이, 카메라 고장 시 해당 경로 배제 우선).",
    "신호등 관측성 게이트가 핵심 안전장치이다: 경로상 신호등을 관측할 건강한 카메라가 없으면 해당 후보는 J = ∞로 배제되며, 신호등 상태 취득원은 고장 유형을 인지해 선택한다(카메라 고장이 아니면 V2X 릴레이, 카메라 고장 시 경로 배제 우선)."))
op('content2.py', 'sub', "이 τ는 센서 고장의 감지 지연(4절의 T_detect)과는",
   ("이 τ는 센서 고장의 감지 지연(4절의 T_detect)과는 별개의 개념이다.",
    "이 τ는 고장 감지 지연(4절의 T_detect)과는 별개 개념이다."))
op('content2.py', 'sub', "— 갓길 진입 기동 자체는 순정 goal_planner의 기능이며 본 연구는 이를 수정하지 않았다",
   ("— 갓길 진입 기동 자체는 순정 goal_planner의 기능이며 본 연구는 이를 수정하지 않았다",
    "— 갓길 진입 기동 자체는 순정 goal_planner의 기능으로 본 연구는 수정하지 않았다"))
op('content2.py', 'sub', "수동 주석은 검증 범위를 주석 구간으로 한정하며, 확장성 한계와",
   ("수동 주석은 검증 범위를 주석 구간으로 한정하며, 확장성 한계와 자동 추출 대안은 제6장에서 논한다.",
    "수동 주석은 검증 범위를 주석 구간으로 한정한다(확장성 한계와 자동 추출 대안은 제6장)."))
op('content2.py', 'sub', "fig_bt_structure.png', None, 12.5),",
   ("fig_bt_structure.png', None, 12.5),", "fig_bt_structure.png', None, 12.0),"))

# ---------------- 6장 ----------------
op('content3.py', 'sub', "관찰된 기전은 상한의 역할을 재정의한다: 대피 기동은 자연 저속화되므로",
   ("관찰된 기전은 상한의 역할을 재정의한다: 대피 기동은 자연 저속화되므로 정상적인 대피에서 상한은 거의 구속되지 않으며, 상한의 가치는 자연 감속에 의존하지 않는 명시적 재가속 억제 상계(재가속 시 열화 상태의 속도 상승을 막는 상계 명령)에 있다.",
    "관찰된 기전은 상한의 역할을 재정의한다: 대피 기동은 자연 저속화되어 정상 대피에서 상한은 거의 구속되지 않으며, 상한의 가치는 자연 감속에 의존하지 않는 명시적 재가속 억제 상계에 있다."))
op('content3.py', 'sub', "특히 \"기록의 부재\"를 \"사건의 부재\"로 읽는 오류는 자동화 대량 실험에서 구조적으로 발생하기 쉬우며, 실시간 원장(사건 즉시",
   ("특히 \"기록의 부재\"를 \"사건의 부재\"로 읽는 오류는 자동화 대량 실험에서 구조적으로 발생하기 쉬우며, 실시간 원장(사건 즉시, 종료 방식과 무관하게 기록)이 실효적 해법이었다.",
    "특히 \"기록의 부재\"를 \"사건의 부재\"로 읽는 오류는 자동화 대량 실험에서 구조적으로 발생하기 쉬우며, 실시간 원장이 실효적 해법이었다."))
op('content3.py', 'sub', "신호등 관측성 게이트는 안전 원칙(\"신호를 읽지 못하는 차량을",
   ("신호등 관측성 게이트는 안전 원칙(\"신호를 읽지 못하는 차량을 신호 교차로 경유 후보에 보내지 않는다\")의 구현이지만 카메라 계열 고장에서 후보 집합을 줄여 대피 완료 비율(cf 16/45)을 제한한다",
    "신호등 관측성 게이트(\"신호를 읽지 못하는 차량을 신호 교차로 경유 후보에 보내지 않는다\")는 카메라 계열 고장에서 후보 집합을 줄여 대피 완료 비율(cf 16/45)을 제한한다"))
op('content3.py', 'sub', "(감시자를 감시하라는 원칙은 실험 인프라에도 적용된다)",
   ("(감시자를 감시하라는 원칙은 실험 인프라에도 적용된다)",
    "(감시자를 감시하라)"))
op('content3.py', 'sub', "본 표본에서 차로 내 정지는 과도구간 발사라는 최악 조건에서도 가장 낮은 충돌률을 보였다",
   ("본 표본에서 차로 내 정지는 과도구간 발사라는 최악 조건에서도 가장 낮은 충돌률을 보였다(제5장 5절). 그러나 그 대가는 차선 점유의 지속이며(제5장 2절),",
    "본 표본에서 차로 내 정지는 과도구간 발사라는 최악 조건에서도 가장 낮은 충돌률을 보였으나(제5장 5절) 그 대가는 차선 점유의 지속이며(제5장 2절),"))


def apply():
    byfile = {}
    for fname, kind, anchor, payload in OPS:
        byfile.setdefault(fname, []).append((kind, anchor, payload))
    for fname, ops in byfile.items():
        path = os.path.join(HERE, fname)
        with open(path, encoding='utf-8') as f:
            lines = f.read().split('\n')
        for kind, anchor, payload in ops:
            hits = [i for i, l in enumerate(lines) if anchor in l]
            assert len(hits) == 1, f'{fname}: anchor match {len(hits)} != 1: {anchor[:60]}'
            i = hits[0]
            old, new = payload
            assert lines[i].count(old) == 1, f'{fname}: sub count != 1: {old[:60]}'
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
