# -*- coding: utf-8 -*-
"""v22 EN mirrors: speed-dose section, cap non-delivery disclosure, renumbering."""
import json, re, sys

TP = 'translated.json'
tr = json.load(open(TP))
FAIL = []

def sw(old, new, tag, cells=False, foot=False):
    for c in tr:
        for it in tr[c]['items']:
            f = it['fields']
            if isinstance(f[0], str) and old in f[0]:
                f[0] = f[0].replace(old, new, 1); print(tag, 'ok'); return
            if foot and it['kind'] == 'tbl' and isinstance(f[-1], str) and old in f[-1]:
                f[-1] = f[-1].replace(old, new, 1); print(tag, 'ok(foot)'); return
            if cells and it['kind'] == 'tbl' and isinstance(f[2], list):
                for row in f[2]:
                    for i, cell in enumerate(row):
                        if isinstance(cell, str) and old in cell:
                            row[i] = cell.replace(old, new, 1); print(tag, 'ok(cell)'); return
    print(tag, 'MISS'); FAIL.append(tag)

# ---------- ch1 contribution ----------
sw('is imposed on the planning layer.',
   'is imposed on the planning layer. The effect of the cap is verified at the causal level in a dose-response experiment restricted to settled encounters where the cap actually held (Chapter 5, Section 8).', 'c1')

# ---------- ch3 cap delivery ----------
sw('— and whose compliance was confirmed in measurements (a health-proportional cap was implemented but unused — Table 4-5). The cap is delivered via the Autoware speed-',
   '(a health-proportional cap was implemented but unused — Table 4-5). The cap is delivered via the Autoware speed-', 'm1a')
sw('and was corrected; the implementation lesson is to intervene on the input side of the arbiter.',
   'and was corrected — the lesson is to intervene on the input side of the arbiter. Second, a message published with a type different from the one the evaluated stack version subscribes to is silently discarded even on the same topic name — a post-campaign audit found that, due to this defect, the explicit cap had not actually been delivered in the campaign runs (discovered through the mismatch between publish logs and measured vehicle speed); after matching the type and adding periodic republication while moving, delivery and compliance were re-verified by measurement (Chapter 5, Section 8). The interface contract extends to the message type, not just the topic name, and a "publish log" is not evidence of delivery (Chapter 6, Section 4).', 'm1b')
sw('The cap is delivered via the Autoware speed-',
   'Two implementation defects were found and fixed on this delivery path by measurement. First, publishing directly to the cap output topic competes with the selector, ', 'm1c')

# ---------- ch4 design (v) ----------
sw('(specified in Chapter 5, Section 7). Adjudication follows the ledger standard',
   '(specified in Chapter 5, Section 7). (v) Speed-dose experiment: after fixing the cap-delivery defect, caps {4.2, 3.6, 3.0} m/s x spawn distances {6, 7, 8, 9} m x 10 seeds (reusing the ablation extension-round seeds S12–S21; gn-mid, injection fixed at 25 s) = 120 runs. Launch uses a settlement trigger rather than a time trigger — the pedestrian is spawned D m ahead at the moment the supervisor is in MRM_MOVE and the measured speed has stayed within the cap-specific band for 1.0 s continuously (spread <= 0.25 m/s) — so that "an encounter under an actually holding cap" is guaranteed at the trigger level. The three cap arms differ only in the value passed through the identical software path (the external velocity-limit interface) (Chapter 5, Section 8). Adjudication follows the ledger standard', 'm2')

# ---------- ch4 stats pre-registration ----------
sw('Three exposure metrics are defined:',
   'For the speed-dose experiment (Chapter 5, Section 8), a single primary endpoint — the paired collision difference between 4.2 and 3.0 m/s at the 8 m spawn (exact McNemar) — was pre-specified in a plan fixed before data collection (including the adoption rule, pinned by a repository commit); the remaining distance-cap combinations are reported only as boundary characterization (descriptive statistics with Wilson CIs). As a precondition check on encounter validity (manipulation check), a run with no launch within 420 s or with a first-tick encounter speed outside the band (0.15 m/s tolerance) is rejected and re-run under identical conditions regardless of its outcome (MANIPULATION_FAIL). Three exposure metrics are defined:', 'm3')

# ---------- ch4 tables ----------
sw('S02–S11 (10 seeds, shared across the four arms;', 'S02–S21 (20 seeds, shared across the four arms;', 'm4', cells=True)
sw('S02~S11 (10 seeds', 'S02~S21 (20 seeds', 'm4b', cells=True) if 'm4' in FAIL else None
sw('Simulator restarted for every case — blocks state accumulation',
   'Simulator restarted for every case — blocks state accumulation', 'noop-m5probe', cells=True)

# ---------- ch5a: 8 m encounter (s4) ----------
sw('in settled cruise under the 3.0 m/s speed cap avoided the pedestrian in all 8 runs',
   'in low-speed settled cruise (nominal 3.0 m/s cap configured; a post-hoc audit found the cap undelivered, the low speed stemming from the restart profile — Section 8 — while encounter speeds are verified by measurement) avoided the pedestrian in all 8 runs', 'e1')

# ---------- ch5a/ch5b renumber refs ----------
sw('detailed distributions are reported in Table 5-8, Section 8.',
   'detailed distributions are reported in Table 5-9, Section 9.', 'r5a', foot=True)

# ---------- ch5b: ablation reinterpretation ----------
sw('and 0:1 for A3↔A4 with p=1.0.',
   'and 0:1 for A3↔A4 with p=1.0. A post-campaign audit of the delivery path (Section 8) found that the explicit cap of A4 had never actually been delivered to the velocity-limit arbiter of the evaluated stack — the published message type differed from the subscribed type of the evaluated version and was silently discarded on the same topic name. A3 and A4 were therefore de facto repeated measurements of the same policy (naturally decelerating evacuation), and p=1.0 together with the two arms\' close collision counts (10/20 vs 11/20) is the consistent consequence — and, incidentally, evidence of seed-level repeatability.', 'e2')
sw('That is, no incremental collision reduction from the explicit speed cap was detected in this sample (this is the statement that "no additional collisions were prevented," not a claim of equivalence — the n=20 sample-size limitation is discussed in Chapter 6, Section 3).',
   'That is, this ablation turned out post hoc to be a design in which the increment of the explicit cap could not be tested (both arms were de facto uncapped), and the causal effect of the cap is verified in a separate dose-response experiment with the delivery fixed (Section 8).', 'e3')
sw('The A2 runs of S12 and S15 in the extension round were likewise filled by the same kind of rerun.',
   'The A2 runs of S12 and S15 in the extension round were likewise filled by the same kind of rerun. The explicit cap of A4 was found post hoc to be undelivered (Section 8), so A3 and A4 are de facto the same policy.', 'e4', foot=True)

# ---------- ch5b: two-regime (s6) ----------
sw('Splitting the encounter outcomes of the same capped evacuation policy (A4-type) by time regime',
   'Splitting the encounter outcomes of the same low-speed evacuation policy by time regime', 'e5a')
sw('whereas launches in settled cruise with deceleration complete (3.0 m/s restart cruise, 8 m encounter re-run) had 0/8 collisions.',
   'whereas launches in low-speed settled cruise with deceleration complete (restart cruise, 8 m encounter re-run; the nominal 3.0 m/s cap was configured but undelivered — the measured encounter speed of about 3.0 m/s stems from the restart profile, Section 8) had 0/8 collisions.', 'e5b')
sw('(b) the two-regime contrast of the same capped (3.0 m/s) evacuation policy',
   '(b) the two-regime contrast of the same low-speed evacuation policy', 'e6')

# ---------- ch5b: low-speed ladder (s7) ----------
sw('In settled cruise at the capped speed of 3.0 m/s, the boundary was measured empirically',
   'In low-speed settled cruise (nominal 3.0 m/s cap configured), the boundary was measured empirically', 'e7')
sw('the speed cap moved the boundary inward — is confirmed by measurement. Two points must be stated explicitly. First, the launch protocols differ',
   'the reduction of encounter speed moved the boundary inward — is confirmed by measurement. Three points must be stated explicitly. First, the explicit cap was undelivered in these ladder runs as well (Section 8) — the low speed stems from the restart acceleration profile, but since the comparison axis is the measured encounter speed the conclusion stands, and the controlled verification under an actually delivered cap is performed in Section 8. Second, the launch protocols differ', 'e8')
sw('Second, the measured boundary (7–8 m) lies outside the pure model prediction (5.79 m).',
   'Third, the measured boundary (7–8 m) lies outside the pure model prediction (5.79 m).', 'e9')
sw('the speed cap physically narrows the range of "unavoidable dart-outs,"',
   'low-speed encounters physically narrow the range of "unavoidable dart-outs,"', 'e10')

# ---------- new section 8 + hard-fail renumber ----------
NEW8 = [
 {'i': -1, 'kind': 'sec', 'fields': ['8. Causal Verification of the Speed Cap: A Dose-Response Experiment on Settled Encounters', 'ch5s8sd']},
 {'i': -1, 'kind': 'p', 'fields': ["The ablation of Section 5 could not test the increment of the explicit cap (a delivery defect), and the two ladders of Section 7 used different launch protocols. To close both gaps at once, a controlled dose-response experiment was performed, with the delivery fixed, exclusively on settled-state encounters in which the cap actually held. How the defect was discovered matters methodologically: cap publish logs were recorded normally throughout the campaigns, yet the tick logs showed the moving vehicle tracking the sectional speed limit rather than the cap. The cause was a published message type that differed from the subscribed type of the evaluated stack's selector, silently discarded on the same topic name — \"a publish log is not evidence of delivery\" (Chapter 6, Section 4). After matching the type and adding 1 s periodic republication while moving, delivery and compliance were re-verified by measurement before entering this experiment."]},
 {'i': -1, 'kind': 'p', 'fields': ['The design is a paired matrix of caps {4.2, 3.6, 3.0} m/s x spawn distances {6, 7, 8, 9} m x 10 seeds = 120 runs (Chapter 4, Sections 4 (v) and 7). The 4.2 m/s arm is a high-cap control practically equivalent to the road speed limit (15 km/h ≈ 4.17 m/s), and the three arms use the identical external velocity-limit interface differing only in the value, so there is no software-path difference. Launch uses the settlement trigger — the pedestrian is spawned D m ahead at the moment the supervisor is in MRM_MOVE and the measured speed has stayed within the cap-specific band for 1.0 s continuously (spread <= 0.25 m/s) — which, unlike the time trigger of the Section 5 ablation (detection + 3 s, transient), guarantees at the trigger level that the cap holds at the encounter. The primary endpoint (8 m, paired 4.2 vs 3.0 exact McNemar) and the manipulation-check adoption rule were pre-specified in a plan before data collection (Chapter 4, Section 7). Of 125 attempts, 120 runs were adopted; the 5 rejections (4 band-not-reached, 1 reverse-direction spawn) were precondition violations rejected and re-run before their outcomes were examined. Adjudication is based on the ego ledger (RAW-HIT).']},
 {'i': -1, 'kind': 'tbl', 'fields': ['Table 5-8. Speed-dose experiment — collisions in settled encounters (n=10 seeds per cell, ledger adjudication)', 'tbl5_sd',
   [['Speed cap', '6 m', '7 m', '8 m', '9 m', 'Estimated boundary'],
    ['4.2 m/s (high-cap control)', '10/10', '10/10', '10/10', '10/10', 'beyond 9 m'],
    ['3.6 m/s', '10/10', '10/10', '10/10', '2/10', 'about 9 m'],
    ['3.0 m/s (policy value)', '8/10', '5/10', '0/10', '0/10', 'about 7 m']],
   'Manipulation check (measured speed at the first encounter tick): 4.2 arm 4.05–4.13 (median 4.08), 3.6 arm 3.37–3.58 (median 3.52), 3.0 arm 2.60–3.07 (median 2.81) m/s — every run within the required band (0.15 m/s tolerance). Minimum pedestrian gaps in avoidance runs are 1.8–5.4 m, i.e., all genuine encounters.']},
 {'i': -1, 'kind': 'p', 'fields': ["The results are monotone along both axes (Table 5-8, Figure 5-6). At the pre-specified primary endpoint — the 8 m encounter — cap 4.2 collided in all ten seeds and cap 3.0 avoided in all ten, giving discordant pairs 10:0 and an exact McNemar two-sided p=0.002: the collision-reduction effect of the explicit cap, untestable in Section 5, is detected with unanimous seed-level directionality once the cap actually holds at the encounter. In the boundary characterization, the avoid/collide boundary is beyond 9 m at 4.2 m/s (consistent with the 8–11 m ladder of Section 3), about 9 m at 3.6 m/s (2/10 at 9 m), and about 7 m at 3.0 m/s (5/10 at 7 m, 0/10 at 8 m and beyond) — moving inward monotonically as the cap is lowered. In particular, the 5/10 of the 3.0 arm at 7 m falls in the middle of the boundary interval (7–8 m) estimated by the Section 7 low-speed ladder, a mutual corroboration."]},
 {'i': -1, 'kind': 'fig', 'fields': ['Figure 5-6. Speed-dose experiment (120 runs, ledger adjudication). (a) Collision rate vs spawn distance per cap (Wilson 95% CI) — the avoid/collide boundary moves inward monotonically as the cap is lowered. (b) Pre-specified primary contrast (8 m): cap 4.2 m/s collided in 10/10, cap 3.0 m/s in 0/10 — discordant pairs 10:0, exact McNemar p=0.002.', 'fig5_6sd', '/home/taewook/autoware_carla_leaderboard/doc/paper_build/figs/fig13_speeddose.png', None, 14.0]},
 {'i': -1, 'kind': 'p', 'fields': ["The limits of interpretation are stated explicitly. This causal conclusion is restricted to the settled regime in which the cap holds; the transient risk before deceleration completes (Sections 5–6, 11/20) is outside the scope of this experiment — the cap does not remove the transient, it creates the physical safety margin after settling. No optimality claim is made for the 3.0 m/s value (the onset of collapse of the 3.6 arm at 9 m only locates the boundary of an intermediate dose), and the restrictions of n=10 per cell and a single fault (gn-mid) on a single evacuation corridor also remain."]},
]
ins = None
for idx, it in enumerate(tr['ch5b']['items']):
    if it['kind'] == 'sec' and it['fields'][0].startswith('8. Hard-Fail'):
        ins = idx; break
assert ins is not None, 'hard-fail sec not found'
tr['ch5b']['items'][ins]['fields'][0] = '9. Hard-Fail Decision Latency: Verifying the 1.5 s Deadline'
tr['ch5b']['items'][ins:ins] = NEW8
print('new8+renumber ok at', ins)
sw('Table 5-8. Hard-fail detection and decision latency',
   'Table 5-9. Hard-fail detection and decision latency', 'r2')
sw('verified with ledger-based simulation time across the full cf/lf matrix (Table 5-8, Figure 5-1)',
   'verified with ledger-based simulation time across the full cf/lf matrix (Table 5-9, Figure 5-1)', 'r3')

# ---------- ch6 ----------
sw('3. The Role of the Speed Cap and the Undetected Increment',
   "3. The Role of the Speed Cap: Causal Effect and Limits", 'd1')
for it in tr['ch6']['items']:
    f = it['fields']
    if isinstance(f[0], str) and "redefines the cap's role" in f[0]:
        f[0] = ("The null A3↔A4 difference in the ablation (Chapter 5, Section 5) was not an absence of a cap effect but an inability to test it — a delivery defect made both arms de facto uncapped, a post-hoc finding that itself extends the adjudication methodology (Section 4). With the delivery fixed and encounters controlled to the settled regime in which the cap actually holds, the dose-response experiment (Chapter 5, Section 8) detected the causal effect of the cap: paired discordance 10:0 at 8 m (p=0.002) and a monotone inward shift of the boundary (beyond 9 m to about 7 m). The cap's role is thus twofold — in the settled regime it verifiably moves the avoidance boundary inward, while in the transient it does not yet hold (measured transient encounter speeds 3.5–3.8 m/s, 11/20 collisions). That is, the cap's value is an explicit re-acceleration-suppressing upper bound that does not depend on natural deceleration, but its protection is effective only after deceleration completes. The 3.0 m/s value is grounded but not claimed optimal (the 9 m boundary of the 3.6 arm only locates an intermediate dose), nor is it a formal closed-loop speed guarantee.")
        print('d2 ok'); break
else:
    print('d2 MISS'); FAIL.append('d2')
sw('In particular, the error of reading "absence of a record" as "absence of an event"',
   'The cap non-delivery incident (Chapter 5, Section 8) is the interface edition of the same lesson — a publish log is not evidence of delivery, the interface contract extends to the message type rather than just the topic name, and actuation commands must be verified by their downstream effect (measured vehicle speed). In particular, the error of reading "absence of a record" as "absence of an event"', 'd3')
sw('The per-speed boundaries (8–11 m, 7–8 m) are values for the low-speed ODD',
   'The per-speed boundaries (8–11 m, 7–8 m) and the dose-response results (Chapter 5, Section 8) are values for the low-speed ODD', 'd4')

# ---------- ch7 ----------
sw('and the stock stack under continued driving in 14/20, while the same evacuation p',
   'and the stock stack under continued driving in 14/20, while the same evacuation p', 'g1probe')
for it in tr['ch7']['items']:
    f = it['fields']
    if isinstance(f[0], str) and '10–11/20 (all during the transient)' in f[0]:
        m = re.search(r'(while the same [^.]*0/8[^.]*\.)', f[0])
        assert m, 'g1 sentence not found'
        f[0] = f[0].replace(m.group(1), m.group(1) + ' After the explicit cap of the ablation was found post hoc to be nullified by a delivery defect and fixed, a dose-response experiment on settled encounters where the cap actually held (3 caps x 4 distances x 10 seeds = 120 runs, pre-registered) detected the collision-reduction effect of cap 4.2 vs 3.0 m/s with paired discordance 10:0 at 8 m (exact McNemar p=0.002), and the avoid/collide boundary moved inward monotonically as the cap was lowered (beyond 9 m to about 7 m).', 1)
        print('g1 ok'); break
else:
    print('g1 MISS'); FAIL.append('g1')
sw('Second, the residual risk of evacuation is concentrated in the post-detection transient (from detection until the settled speed is reached) — a statement restricted to the single launch instant (detection + 3 s) of the ablation',
   'Second, the residual risk of evacuation is concentrated in the post-detection transient (from detection until the settled speed is reached), while low speed after settling verifiably moves the avoidance boundary inward (transient 11/20 vs settled 0/8; dose-response 10:0, p=0.002) — the transient statement is restricted to the single launch instant (detection + 3 s) of the ablation', 'g2')
sw('formalizing the detection budget (explicit reservation of FRTI and margin, and q',
   'formalizing the detection budget (explicit reservation of FRTI and margin, and q', 'g3probe')
for it in tr['ch7']['items']:
    f = it['fields']
    if isinstance(f[0], str) and f[0].startswith('Future work'):
        assert 'implemented, unevaluated' in f[0] or 'implemented but unevaluated' in f[0] or True
        if 'extending the dose-response experiment' not in f[0]:
            f[0] = f[0].replace('; and validation on a real vehicle',
                                '; extending the dose-response experiment to multiple faults and corridors; and validation on a real vehicle', 1)
            if 'extending the dose-response experiment' not in f[0]:
                print('g3 MISS'); FAIL.append('g3')
            else:
                print('g3 ok')
        break

json.dump(tr, open(TP, 'w'), ensure_ascii=False, indent=1)
print('saved. FAIL:', FAIL)
