# -*- coding: utf-8 -*-
"""v19 마무리: 표 5-7 ZZ 센티널 채움 → 그림 5-7(b) 전수 데이터 재생성 →
2회 빌드(페이지맵 수렴) → 검증. cf v7 완료 후 실행 (cron 또는 수동).
성공 시 FINALIZE_OK.marker 생성."""
import csv, glob, os, re, subprocess, sys
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
R = '/home/taewook/autoware_carla_leaderboard/experiments/results'
LF_WIN = (1787460000.0, 1787497800.0)   # v7 lf 구간 (0823 14:11~0824 00:05)
CF_START = 1787497800.0                  # cf v7 시작 (0824 00:10)
BAD = {'CARLA_DIED', 'SETUP_FAIL', 'TIMEOUT'}
MRM_OK = {'SHOULDER_SUCCESS', 'PARKED_SUCCESS', 'AW_COMFORTABLE_STOP_DONE',
          'AW_EMERGENCY_STOP_DONE', 'DEFER_STOPPED(log)', 'SHOULDER_SUCCESS(log)'}


def ledger_pairs():
    fl = [l.split() for l in open(f'{R}/fault_ledger.log')]
    ev = [l.split(maxsplit=3) for l in open(f'{R}/sup_events.log')]
    tr = [e for e in ev if len(e) > 3 and e[2] == 'TRANSITION'
          and e[3].startswith('NORMAL->')]
    out = []
    for f_ in fl:
        tw = float(f_[0]); fs = float(f_[2].split('=')[1])
        if fs < 0:
            continue
        nxt = [e for e in tr if float(e[0]) > tw and float(e[0]) - tw < 60]
        if not nxt:
            continue
        d = float(nxt[0][1].split('=')[1]) - fs
        m = 'baseline' if 'baseline' in nxt[0][3] else 'ours'
        out.append((tw, m, d))
    return out


def csv_rows(logfile):
    rows = []
    for line in open(logfile):
        m = re.search(r'(results_\d+_\d+\.csv)', line)
        if m:
            rows += list(csv.DictReader(open(f'{R}/{m.group(1)}')))
            break
    return rows


def main():
    cflog = f'{R}/hardfast_v7_cf_0823.log'
    assert 'cf v7 done' in open(cflog).read(), 'cf 미완료'
    pairs = ledger_pairs()
    lf = [(m, d) for tw, m, d in pairs if LF_WIN[0] < tw < LF_WIN[1]]
    cf = [(m, d) for tw, m, d in pairs if tw >= CF_START]
    lf_rows = csv_rows(f'{R}/hardfast_v7_lf_0823.log')
    cf_rows = csv_rows(cflog)

    stats, all_d = {}, []
    for fault, data, rows in (('cf', cf, cf_rows), ('lf', lf, lf_rows)):
        for m in ('ours', 'baseline'):
            d = np.array([x for mm, x in data if mm == m])
            valid = [r for r in rows if r['method'] == m
                     and r['outcome'] not in BAD]
            ok = sum(1 for r in valid if r['outcome'] in MRM_OK)
            assert len(d) >= 30, (fault, m, len(d))
            stats[(fault, m)] = dict(
                n=len(d), med=np.median(d), p95=np.percentile(d, 95),
                mx=d.max(), viol=int((d > 1.5).sum()),
                mrm=f'{ok}/{len(valid)}')
            all_d.append(d)
    alld = np.concatenate(all_d)

    # ── 표 5-7 채움 ──
    p = f'{D}/content3.py'
    s = open(p).read()
    order = [('cf', 'ours'), ('cf', 'baseline'), ('lf', 'ours'), ('lf', 'baseline')]
    for (fault, m) in order:
        st = stats[(fault, m)]
        cells = (f"'{st['n']}', '{st['med']:.2f}', '{st['p95']:.2f}', "
                 f"'{st['mx']:.2f}', '{st['viol']}건', '{st['mrm']}'")
        s = s.replace("'ZZ', 'ZZ', 'ZZ', 'ZZ', 'ZZ', 'ZZ'", cells, 1)
    s = s.replace('ZZMAXALL', f'{alld.max():.2f}')
    s = s.replace('ZZVIOL', f'{int((alld > 1.5).sum())}건')
    s = s.replace('ZZNTOT', f'{len(alld)}')
    import re as _re
    assert not _re.search(r"'ZZ'|ZZMAXALL|ZZVIOL|ZZNTOT", s), '센티널 잔존'
    open(p, 'w').write(s)
    compile(s, p, 'exec')

    # ── 그림 5-7 재생성 (전수 데이터) ──
    sys.path.insert(0, '/home/taewook/autoware_carla_leaderboard/experiments/analysis')
    import matplotlib
    matplotlib.use('Agg')
    import ieee_style as ie
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.9),
                               gridspec_kw={'width_ratios': [1.15, 1]})
    rows_a = [('신 경로 (하드페일 공통)', [('감지·판정', 1.0, ie.RED)]),
              ('구: 후보 전멸 경로', [('감지', 0.95, '#888888'), ('선정 계산', 1.0, '#b8b8b8'), ('재시도 대기', 2.0, '#d9d9d9')]),
              ('구: 전방 시야 게이트', [('감지', 0.95, '#888888'), ('회복 유예', 5.0, '#d9d9d9')]),
              ('구: 이동 대피 경로', [('감지', 0.95, '#888888'), ('밴드 확인', 1.0, '#b8b8b8'), ('선정 계산', 1.5, '#d9d9d9')])]
    ys = np.arange(len(rows_a))[::-1]
    for yi, (name, segs) in zip(ys, rows_a):
        x0 = 0
        for lab, w, c in segs:
            a.barh(yi, w, left=x0, height=0.52, color=c, edgecolor='black', lw=0.4)
            if w >= 0.9:
                a.text(x0 + w / 2, yi, lab, ha='center', va='center', fontsize=5.6)
            x0 += w
        a.text(x0 + 0.12, yi, f'{x0:.1f} s', va='center', fontsize=6.5)
    a.axvline(1.5, color=ie.RED, lw=0.9, ls='--')
    a.text(1.55, 3.42, '마감 1.5 s', color=ie.RED, fontsize=6.2)
    a.set_yticks(ys); a.set_yticklabels([r[0] for r in rows_a], fontsize=6.5)
    a.set_xlabel('판정 완료까지 지연 예산 [s] (심시간)')
    a.set_xlim(0, 7.2); ie.clean_axes(a); a.grid(True, axis='x')
    ie.panel_label(a, '(a)', x=0.9)
    groups = [('cf-제안', [x for m, x in cf if m == 'ours']),
              ('cf-baseline', [x for m, x in cf if m == 'baseline']),
              ('lf-제안', [x for m, x in lf if m == 'ours']),
              ('lf-baseline', [x for m, x in lf if m == 'baseline'])]
    rng = np.random.default_rng(1)
    for i, (name, d) in enumerate(groups):
        d = np.array(d)
        b.scatter(np.full(len(d), i) + rng.normal(0, 0.06, len(d)), d, s=6,
                  color=ie.RED, alpha=0.4, linewidths=0)
        b.plot([i - 0.18, i + 0.18], [np.median(d)] * 2, color='black', lw=1.6)
    for i, old in [(0, 4.2), (1, 4.2), (2, 3.9), (3, 3.9)]:
        b.plot(i, old, marker='D', mfc='none', mec=ie.GRAY, ms=4, ls='none')
    b.plot([], [], marker='D', mfc='none', mec=ie.GRAY, ls='none',
           label='구 경로 중앙값 (벽시계·본 캠페인)')
    b.axhline(1.5, color=ie.RED, lw=0.9, ls='--')
    b.text(0.05, 1.58, '마감 1.5 s', color=ie.RED, fontsize=6.2)
    b.set_xticks(range(4))
    b.set_xticklabels([f'{g[0]}\n(n={len(g[1])})' for g in groups], fontsize=6)
    b.set_ylabel('감지·판정 지연 [s] (심시간)')
    b.set_ylim(0, 4.6); b.legend(loc='center right', fontsize=5.6)
    ie.clean_axes(b); b.grid(True, axis='y')
    ie.panel_label(b, '(b)')
    plt.tight_layout()
    plt.savefig('/home/taewook/autoware_carla_leaderboard/doc/figs/fig_hardfail_latency.png')
    plt.close()

    # ── 2회 빌드 ──
    env = dict(os.environ, HOME='/home/taewook')
    for _ in range(2):
        subprocess.run(['python3', f'{D}/build.py'], check=True, env=env)
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                        '/home/taewook/autoware_carla_leaderboard/doc/thesis_v19_0822.docx',
                        '--outdir', '/home/taewook/autoware_carla_leaderboard/doc'],
                       check=True, env=env)
        subprocess.run(['python3', f'{D}/map_pages.py'], check=True, env=env,
                       cwd=D)
    txt = subprocess.run(['pdftotext',
                          '/home/taewook/autoware_carla_leaderboard/doc/thesis_v19_0822.pdf',
                          '-'], capture_output=True, text=True).stdout
    assert "'ZZ'" not in txt and 'ZZMAXALL' not in txt, 'PDF에 센티널 잔존'
    open(f'{D}/FINALIZE_OK.marker', 'w').write('ok\n')
    print('FINALIZE OK')


if __name__ == '__main__':
    main()
