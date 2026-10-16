#!/usr/bin/env python3
"""Builds docs/SPECIFICATION.md. The tables come from tools/build_dctl.py, so the spec can't drift from the DCTLs.

    python3 tools/build_spec.py
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_dctl as B  # noqa: E402

VERSION = B.VERSION


def npm(p, w):
    xyz = lambda x, y: np.array([x / y, 1.0, (1 - x - y) / y])
    P = np.stack([xyz(p[0], p[1]), xyz(p[2], p[3]), xyz(p[4], p[5])], axis=1)
    return P * np.linalg.solve(P, xyz(*w))


def fmt_m(M):
    return '\n'.join(' '.join(f'{v:9.6f}' for v in row) for row in M)


STATUS = {
    'KWG': 'Published: Kinefinity KineLog3 spec v2',
    'KWG8K': '**Provisional**: no published primaries yet; uses Kinefinity Wide Gamut',
    'KWGVST': '**Provisional**: no published primaries yet; uses Kinefinity Wide Gamut',
    'KBT2020': 'Exact: KineOS 8 "BT.2020" gamut = ITU-R BT.2020',
    'DGAMUT': 'Published: DJI D-Log/D-Gamut white papers (X7 2017, X9 2022)',
}

CURVE_DEF = {
    'LIN':     ('Identity', '-'),
    'KL3':     ('x ≥ −0.008239: 0.296·0.907136·log10(66.64x + 1) + 0.092864; else (x + 0.008239)/0.017178',
                'Kinefinity KineLog3 spec v2'),
    'LOGC3':   ('x > 0.010591: 0.247190·log10(5.555556x + 0.052272) + 0.385537; else 5.367655x + 0.092809 (EI 800)',
                'ARRI LogC3 (SUP 3.x, scene-linear)'),
    'LOGC4':   ('x ≥ t: ((log2(a·x + 64) − 6)/14)·b + c; else (x − t)/s; a = (2^18 − 16)/117.45, b = 928/1023, c = 95/1023',
                'ARRI LogC4 specification'),
    'DI':      ('x > 0.00262409: (log2(x + 0.0075) + 7)·0.07329248; else 10.44426855x',
                'Blackmagic DaVinci Wide Gamut / Intermediate'),
    'SLOG3':   ('x ≥ 0.01125: (420 + 261.5·log10((x + 0.01)/0.19))/1023; else (76.2102946929x/0.01125 + 95)/1023',
                'Sony S-Log3 technical summary'),
    'L3G10':   ('t = x + 0.01; t ≥ 0: 0.224282·log10(155.975327t + 1); else 15.1927t', 'RED Log3G10 (IPP2)'),
    'VLOG':    ('x ≥ 0.01: 0.241514·log10(x + 0.00873) + 0.598206; else 5.6x + 0.125', 'Panasonic V-Log/V-Gamut'),
    'CLOG3':   ('t = x/0.9; |t| ≤ 0.014: 1.9754798t + 0.12512219; t > 0.014: 0.36726845·log10(14.98325t + 1) + 0.12240537; '
                't < −0.014: −0.36726845·log10(1 − 14.98325t) + 0.12783901', 'Canon Log 3 (v1.2)'),
    'BMDG5':   ('x ≥ 0.005: 0.0869287607·ln(x + 0.0054940724) + 0.5300133392; else 8.2836059324x + 0.0924657534',
                'Blackmagic Film Generation 5'),
    'FLOG2':   ('x ≥ 0.000889: 0.245281·log10(5.555556x + 0.064829) + 0.384316; else 8.799461x + 0.092864',
                'Fujifilm F-Log2 data sheet'),
    'ACESCCT': ('x > 0.0078125: (log2(x) + 9.72)/17.52; else 10.5402377416545x + 0.0729055341958355', 'AMPAS S-2016-001'),
    'ACESCC':  ('x ≤ 0: −0.3584474886; x < 2^−15: (log2(2^−16 + x/2) + 9.72)/17.52; else (log2(x) + 9.72)/17.52',
                'AMPAS S-2014-003'),
    'R709':    ('x < 0.018: 4.5x; else 1.099x^0.45 − 0.099 (sign-mirrored)', 'ITU-R BT.709 OETF'),
    'SRGB':    ('x ≤ 0.0031308: 12.92x; else 1.055x^(1/2.4) − 0.055 (sign-mirrored)', 'IEC 61966-2-1'),
    'G22':     ('x^(1/2.2) (sign-mirrored)', 'Pure power'),
    'G24':     ('x^(1/2.4) (sign-mirrored)', 'Pure power (BT.1886 inverse, black = 0)'),
    'G26':     ('x^(1/2.6) (sign-mirrored)', 'Pure power'),
    'PQ':      ('SMPTE ST 2084 inverse EOTF of 100·x cd/m² (linear 1.0 = 100 nits)', 'SMPTE ST 2084'),
    'DLOG':    ('x ≤ 0.0078: 6.025x + 0.0929; else 0.256663·log10(0.9892x + 0.0108) + 0.584555',
                'DJI D-Log/D-Gamut white papers'),
}


def tables():
    gam = ['| # | Color space | x R | y R | x G | y G | x B | y B | x W | y W | Status / source |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    for i, (gid, name, p, w) in enumerate(B.GAMUTS):
        st = STATUS.get(gid, 'Manufacturer / standards body specification')
        gam.append(f'| {i} | {name} | ' + ' | '.join(str(v) for v in p + w) + f' | {st} |')
    cur = ['| # | Gamma | Linear → encoded (decode is the exact inverse) | Source |', '|---|---|---|---|']
    for i, (cid, name) in enumerate(B.CURVES):
        f, src = CURVE_DEF[cid]
        cur.append(f'| {i} | {name} | {f} | {src} |')
    ei = ['| # | EI | cut | a | b | c | d | e | f |', '|---|---|---|---|---|---|---|---|---|']
    for i, e in enumerate(sorted(B._LOGC3)):
        ei.append(f'| {i} | {e} | ' + ' | '.join(str(v) for v in B._LOGC3[e]) + ' |')
    return '\n'.join(gam), '\n'.join(cur), '\n'.join(ei)


def main():
    gam, cur, ei = tables()
    kwg = npm(B.GAMUTS[0][2], B.GAMUTS[0][3])
    dg = npm(*[(g[2], g[3]) for g in B.GAMUTS if g[0] == 'DGAMUT'][0])
    awg3 = npm(*[(g[2], g[3]) for g in B.GAMUTS if g[0] == 'AWG3'][0])
    dwg = npm(*[(g[2], g[3]) for g in B.GAMUTS if g[0] == 'DWG'][0])
    r2020 = npm(*[(g[2], g[3]) for g in B.GAMUTS if g[0] == 'REC2020'][0])
    src = open(os.path.join(HERE, 'SPECIFICATION.template.md')).read()
    out = (src.replace('{{VERSION}}', VERSION).replace('{{GAMUT_TABLE}}', gam).replace('{{CURVE_TABLE}}', cur)
              .replace('{{LOGC3_TABLE}}', ei)
              .replace('{{KWG_XYZ}}', fmt_m(kwg)).replace('{{XYZ_KWG}}', fmt_m(np.linalg.inv(kwg)))
              .replace('{{KWG_2020}}', fmt_m(np.linalg.inv(r2020) @ kwg))
              .replace('{{KWG_AWG3}}', fmt_m(np.linalg.inv(awg3) @ kwg))
              .replace('{{KWG_DWG}}', fmt_m(np.linalg.inv(dwg) @ kwg))
              .replace('{{DG_XYZ}}', fmt_m(dg)).replace('{{DG_AWG3}}', fmt_m(np.linalg.inv(awg3) @ dg))
              .replace('{{DG_DWG}}', fmt_m(np.linalg.inv(dwg) @ dg)))
    assert '{{' not in out, 'unfilled placeholder'
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    path = os.path.join(ROOT, 'docs', 'SPECIFICATION.md')
    open(path, 'w').write(out)
    print('wrote', path)


if __name__ == '__main__':
    main()
