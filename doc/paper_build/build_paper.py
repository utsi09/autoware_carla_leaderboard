# -*- coding: utf-8 -*-
"""Paper builder (0826): KO + EN versions from the slide-15+ figure set.
Figures are embedded as-is (no recompression); fig5 is the d78cf4f scene panels.
Outputs doc/paper_ko_0826.docx / doc/paper_en_0826.docx (+pdf via soffice)."""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, 'figs')
OUTDIR = os.path.dirname(HERE)

# ---------------------------------------------------------------- content: EN
EN = []
EN.append(('title', 'Graded Fault Response for Autonomous Driving via Behavior-Tree-based Sensor Health Monitoring and Risk/Capability-aware MRM Supervision'))
EN.append(('author', '○○○\nDepartment of Electrical and Computer Engineering, Sungkyunkwan University'))
EN.append(('h1', 'Abstract'))
EN.append(('abs', 'Sensor-fault handling in automated driving stacks largely reduces to a single strategy — an immediate in-lane stop — which leaves the vehicle obstructing live traffic, while undetected faults let it keep driving on degraded perception. This paper presents a graded fault-response framework composed of a behavior-tree monitor that estimates per-sensor health as continuous scores from freshness, quality, and physics channels, and a supervisor that selects between shoulder/parking-lot evacuation and deferral to the stock in-lane stop according to fault type, severity, and remaining capability, enforcing a 3.0 m/s speed cap during evacuation. The framework runs as an add-on to an unmodified Autoware 0.39.0 stack in closed loop with CARLA 0.9.16. Across 1,131 valid cases the detector reached 96–100% detection with 2.1–5.0 s median latency in 11 of 12 fault conditions and zero false activations in 45 fault-free cases, and supervision cut degraded-state driving exposure from 238–275 m to 32–58 m. Complete sensor silence is decided through a hard-fail fast path that met a 1.5 s detection-to-decision deadline in every case (max 1.20 s). A paired four-arm ablation with a standardized pedestrian dart-out shows that the choice between stopping and evacuating is a temporal trade-off: residual evacuation risk concentrates in the deceleration transient (11/20), while the same policy in settled cruise avoided all encounters (0/8). A supplementary campaign extended the fault model to correlated GNSS bias, GNSS outage, and IMU bias/drift (611 valid cases, 100% detection).'))
EN.append(('kw', 'Keywords: autonomous driving, functional safety, minimal risk maneuver, FTTI, sensor fault detection, behavior tree'))

EN.append(('h1', '1. Introduction'))
EN.append(('p', 'Production-grade automated driving stacks ship with a minimal-risk-maneuver (MRM) repertoire that, in practice, collapses to one behavior: when a fault is severe enough to be noticed, stop in the current lane. This single strategy has two failure modes at opposite ends of the severity spectrum. When it fires, the vehicle becomes a stationary obstacle in a live lane, exposing following traffic to a hazard the stop was meant to remove; when it does not fire — because the fault degrades perception without tripping a binary diagnostic — the vehicle simply keeps driving with senses it no longer has. Figure 1 illustrates the setting: a vehicle that detects a sensor fault on a two-lane rural road usually has better options than its own lane, including adjacent free space, a parking lot, or a downstream shoulder, but exploiting them requires knowing how much capability remains and whether the maneuver itself is still safe, including against edge cases such as a pedestrian darting out during the evacuation.'))
EN.append(('fig', 'fig1_problem.png', 14.5, 'Fig. 1. Problem setting: graded refuge options upon a sensor fault (a) and the pedestrian dart-out edge case during evacuation (b). Candidates are ranked by a cost function.'))
EN.append(('p', 'We propose a graded fault-response framework built from two cooperating components: a behavior-tree monitor (CDR Monitor) that turns raw sensor streams into continuous per-sensor and per-sector health scores, and a supervisor (MRM Supervisor) that maps the monitored condition to one of five responses — continue, shoulder stop, parking-lot stop, in-lane stop, or emergency stop — using dual health thresholds and a time-denominated cost function over pre-annotated refuge candidates. The framework attaches to an unmodified Autoware stack through read-only topic subscriptions and the standard AD API and diagnostics interfaces, so the nominal driving channel is never altered.'))
EN.append(('p', 'The contributions are: (1) a monitoring design that produces graded health estimates rather than binary faults, with an evidence-aware fast path that decides complete sensor silence within a 1.5 s deadline; (2) a capability-aware MRM selection policy with an explicit quality ordering over minimal-risk conditions and a conservative 3.0 m/s evacuation speed cap derived from a stopping-distance model; (3) a closed-loop evaluation of 1,131 valid cases plus a 611-case supplementary campaign over an eleven-type physics-grounded fault model; and (4) an empirical characterization of the stop-versus-evacuate trade-off, including a two-regime analysis showing that evacuation risk concentrates in the detection-to-deceleration transient.'))

EN.append(('h1', '2. Related Work'))
EN.append(('p', 'Autoware [1] provides in-lane MRMs (comfortable and emergency stop) triggered by its diagnostics graph, but offers no built-in notion of evacuating to a refuge, and its fault handling is binary. Standards frame the requirements we target: ISO 26262 [4] demands a bounded time to a safe state and defines the fault-tolerant time interval (FTTI); UNECE Regulation No. 157 [6] requires an MRM that ends in a standstill with risk minimized during the maneuver; ISO 23793-1 [5] classifies MRM types for low-speed automated driving, distinguishing in-lane stops from maneuvers to safer stopping positions; SAE J3016 [7] defines the minimal risk condition (MRC) the maneuver must reach. Our policy operationalizes these concepts as an explicit, testable selection matrix. The fault model draws on the LiDAR degradation literature: the fault taxonomy of Goelles et al. [8], measured rain attenuation and clutter models [9, 10], adverse-weather point-cloud simulation [11, 12], and measured cover-soiling effects [13]. The experimental infrastructure builds on CARLA [2], the Autoware–CARLA leaderboard integration of Kaljavesi et al. [3], and a custom Town07 lanelet2 map annotated with refuge candidates.'))

EN.append(('h1', '3. System Design'))
EN.append(('h2', '3.1 Architecture'))
EN.append(('p', 'Figure 2 shows the architecture. The CARLA server feeds a bridge that converts sensor topics for the Autoware stack; sensor faults are injected inside this bridge conversion layer, so the faulted data reaches the nominal stack and the proposed supervision layer identically. The CDR Monitor subscribes read-only to the same sensor topics and publishes health scores at 10 Hz; the MRM Supervisor consumes the scores and, when intervention is warranted, acts on the stack only through public interfaces — a reroute request with a speed cap for evacuation (MOVE), or an injected diagnostic ERROR that delegates to the stock in-lane stop (DEFER). Autoware itself runs unmodified.'))
EN.append(('fig', 'fig2_arch.png', 14.0, 'Fig. 2. System architecture. The proposed supervision layer (CDR Monitor and MRM Supervisor) attaches to an unmodified Autoware stack; faults are injected in the bridge, upstream of both the stack and the monitor.'))
EN.append(('h2', '3.2 Behavior-tree health monitoring'))
EN.append(('p', 'The monitor is a behavior tree ticked at 10 Hz (Figure 3). A sequence node updates the driving state, then a parallel node runs per-sensor checkers — front and rear LiDAR, camera, IMU, and GNSS — each scoring its stream on freshness (message arrival against a deadline), quality (e.g., point count, pixel statistics), and physical consistency (e.g., yaw-rate plausibility, EKF residuals). Channel scores are fused into per-sector capability scores that express what the vehicle can still perceive in each direction, which is the currency the supervisor reasons in. Two failure classes get distinct treatment: gradual degradation passes through band debouncing to suppress transients, whereas complete silence — a dead sensor — takes a hard-fail fast path: once the freshness deadline (1.0 s) is exceeded, debouncing and recovery holds are skipped because the silence itself is persistent evidence, and the monitor commits to a decision within a 1.5 s detection-to-decision deadline.'))
EN.append(('fig', 'fig3_bt.png', 15.0, 'Fig. 3. Behavior-tree structure of the CDR Monitor (10 Hz tick): state update, parallel per-sensor checks, and sector/capability fusion.'))
EN.append(('h2', '3.3 MRM selection policy'))
EN.append(('p', 'Table 1 gives the selection policy. Dual thresholds partition the health estimate: above the intervention-entry threshold θH the vehicle continues; in the band between θH and the minimum-capability threshold θL — or immediately upon a dead sensor — the supervisor evacuates (MOVE), choosing among shoulder and parking-lot candidates ranked by a cost function, with the in-lane stop as fallback if the maneuver fails; below θL, or when no candidate is reachable, it delegates the stop to the stock stack (DEFER), with the emergency stop as the final fallback. The cost of a candidate is dominated by the exposure time η it implies — route time under the speed limits plus expected signal waits — following the time-to-safe-state framing of ISO 26262: risk accumulates per second of degraded driving, not per meter. Additional terms penalize routes through traffic lights when camera capability is low, penalize candidates whose required perception sectors are unhealthy, and encode the MRC quality ordering (a parking lot fully clears the roadway; a shoulder stop may partially occupy it) as a fixed penalty on shoulder candidates.'))
EN.append(('fig', 'tab1_policy.png', 15.5, 'Table 1. MRM selection policy by monitored condition. ● selected (cost-ordered), ○ fallback on move failure, × not selected.'))
EN.append(('p', 'During evacuation the supervisor enforces a fixed 3.0 m/s speed cap. The value comes from a stopping-distance model d(v) = vτ + v²/2a with an empirically identified effective reaction time τ = 1.5 s and deceleration a = 3.5 m/s²: 3.0 m/s keeps the required stopping distance (5.8 m) inside the 8 m encounter envelope used in our edge-case experiments, whereas the uncapped evacuation speed of 4.2 m/s requires 8.8 m and cannot stop in time. Section 5.3 validates the model against measured avoid/collide boundaries.'))
EN.append(('h2', '3.4 Refuge candidate map'))
EN.append(('p', 'Candidates are not searched online; they are pre-annotated in a custom lanelet2 map of Town07 (Figure 4): 16 shoulder lanelets tagged road_shoulder and 4 parking-lot polygons with individual parking spaces. Pockets too short for a moving pull-over are excluded at extraction time. Along the reference route the nearest candidate is never far — median 4.3 m, worst case 23.4 m straight-line — so a bounded-time evacuation is available from any point of the operational design domain; where such coverage cannot be guaranteed, the policy answer is DEFER, not a longer drive.'))
EN.append(('fig', 'fig4_candidates.png', 11.5, 'Fig. 4. Pre-annotated refuge candidates on the custom Town07 lanelet2 map: 16 shoulder lanelets (red), 4 parking-lot polygons (blue), and the reference route (dashed).'))

EN.append(('h1', '4. Experimental Setup'))
EN.append(('p', 'All experiments run in a closed loop of CARLA 0.9.16 and Autoware 0.39.0 on Town07 under a 15 km/h speed limit, orchestrated through the CARLA leaderboard for case execution and official scoring [3]. Figure 5 shows representative scenes: the nominal driving environment, the perception view, the annotated vector map, the two evacuation MRCs (shoulder and parking lot), and the pedestrian dart-out used in the edge-case study. Timing metrics are reported in simulation time throughout.'))
EN.append(('fig', 'fig5_scenes.png', 16.0, 'Fig. 5. Representative scenes: (a) Town07 driving scene, (b) RViz perception view, (c) custom vector map with refuge candidates, (d) shoulder-evacuation MRC with traffic passing, (e) parking-lot evacuation MRC, (f) pedestrian dart-out.'))
EN.append(('p', 'The fault model (Figure 6) covers eleven types across four sensor families, grounded in the measurement literature where physics matters: LiDAR soiling as sector-local transmittance loss with threshold-dependent dropout [8, 13], rain as Beer–Lambert attenuation with near-range clutter [9, 10], camera pixel noise, dead sensors (camera and LiDAR stream freeze), and navigation faults — GNSS white noise, first-order Gauss–Markov correlated bias, GNSS outage, and gyro white noise, fixed bias, and bias ramp. Each type is injected at mid and high severity inside the bridge.'))
EN.append(('fig', 'fig6_faults.png', 12.0, 'Fig. 6. Sensor fault model: (a) LiDAR soiling, (b) LiDAR rain clutter, (c) camera pixel noise, (d) navigation fault waveforms.'))
EN.append(('p', 'The main campaign comprises 1,131 valid cases over fault types, severities, traffic densities, and methods (proposed versus unsupervised stock), with 45 fault-free cases for false-activation measurement; a supplementary campaign of 611 valid cases covers the navigation fault extension at the same protocol scale. The edge-case study is a paired, same-seed, four-arm ablation over 20 seeds: a pedestrian crosses from the right lane edge 8 m ahead, launched at detection + 3 s by a behavior-independent trigger so all arms face identical relative geometry. Collision outcomes are established by a triple verdict system — a real-time ego collision-sensor ledger, a walker-physics oracle, and a human visual cross-check — introduced after we found that a walker-attached collision sensor never fires and that runner exit labels and official infraction records can both mislead; we document this as a methodological caution for CARLA-based safety claims.'))

EN.append(('h1', '5. Results'))
EN.append(('h2', '5.1 Detection'))
EN.append(('p', 'Figure 7 summarizes detection latency per fault condition. The monitor detected 96–100% of injected faults in 11 of 12 main-campaign conditions with median latencies of 2.1–5.0 s; the exception is mild LiDAR sparsification, tolerated by design as it does not reduce driving capability. No false activation occurred in 45 fault-free cases. The supplementary navigation campaign reached 100% detection in all conditions, with a dose–response relationship for the gyro bias ramp (slower ramps take longer to cross detection thresholds) and a bimodal latency for GNSS outage depending on whether injection occurred while moving or while waiting at a signal. Dead-sensor conditions exercise the hard-fail fast path: across the full camera/LiDAR-freeze matrix the detection-to-decision time was about 1.0 s at the median — dominated by the freshness deadline — with a maximum of 1.20 s and zero violations of the 1.5 s deadline, and every case completed its MRM.'))
EN.append(('fig', 'fig7_latency.png', 12.0, 'Fig. 7. Detection latency by fault condition (proposed arm; dead-sensor rows re-measured through the hard-fail fast path in simulation time).'))
EN.append(('h2', '5.2 Exposure reduction'))
EN.append(('p', 'The purpose of evacuation is to shorten the time the vehicle spends driving on degraded senses. Measured as degraded-state driving distance, supervision reduced exposure from 238–275 m under the unsupervised stock stack to 32–58 m with detect-and-evacuate for camera and localization faults. The comparison between stop styles is also informative: the in-lane stop yields zero post-encounter moving exposure but occupies the driving lane beyond the observation horizon, whereas evacuation spends a median of 37.2 m of controlled low-speed motion and then clears the roadway — the two responses trade different kinds of exposure, which is precisely what a graded policy should arbitrate.'))
EN.append(('h2', '5.3 Stopping-distance model validation'))
EN.append(('p', 'Distance-ladder experiments located the avoid/collide boundary at 8–11 m for 4.2 m/s driving and at 7–8 m for 3.0 m/s (Figure 8). The model reproduces the uncapped boundary closely (prediction 8.8 m) and is optimistic at the capped speed (prediction 5.8 m against a measured 7–8 m band), the gap reflecting planner reaction variance; both measurements support the design conclusion that 4.2 m/s cannot stop within the 8 m envelope while 3.0 m/s can, with margin at the model level and marginally in the worst measured case.'))
EN.append(('fig', 'fig8_stopdist.png', 12.0, 'Fig. 8. Stopping-distance model d(v)=vτ+v²/2a (τ=1.5 s, a=3.5 m/s²) against measured avoid/collide boundaries from the distance ladder.'))
EN.append(('h2', '5.4 Stop versus evacuate: the edge case'))
EN.append(('p', 'In the four-arm ablation, native continuation collided in 14 of 20 seeds, detection with in-lane stop in 0 of 20, uncapped evacuation in 10 of 20, and capped evacuation in 11 of 20 (exact McNemar, native versus capped evacuation: p = 0.375). The explicit cap prevented no additional collisions in this sample — we report this without an equivalence claim. The decisive observation is temporal: every evacuation-arm collision occurred during the detection-to-deceleration transient, while the same capped-evacuation policy facing encounters in settled cruise after deceleration avoided all of them (0/8). The stop-versus-evacuate choice is thus a trade-off between immediate collision risk during the transient, which favors stopping, and the terminal benefit of clearing the lane, which favors evacuation when it succeeds — observational evidence, from a two-regime comparison rather than a causal manipulation, that shortening detection and deceleration is where additional safety is to be found, in line with the FTTI framing.'))
EN.append(('p', 'Figure 9 completes the picture on the benefit side. Among the 20 evacuation-arm cases, 7 collided (reported separately as failed lane clearance), 6 cleared the driving lane within the observation horizon with an observed median of 11.0 s, and 7 had not cleared by the horizon and are right-censored; the Kaplan–Meier survival of lane occupancy ends at 0.538, so the median clearance time is not reached within the horizon. Evacuation, when it works, converts a permanent lane obstruction into a bounded clearing process, but the censored fraction shows the conversion is not guaranteed within a short horizon.'))
EN.append(('fig', 'fig9_km.png', 12.0, 'Fig. 9. Kaplan–Meier curve of driving-lane occupancy after the encounter (evacuation arms; ticks mark censored cases). Terminal survival 0.538; median not reached within the horizon.'))

EN.append(('h1', '6. Limitations'))
EN.append(('p', 'The evaluation uses a single map, a single 15 km/h speed limit, and two launch corridors, and all stack-specific observations are tied to Autoware 0.39.0. The two-regime transient analysis is observational: encounter timing was standardized relative to detection, not manipulated causally. The ablation sample (20 seeds) is small for arm-to-arm comparisons, which is why we report exact McNemar statistics and abstain from equivalence claims. Refuge coverage is a property of the annotated map; deployments on sparser road networks would rely on the DEFER branch more often, and an absolute exposure-time ceiling on candidate selection is a natural hardening we identify for future work.'))

EN.append(('h1', '7. Conclusion'))
EN.append(('p', 'A graded fault response — continuous health monitoring feeding a capability-aware choice among refuge options — can be attached to a production automated driving stack without modifying it, detects a physics-grounded spectrum of sensor faults reliably and within hard deadlines for dead sensors, and materially shortens degraded-state exposure relative to both silent continuation and the ubiquitous in-lane stop. The edge-case study tempers the promise with a precise boundary: during the detection transient, stopping remains the safer reflex, and the payoff of evacuation is realized after deceleration settles. Making that transient shorter is the clearest path to making graded responses strictly dominant.'))

EN.append(('h1', 'References'))
for r in [
 '[1] S. Kato et al., "Autoware on Board: Enabling Autonomous Vehicles with Embedded Systems," Proc. ACM/IEEE ICCPS, 2018.',
 '[2] A. Dosovitskiy, G. Ros, F. Codevilla, A. Lopez, and V. Koltun, "CARLA: An Open Urban Driving Simulator," Proc. CoRL, 2017.',
 '[3] G. Kaljavesi, D. Majstorovic, M. Clement, and F. Diermeyer, "Empirical Mapping of Technical Bottlenecks in Autonomous Driving: A Cross-Platform Evaluation of Simulated and Real-World Performance," preprint, 2026.',
 '[4] ISO 26262:2018, Road Vehicles — Functional Safety.',
 '[5] ISO 23793-1:2022, Intelligent Transport Systems — Minimal Risk Manoeuvre (MRM) for Automated Driving — Part 1.',
 '[6] UNECE Regulation No. 157, Automated Lane Keeping Systems (ALKS), 2021.',
 '[7] SAE J3016, Taxonomy and Definitions for Terms Related to Driving Automation Systems, 2021.',
 '[8] T. Goelles, B. Schlager, and S. Muckenhuber, "Fault Detection, Isolation, Identification and Recovery (FDIIR) Methods for Automotive Perception Sensors Including a Detailed Literature Survey for Lidar," Sensors, vol. 20, no. 13, p. 3662, 2020.',
 '[9] C. Goodin, D. Carruth, M. Doude, and C. Hudson, "Predicting the Influence of Rain on LIDAR in ADAS," Electronics, vol. 8, no. 1, p. 89, 2019.',
 '[10] V. Kilic et al., "Lidar Light Scattering Augmentation (LISA): Physics-Based Simulation of Adverse Weather Conditions for 3D Object Detection," arXiv:2107.07004, 2021.',
 '[11] M. Hahner, C. Sakaridis, D. Dai, and L. Van Gool, "Fog Simulation on Real LiDAR Point Clouds for 3D Object Detection in Adverse Weather," Proc. IEEE/CVF ICCV, 2021.',
 '[12] M. Hahner et al., "LiDAR Snowfall Simulation for Robust 3D Object Detection," Proc. IEEE/CVF CVPR, 2022.',
 '[13] M. Trierweiler, T. Peterseim, and C. Neumann, "Automotive LiDAR Pollution Detection System Based on Total Internal Reflection Techniques," IEEE SENSORS, 2019.',
]:
    EN.append(('ref', r))

# ---------------------------------------------------------------- content: KO
KO = []
KO.append(('title', '행동트리 기반 센서 건강도 감시와 위험·잔여능력 기반 최소위험기동 감독을 통한 자율주행 시스템의 단계적 고장 대응'))
KO.append(('author', '○○○\n성균관대학교 전자전기컴퓨터공학과'))
KO.append(('h1', '초록'))
KO.append(('abs', '자율주행 스택의 센서 고장 대응은 사실상 하나의 전략 — 즉시 차선 내 정지 — 로 수렴해 있다. 이 전략이 발동하면 차량은 주행 차선을 점유한 장애물이 되고, 발동하지 못하면 차량은 저하된 인지 능력으로 주행을 계속한다. 본 논문은 신선도·품질·물리 3계열 점검으로 센서별 건강도를 연속 점수로 추정하는 행동트리 기반 감시기와, 고장 유형·심각도·잔여능력에 따라 갓길/주차장 대피와 순정 정지 위임 중에서 대응을 선택하고 대피 중 3.0 m/s 속도 상한을 강제하는 감독기로 구성된 단계적 고장 대응 프레임워크를 제안한다. 프레임워크는 무수정 Autoware 0.39.0 스택에 애드온으로 부착되어 CARLA 0.9.16과 폐루프로 평가되었다. 유효 1,131케이스에서 감지기는 12개 고장 조건 중 11개에서 96–100% 감지율과 2.1–5.0초의 중앙값 지연을 보였고 무고장 45케이스에서 오발동이 없었으며, 감독 도입은 저하 상태 주행 노출을 238–275 m에서 32–58 m로 줄였다. 완전한 센서 침묵은 하드페일 고속경로로 판정되어 전 케이스에서 1.5초 감지-판정 데드라인을 충족했다(최대 1.20초). 표준화된 보행자 돌발 조우를 사용한 짝지은 4팔 절제 실험은 정지와 대피의 선택이 시간적 트레이드오프임을 보인다: 대피의 잔여 위험은 감속 과도구간에 집중되고(11/20), 동일 정책이 정속 구간에서 만난 조우는 전부 회피되었다(0/8). 보조 캠페인은 고장 모델을 GNSS 상관 편향·신호 상실과 IMU 편향·드리프트로 확장했다(유효 611케이스, 전 조건 100% 감지).'))
KO.append(('kw', '주제어: 자율주행, 기능안전, 최소위험기동, FTTI, 센서 고장 감지, 행동트리'))

KO.append(('h1', '1. 서론'))
KO.append(('p', '양산 수준의 자율주행 스택이 갖춘 최소위험기동(MRM) 목록은 실제로는 하나의 행동으로 수렴한다: 고장이 인지될 만큼 심각하면 현재 차선에 정지한다. 이 단일 전략은 심각도 스펙트럼의 양 끝에서 서로 다른 방식으로 실패한다. 발동하면 차량은 주행 차선 위의 정지 장애물이 되어, 정지가 제거하려던 위험에 후속 교통을 노출시킨다. 발동하지 못하면 — 고장이 이진 진단을 트리거하지 않은 채 인지 성능만 저하시키면 — 차량은 더 이상 갖고 있지 않은 감각으로 주행을 계속한다. 그림 1이 문제 설정을 보여준다. 2차선 지방도로에서 센서 고장을 감지한 차량에게는 대개 자기 차선보다 나은 선택지 — 인접 여유 공간, 주차장, 전방 갓길 — 가 존재하지만, 이를 활용하려면 잔여능력이 얼마인지, 그리고 대피 기동 자체가 여전히 안전한지 — 대피 중 보행자가 돌발 진입하는 엣지케이스까지 포함해서 — 를 알아야 한다.'))
KO.append(('fig', 'fig1_problem.png', 14.5, '그림 1. 문제 설정: 센서 고장 시의 단계적 대피 선택지(a)와 대피 중 보행자 돌발 조우 엣지케이스(b). 후보는 비용함수로 서열화된다.'))
KO.append(('p', '본 논문은 협력하는 두 구성요소로 이루어진 단계적 고장 대응 프레임워크를 제안한다. 행동트리 감시기(CDR Monitor)는 원시 센서 스트림을 센서별·섹터별 연속 건강도 점수로 변환하고, 감독기(MRM Supervisor)는 이중 임계값과 사전 주석된 대피 후보에 대한 시간 단위 비용함수를 사용해 감시 상태를 다섯 가지 대응 — 주행 지속, 갓길 정차, 주차장 정차, 차선 내 정지, 비상 정지 — 중 하나로 사상한다. 프레임워크는 읽기 전용 토픽 구독과 표준 AD API·진단 인터페이스만으로 무수정 Autoware 스택에 부착되므로 정상 주행 채널은 전혀 변경되지 않는다.'))
KO.append(('p', '기여는 다음과 같다. (1) 이진 고장이 아닌 단계적 건강도 추정을 산출하며, 완전한 센서 침묵을 1.5초 데드라인 안에 판정하는 증거 기반 고속경로를 갖춘 감시 설계. (2) 최소위험상태(MRC)의 질 서열과 정지거리 모델에서 유도된 보수적 3.0 m/s 대피 속도 상한을 명시한 잔여능력 기반 MRM 선택 정책. (3) 물리 근거를 갖춘 11종 고장 모델에 대한 유효 1,131케이스 폐루프 평가와 611케이스 보조 캠페인. (4) 정지-대피 트레이드오프의 실증적 규명 — 대피 위험이 감지-감속 과도구간에 집중됨을 보이는 2국면 분석을 포함한다.'))

KO.append(('h1', '2. 관련 연구'))
KO.append(('p', 'Autoware[1]는 진단 그래프로 트리거되는 차선 내 MRM(컴포트/이머전시 정지)을 제공하지만 대피지로의 이동이라는 개념이 없고 고장 처리도 이진적이다. 표준은 본 연구가 겨냥하는 요구사항의 틀을 제공한다. ISO 26262[4]는 안전 상태 도달 시간의 유계성을 요구하며 고장 허용 시간 간격(FTTI)을 정의하고, UNECE R157[6]은 기동 중 위험을 최소화하며 정지로 종결되는 MRM을 요구하며, ISO 23793-1[5]은 저속 자율주행의 MRM 유형을 차선 내 정지와 더 안전한 정차 위치로의 기동으로 구분하고, SAE J3016[7]은 기동이 도달해야 할 최소위험상태를 정의한다. 본 연구의 정책은 이 개념들을 명시적이고 검증 가능한 선택 행렬로 운용화한 것이다. 고장 모델은 라이다 열화 문헌 — Goelles 등의 고장 분류학[8], 강우 감쇠·클러터의 실측 모델[9, 10], 악천후 포인트클라우드 시뮬레이션[11, 12], 커버 오염의 실측 효과[13] — 에 근거한다. 실험 인프라는 CARLA[2], Kaljavesi 등의 Autoware–CARLA 리더보드 연동[3], 그리고 대피 후보를 주석한 자체 제작 Town07 lanelet2 맵 위에 구축되었다.'))

KO.append(('h1', '3. 시스템 설계'))
KO.append(('h2', '3.1 아키텍처'))
KO.append(('p', '그림 2는 아키텍처를 보여준다. CARLA 서버는 브리지를 거쳐 Autoware 스택에 센서 토픽을 공급하며, 센서 고장은 이 브리지 변환 계층 내부에서 주입된다. 따라서 오염된 데이터는 정상 스택과 제안 감독 계층에 동일하게 도달한다. CDR Monitor는 같은 센서 토픽을 읽기 전용으로 구독해 10 Hz로 건강도 점수를 발행하고, MRM Supervisor는 점수를 소비하여 개입이 필요할 때 공개 인터페이스만으로 스택에 작용한다 — 대피(MOVE)는 속도 상한을 동반한 경로 재설정 요청으로, 위임(DEFER)은 순정 차선 내 정지를 발동시키는 진단 ERROR 주입으로. Autoware 자체는 무수정으로 동작한다.'))
KO.append(('fig', 'fig2_arch.png', 14.0, '그림 2. 시스템 아키텍처. 제안 감독 계층(CDR Monitor, MRM Supervisor)이 무수정 Autoware 스택에 부착되며, 고장은 스택과 감시기 양쪽의 상류인 브리지에서 주입된다.'))
KO.append(('h2', '3.2 행동트리 건강도 감시'))
KO.append(('p', '감시기는 10 Hz로 틱되는 행동트리다(그림 3). 시퀀스 노드가 주행 상태를 갱신한 뒤, 병렬 노드가 센서별 점검기 — 전·후방 라이다, 카메라, IMU, GNSS — 를 실행한다. 각 점검기는 신선도(데드라인 대비 메시지 도착), 품질(포인트 수, 픽셀 통계 등), 물리적 정합성(요레이트 타당성, EKF 잔차 등)으로 스트림을 점수화하고, 채널 점수는 방향별로 차량이 무엇을 여전히 인지할 수 있는지를 표현하는 섹터별 능력 점수로 융합된다 — 감독기가 추론하는 화폐가 바로 이것이다. 두 고장 계열은 다르게 취급된다. 점진적 열화는 과도현상을 억제하는 밴드 디바운싱을 거치지만, 완전한 침묵 — 죽은 센서 — 은 하드페일 고속경로를 탄다: 신선도 데드라인(1.0초)이 초과되는 순간 침묵 자체가 지속적 증거이므로 디바운싱과 회복 대기를 건너뛰고, 1.5초의 감지-판정 데드라인 안에 결정을 확정한다.'))
KO.append(('fig', 'fig3_bt.png', 15.0, '그림 3. CDR Monitor의 행동트리 구조(10 Hz 틱): 상태 갱신, 병렬 센서 점검, 섹터·능력 융합.'))
KO.append(('h2', '3.3 MRM 선택 정책'))
KO.append(('p', '표 1이 선택 정책이다. 이중 임계값이 건강도 추정을 분할한다: 개입 진입 임계값 θH 위에서는 주행을 지속하고, θH와 최소능력 임계값 θL 사이의 밴드 — 또는 죽은 센서 즉시 — 에서는 비용함수로 서열화된 갓길·주차장 후보 중에서 골라 대피(MOVE)하며 기동 실패 시 차선 내 정지가 폴백이 된다. θL 아래이거나 도달 가능한 후보가 없으면 정지를 순정 스택에 위임(DEFER)하고 비상 정지가 최종 폴백이다. 후보의 비용은 그것이 함의하는 노출 시간 η — 제한속도 기준 경로 시간에 기대 신호 대기를 더한 값 — 가 지배한다. 이는 ISO 26262의 안전 상태 도달 시간 관점을 따른 것으로, 위험은 미터가 아니라 저하 주행의 초 단위로 누적된다. 추가 항은 카메라 능력이 낮을 때 신호등 경유 경로를 벌점하고, 요구 인지 섹터가 불건강한 후보를 벌점하며, MRC 질 서열 — 주차장은 도로를 완전히 비우지만 갓길 정차는 부분 점유가 남는다 — 을 갓길 후보에 대한 고정 벌점으로 부호화한다.'))
KO.append(('fig', 'tab1_policy.png', 15.5, '표 1. 감시 상태별 MRM 선택 정책. ● 선택(비용 서열), ○ 이동 실패 시 폴백, × 미선택.'))
KO.append(('p', '대피 중 감독기는 3.0 m/s 고정 속도 상한을 강제한다. 이 값은 실측 동정된 유효 반응시간 τ = 1.5 s와 감속도 a = 3.5 m/s²의 정지거리 모델 d(v) = vτ + v²/2a에서 나온다: 3.0 m/s는 필요 정지거리(5.8 m)를 엣지케이스 실험의 8 m 조우 봉투 안에 유지하지만, 상한 없는 대피 속도 4.2 m/s는 8.8 m를 요구해 제때 정지할 수 없다. 5.3절에서 이 모델을 실측 회피/충돌 경계와 대조해 검증한다.'))
KO.append(('h2', '3.4 대피 후보 지도'))
KO.append(('p', '후보는 온라인으로 탐색되지 않고 자체 제작 Town07 lanelet2 맵에 사전 주석된다(그림 4): road_shoulder로 태그된 갓길 레인렛 16개와 개별 주차칸을 갖춘 주차장 폴리곤 4개다. 이동식 정차가 불가능한 짧은 포켓은 추출 단계에서 제외된다. 기준 경로를 따라 최근접 후보까지의 거리는 중앙값 4.3 m, 최악 23.4 m(직선거리)로, 운영설계영역의 어느 지점에서도 유계 시간 내 대피가 가능하다. 이런 커버리지가 보장되지 않는 도로라면 정책의 답은 더 먼 주행이 아니라 DEFER다.'))
KO.append(('fig', 'fig4_candidates.png', 11.5, '그림 4. 자체 제작 Town07 lanelet2 맵의 사전 주석 대피 후보: 갓길 레인렛 16개(적색), 주차장 폴리곤 4개(청색), 기준 경로(점선).'))

KO.append(('h1', '4. 실험 환경'))
KO.append(('p', '모든 실험은 CARLA 0.9.16과 Autoware 0.39.0의 폐루프로 Town07에서 제한속도 15 km/h 하에 수행되며, 케이스 실행과 공식 채점은 CARLA 리더보드를 통한다[3]. 그림 5는 대표 장면들 — 정상 주행 환경, 인식 화면, 주석된 벡터맵, 두 가지 대피 MRC(갓길·주차장), 엣지케이스 연구에 쓰인 보행자 돌발 조우 — 을 보여준다. 시간 지표는 전부 시뮬레이션 시간으로 보고한다.'))
KO.append(('fig', 'fig5_scenes.png', 16.0, '그림 5. 대표 장면: (a) Town07 주행 장면, (b) RViz 인식 화면, (c) 대피 후보가 주석된 자체 벡터맵, (d) 갓길 대피 MRC(후속 교통 통과), (e) 주차장 대피 MRC, (f) 보행자 돌발 조우.'))
KO.append(('p', '고장 모델(그림 6)은 4개 센서 계열에 걸친 11종을 다루며, 물리가 중요한 곳에서는 실측 문헌에 근거한다: 문턱 의존 드롭아웃을 동반한 섹터 국소 투과율 손실로서의 라이다 오염[8, 13], Beer–Lambert 감쇠와 근거리 클러터로서의 강우[9, 10], 카메라 픽셀 노이즈, 죽은 센서(카메라·라이다 스트림 정지), 그리고 항법 고장 — GNSS 백색 노이즈, 1차 Gauss–Markov 상관 편향, GNSS 신호 상실, 자이로 백색 노이즈·고정 편향·편향 램프. 각 유형은 mid·high 두 심각도로 브리지 내부에서 주입된다.'))
KO.append(('fig', 'fig6_faults.png', 12.0, '그림 6. 센서 고장 모델: (a) 라이다 오염, (b) 라이다 강우 클러터, (c) 카메라 픽셀 노이즈, (d) 항법 고장 파형.'))
KO.append(('p', '본 캠페인은 고장 유형·심각도·교통 밀도·방법(제안 대 무감독 순정)에 걸친 유효 1,131케이스로 구성되며 오발동 측정을 위한 무고장 45케이스를 포함한다. 보조 캠페인 유효 611케이스는 항법 고장 확장을 동일 프로토콜 규모로 다룬다. 엣지케이스 연구는 20개 시드에 대한 짝지은 동일 시드 4팔 절제 실험이다: 보행자가 전방 8 m에서 차선 우측 끝으로부터 횡단하며, 행동 독립적 트리거에 의해 감지+3초에 발사되어 모든 팔이 동일한 상대 기하를 마주한다. 충돌 판정은 삼중 판정 체계 — 실시간 에고 충돌센서 원장, 워커 물리 오라클, 인간 시각 교차검증 — 로 확정했다. 이는 워커에 부착한 충돌센서가 전혀 발화하지 않음을 실증적으로 발견한 뒤 도입한 것으로, 러너 종료 라벨과 공식 위반 기록이 모두 오도할 수 있다는 사실과 함께 CARLA 기반 안전성 주장에 대한 방법론적 주의사항으로 기록해 둔다.'))

KO.append(('h1', '5. 결과'))
KO.append(('h2', '5.1 감지'))
KO.append(('p', '그림 7은 고장 조건별 감지 지연을 요약한다. 감시기는 본 캠페인 12개 조건 중 11개에서 주입 고장의 96–100%를 감지했고 중앙값 지연은 2.1–5.0초였다. 예외는 경미한 라이다 희박화로, 주행 능력을 저하시키지 않아 설계상 용인된다. 무고장 45케이스에서 오발동은 없었다. 보조 항법 캠페인은 전 조건 100% 감지에 도달했으며, 자이로 편향 램프에서 용량-반응 관계(완만한 램프일수록 임계값 도달이 늦음)가, GNSS 신호 상실에서는 주입 시점이 주행 중인지 신호 대기 중인지에 따른 이봉 지연 분포가 관찰되었다. 죽은 센서 조건은 하드페일 고속경로를 검증한다: 카메라/라이다 정지 전체 행렬에서 감지-판정 시간은 중앙값 약 1.0초 — 신선도 데드라인이 지배 — 였고 최대 1.20초로 1.5초 데드라인 위반이 0건이었으며, 전 케이스가 MRM을 완수했다.'))
KO.append(('fig', 'fig7_latency.png', 12.0, '그림 7. 고장 조건별 감지 지연(제안 팔; 죽은 센서 행은 하드페일 고속경로로 시뮬레이션 시간 재계측).'))
KO.append(('h2', '5.2 노출 감소'))
KO.append(('p', '대피의 목적은 차량이 저하된 감각으로 주행하는 시간을 줄이는 것이다. 저하 상태 주행거리로 측정했을 때, 감독 도입은 카메라·측위 고장에서 노출을 무감독 순정 스택의 238–275 m에서 감지-대피의 32–58 m로 줄였다. 정지 방식 간 비교도 시사적이다: 차선 내 정지는 조우 후 이동 노출이 0이지만 관측 지평 너머까지 주행 차선을 점유하는 반면, 대피는 중앙값 37.2 m의 통제된 저속 이동을 소비한 뒤 도로를 비운다 — 두 대응은 서로 다른 종류의 노출을 교환하며, 단계적 정책이 중재해야 할 대상이 정확히 이것이다.'))
KO.append(('h2', '5.3 정지거리 모델 검증'))
KO.append(('p', '거리 사다리 실험은 회피/충돌 경계를 4.2 m/s 주행에서 8–11 m, 3.0 m/s에서 7–8 m로 위치시켰다(그림 8). 모델은 상한 없는 속도의 경계를 근접 재현하고(예측 8.8 m), 상한 속도에서는 낙관적이다(예측 5.8 m 대 실측 7–8 m 밴드; 간극은 플래너 반응 분산을 반영한다). 두 실측 모두 설계 결론 — 4.2 m/s는 8 m 봉투 안에서 정지할 수 없고 3.0 m/s는 가능하다 — 을 지지한다.'))
KO.append(('fig', 'fig8_stopdist.png', 12.0, '그림 8. 정지거리 모델 d(v)=vτ+v²/2a (τ=1.5 s, a=3.5 m/s²)와 거리 사다리로 실측한 회피/충돌 경계.'))
KO.append(('h2', '5.4 정지 대 대피: 엣지케이스'))
KO.append(('p', '4팔 절제 실험에서 순정 지속은 20개 시드 중 14개에서, 감지+차선 내 정지는 0개에서, 상한 없는 대피는 10개에서, 상한 대피는 11개에서 충돌했다(정확 McNemar, 순정 대 상한 대피: p = 0.375). 명시적 상한은 이 표본에서 추가 충돌을 예방하지 못했다 — 동등성 주장 없이 그대로 보고한다. 결정적 관찰은 시간적이다: 대피 팔의 모든 충돌은 감지-감속 과도구간에서 발생했고, 동일한 상한 대피 정책이 감속 안착 후 정속 구간에서 만난 조우는 전부 회피했다(0/8). 따라서 정지-대피 선택은 과도구간의 즉각적 충돌 위험(정지에 유리)과, 대피가 성공했을 때 차선을 비워 더 안전한 최종 위치에 도달하는 이득(대피에 유리) 사이의 시간적 트레이드오프다. 이는 인과 조작이 아닌 2국면 비교의 관찰 증거지만, FTTI 관점에서 추가 안전이 감지·감속 단축에 있음을 정량적으로 뒷받침한다.'))
KO.append(('p', '그림 9는 이득 측면을 완성한다. 대피 팔 20케이스 중 7개는 충돌해 차선 정리 실패로 별도 보고되고, 6개는 관측 지평 내에 주행 차선을 비웠으며(관측 중앙값 11.0초), 7개는 지평까지 비우지 못해 우측 절단되었다. 차선 점유의 Kaplan–Meier 생존은 0.538에서 끝나 중앙값 정리 시간은 지평 내에 도달하지 않는다. 대피는 성공할 경우 영구적 차선 점유를 유계의 정리 과정으로 전환하지만, 절단 비율은 그 전환이 짧은 지평 안에서 보장되지는 않음을 보여준다.'))
KO.append(('fig', 'fig9_km.png', 12.0, '그림 9. 조우 후 주행 차선 점유의 Kaplan–Meier 곡선(대피 팔; 눈금은 절단 케이스). 최종 생존 0.538, 중앙값은 지평 내 미도달.'))

KO.append(('h1', '6. 한계'))
KO.append(('p', '평가는 단일 맵, 단일 제한속도(15 km/h), 두 개의 발사 회랑을 사용하며, 스택 관련 관찰은 모두 Autoware 0.39.0에 종속적이다. 2국면 과도구간 분석은 관찰적이다: 조우 시점은 감지 기준으로 표준화되었을 뿐 인과적으로 조작되지 않았다. 절제 표본(20 시드)은 팔 간 비교에 작은 크기이며, 이 때문에 정확 McNemar 통계를 보고하고 동등성 주장을 삼갔다. 대피 커버리지는 주석된 맵의 속성이므로 더 성긴 도로망에서는 DEFER 분기에 더 자주 의존하게 될 것이며, 후보 선택에 대한 절대 노출 시간 상한은 향후 과제로 식별해 둔 자연스러운 보강이다.'))

KO.append(('h1', '7. 결론'))
KO.append(('p', '연속 건강도 감시가 대피 선택지에 대한 잔여능력 기반 선택으로 이어지는 단계적 고장 대응은, 양산 자율주행 스택을 수정하지 않고 부착될 수 있고, 물리 근거를 갖춘 센서 고장 스펙트럼을 신뢰성 있게 — 죽은 센서에 대해서는 엄격한 데드라인 안에 — 감지하며, 무언의 주행 지속과 편재하는 차선 내 정지 양쪽에 대해 저하 상태 노출을 실질적으로 줄인다. 엣지케이스 연구는 이 가능성에 정밀한 경계를 붙인다: 감지 과도구간에서는 정지가 여전히 더 안전한 반사이고, 대피의 보상은 감속이 안착한 뒤에 실현된다. 그 과도구간을 줄이는 것이 단계적 대응을 엄밀히 우월하게 만드는 가장 분명한 길이다.'))

KO.append(('h1', '참고문헌'))
for _, r in [(None, x[1]) for x in EN if x[0] == 'ref']:
    KO.append(('ref', r))

# ---------------------------------------------------------------- builder
def build(content, out, latin='Times New Roman', ea='바탕'):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    for m in ('top_margin', 'bottom_margin', 'left_margin', 'right_margin'):
        setattr(sec, m, Cm(2.5))
    st = doc.styles['Normal']
    st.font.name = latin; st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), ea)
    st.paragraph_format.space_after = Pt(4)

    def para(txt, size=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             before=0, after=4, italic=False):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        r = p.add_run(txt)
        r.font.size = Pt(size); r.bold = bold; r.italic = italic
        r.font.name = latin
        r._element.rPr.rFonts.set(qn('w:eastAsia'), ea)
        return p

    for item in content:
        kind = item[0]
        if kind == 'title':
            para(item[1], 15, True, WD_ALIGN_PARAGRAPH.CENTER, after=10)
        elif kind == 'author':
            for ln in item[1].split('\n'):
                para(ln, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, after=2)
            para('', after=6)
        elif kind == 'h1':
            para(item[1], 12.5, True, WD_ALIGN_PARAGRAPH.LEFT, before=10, after=5)
        elif kind == 'h2':
            para(item[1], 11, True, WD_ALIGN_PARAGRAPH.LEFT, before=6, after=4)
        elif kind == 'abs':
            p = para(item[1], 9.5)
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.right_indent = Cm(0.8)
        elif kind == 'kw':
            p = para(item[1], 9.5, italic=True)
            p.paragraph_format.left_indent = Cm(0.8)
        elif kind == 'p':
            para(item[1])
        elif kind == 'ref':
            p = para(item[1], 9)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(2)
        elif kind == 'fig':
            _, fn, wcm, cap = item
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.add_run().add_picture(os.path.join(F, fn), width=Cm(wcm))
            c = para(cap, 9, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
            c.paragraph_format.space_before = Pt(2)
    doc.save(out)
    print('built', out)

build(EN, os.path.join(OUTDIR, 'paper_en_0826.docx'), ea='Times New Roman')
build(KO, os.path.join(OUTDIR, 'paper_ko_0826.docx'), ea='바탕')
