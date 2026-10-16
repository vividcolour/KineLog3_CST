#!/usr/bin/env python3
"""
Test suite for Color Space Transform mk2 and Color Remap mk2.

    pip install -r tests/requirements.txt
    python3 tests/run_tests.py            # all backends available on this machine
    python3 tests/run_tests.py --quick    # fewer samples

Checks every curve, every gamut pair and every Remap setting against independent references
(colour-science + the manufacturers' published numbers), on C++, C99 and OpenCL builds.
"""
import argparse, os, sys, time, warnings
import numpy as np

warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import colour                      # noqa: E402
import dctl_harness as H           # noqa: E402
import build_dctl as B             # noqa: E402

CST = os.path.join(ROOT, 'dctl', B.CST_NAME)
REMAP = os.path.join(ROOT, 'dctl', B.REMAP_NAME)
M = colour.models

GAMUT_IDS = [g[0] for g in B.GAMUTS]
CURVE_IDS = [c[0] for c in B.CURVES]
G = {k: i for i, k in enumerate(GAMUT_IDS)}
C = {k: i for i, k in enumerate(CURVE_IDS)}

# ------------------------------------------------------------------ references
def kl3_enc(x):
    a, b, c, d, cut, s = 66.64, 0.296, 0.907136, 0.092864, -0.008239, 0.017178
    x = np.asarray(x, float)
    return np.where(x < cut, (x - cut) / s, np.log10(np.maximum(a * x + 1, 1e-30)) * b * c + d)

REF_ENC = {
    'LIN': lambda x: x, 'KL3': kl3_enc, 'LOGC3': M.log_encoding_ARRILogC3, 'LOGC4': M.log_encoding_ARRILogC4,
    'DI': M.oetf_DaVinciIntermediate, 'SLOG3': M.log_encoding_SLog3, 'L3G10': M.log_encoding_Log3G10,
    'VLOG': M.log_encoding_VLog, 'CLOG3': M.log_encoding_CanonLog3, 'BMDG5': M.oetf_BlackmagicFilmGeneration5,
    'FLOG2': M.log_encoding_FLog2, 'ACESCCT': M.log_encoding_ACEScct, 'ACESCC': M.log_encoding_ACEScc,
    'R709': M.oetf_BT709, 'SRGB': M.eotf_inverse_sRGB, 'G22': lambda x: np.power(x, 1 / 2.2),
    'G24': lambda x: np.power(x, 1 / 2.4), 'G26': lambda x: np.power(x, 1 / 2.6),
    'PQ': lambda x: M.eotf_inverse_ST2084(np.asarray(x) * 100.0), 'DLOG': M.log_encoding_DJIDLog,
}
CS_NAME = {'AWG3': 'ARRI Wide Gamut 3', 'AWG4': 'ARRI Wide Gamut 4', 'DWG': 'DaVinci Wide Gamut',
           'REC709': 'ITU-R BT.709', 'REC2020': 'ITU-R BT.2020', 'P3D65': 'P3-D65', 'P3DCI': 'DCI-P3',
           'AP0': 'ACES2065-1', 'AP1': 'ACEScg', 'SG3': 'S-Gamut3', 'SG3C': 'S-Gamut3.Cine',
           'RWG': 'REDWideGamutRGB', 'VGAMUT': 'V-Gamut', 'CINEMA': 'Cinema Gamut',
           'BMDWG': 'Blackmagic Wide Gamut', 'FGAMUT': 'ITU-R BT.2020'}

def ref_space(gid):
    if gid == 'KBT2020':
        return colour.RGB_COLOURSPACES['ITU-R BT.2020']
    if gid in ('KWG', 'KWG8K', 'KWGVST'):   # Kinefinity spec primaries
        return colour.RGB_Colourspace('KWG', np.array([[0.7571, 0.2282], [0.2139, 1.1480], [0.0536, -0.2236]]),
                                      np.array([0.3127, 0.3290]))
    if gid == 'DGAMUT':  # DJI white-paper primaries (colour-science uses DJI's 4-decimal rounded matrix instead)
        return colour.RGB_Colourspace('D-Gamut', np.array([[0.71, 0.31], [0.21, 0.88], [0.09, -0.08]]),
                                      np.array([0.3127, 0.3290]))
    return colour.RGB_COLOURSPACES[CS_NAME[gid]]

# ------------------------------------------------------------------ tiny test framework
RESULTS = []
GHA = os.environ.get('GITHUB_ACTIONS') == 'true'

def gha(level, title, msg):
    """On GitHub Actions, also emit an annotation so failures are visible on the run page without the log."""
    if GHA:
        clean = lambda t: str(t).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::{level} title={clean(title)}::{clean(msg)}', flush=True)

def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok), detail))
    print(f'  [{"PASS" if ok else "FAIL"}] {name}' + (f'  ({detail})' if detail else ''), flush=True)
    if not ok:
        gha('error', f'FAIL: {name}', detail)

def pixel_rel(a, b, floor=1e-3):
    """Colour error relative to the pixel's brightness (max |channel|), in linear light."""
    return np.max(np.abs(a - b) / np.maximum(np.abs(b).max(1, keepdims=True), floor))

def rel_err(a, b, floor=1e-3):
    return np.max(np.abs(a - b) / np.maximum(np.abs(b), floor))

# ------------------------------------------------------------------ tests
def test_spec_anchors(cst):
    print('\nManufacturer reference values')
    grey = lambda gamma: cst.run([[G['KWG'], C['LIN'], G['KWG'], C[gamma], 0]], [[0.18] * 3])[0, 0]
    v = cst.run([[0, C['LIN'], 0, C['KL3'], 0]], [[0.0] * 3, [0.18] * 3, [0.90] * 3])[:, 0] * 100
    check('KineLog3 18% grey = 39.2 IRE (Kinefinity spec)', abs(v[1] - 39.2) < 0.05, f'{v[1]:.2f}')
    check('KineLog3 90% white = 57.2 IRE (Kinefinity spec)', abs(v[2] - 57.2) < 0.05, f'{v[2]:.2f}')
    check('KineLog3 0% black = 9.29 (0.0929 code value)', abs(v[0] - 9.2864) < 0.01, f'{v[0]:.3f}')
    d = grey('DLOG') * 1023
    check('DJI D-Log 18% grey = 408 10-bit (DJI X9 white paper)', abs(d - 408) < 0.6, f'{d:.1f}')
    check('ARRI LogC3 EI800 18% grey = 0.3910', abs(grey('LOGC3') - 0.391007) < 2e-5, f'{grey("LOGC3"):.5f}')
    check('ARRI LogC4 18% grey = 0.2784', abs(grey('LOGC4') - 0.278395) < 2e-5, f'{grey("LOGC4"):.5f}')
    check('DaVinci Intermediate 18% grey = 0.3360', abs(grey('DI') - 0.336043) < 2e-5, f'{grey("DI"):.5f}')
    check('Sony S-Log3 18% grey = 420/1023', abs(grey('SLOG3') * 1023 - 420) < 0.05, f'{grey("SLOG3")*1023:.2f}')
    # published matrices (4 decimals) - columns of the DCTL matrix = images of R, G, B unit vectors
    eye = np.eye(3)
    ap0 = cst.run([[G['KWG'], 0, G['AP0'], 0, 2]], eye).T  # KWG -> AP0, no CAT -> derive KWG->XYZ via colour
    kwg_xyz = colour.RGB_COLOURSPACES['ACES2065-1'].matrix_RGB_to_XYZ @ ap0
    pub = np.array([[0.6879, 0.1979, 0.0646], [0.2073, 1.0622, -0.2696], [0.0134, -0.3349, 1.4106]])
    check('KWG -> XYZ matches Kinefinity published matrix', np.abs(kwg_xyz - pub).max() < 1e-4,
          f'max diff {np.abs(kwg_xyz - pub).max():.1e}')
    pub2020 = np.array([[1.1038, 0.0468, -0.1506], [-0.1232, 1.5798, -0.4566], [0.0158, -0.3574, 1.3416]])
    m2020 = cst.run([[G['KWG'], 0, G['REC2020'], 0, 0]], eye).T
    check('KWG -> Rec.2020 matches Kinefinity published matrix', np.abs(m2020 - pub2020).max() < 1e-4,
          f'max diff {np.abs(m2020 - pub2020).max():.1e}')
    kb = cst.run([[G['KBT2020'], 0, G['REC2020'], 0, 0]], eye).T
    check('Kinefinity BT.2020 mode == ITU-R BT.2020 exactly', np.array_equal(kb, eye) or np.abs(kb - eye).max() < 1e-6,
          f'max diff {np.abs(kb - eye).max():.1e}')
    for gid in ('KWG8K', 'KWGVST'):
        mk = cst.run([[G[gid], 0, G['KWG'], 0, 0]], eye).T
        check(f'{gid} (provisional) currently == published Kinefinity Wide Gamut', np.abs(mk - eye).max() < 1e-6,
              f'max diff {np.abs(mk - eye).max():.1e}')
    v1 = np.array([[1.1273, 0.0479, -0.1526], [-0.1259, 1.6209, -0.4626], [0.0162, -0.3666, 1.3597]])
    check('KineLog3 spec v1 matrix is NOT white-preserving (why v2 is used)', np.abs(v1.sum(1) - 1).max() > 0.02,
          f'v1 row sums {np.round(v1.sum(1), 4).tolist()}, ours {np.round(m2020.sum(1), 4).tolist()}')
    dji = np.array([[0.6482, 0.1940, 0.1082], [0.2830, 0.8132, -0.0962], [-0.0183, -0.0832, 1.1903]])
    mdg = colour.RGB_COLOURSPACES['ACES2065-1'].matrix_RGB_to_XYZ @ cst.run([[G['DGAMUT'], 0, G['AP0'], 0, 2]], eye).T
    check('D-Gamut -> XYZ matches DJI published matrix (4 dp, rounded)', np.abs(mdg - dji).max() < 3e-4,
          f'max diff {np.abs(mdg - dji).max():.1e}')


def test_curves(cst, n):
    print('\nTransfer functions vs colour-science (encode and decode)')
    lin = np.concatenate([[0.0, 0.18, 0.9, 1.0], np.geomspace(1e-4, 40, n)])
    for cid in CURVE_IDS:
        x = lin[lin <= 100] if cid == 'PQ' else lin
        ref = REF_ENC[cid](x)
        enc = cst.run([[0, C['LIN'], 0, C[cid], 0]], np.repeat(x[:, None], 3, 1))[:, 0]
        dec = cst.run([[0, C[cid], 0, C['LIN'], 0]], np.repeat(np.asarray(ref)[:, None], 3, 1))[:, 0]
        ee, de = np.max(np.abs(enc - ref)), rel_err(dec, x)
        check(f'{cid:<8} encode / decode', ee < 2e-5 and de < 1e-4, f'enc {ee:.1e}, dec rel {de:.1e}')


def test_round_trip(cst):
    print('\nRound trips incl. toe and negative values (-0.05 .. 1.0), monotonic decode')
    y = np.linspace(-0.05, 1.0, 2101); Y = np.repeat(y[:, None], 3, 1)
    for cid in CURVE_IDS:
        lin = cst.run([[3, C[cid], 3, C['LIN'], 0]], Y)
        rt = cst.run([[3, C['LIN'], 3, C[cid], 0]], lin)[:, 0]
        err = np.max(np.abs(rt - y))
        # BT.709 OETF is (by the standard) not exactly invertible at its 0.018 knee: 2.5e-4 jump
        tol = 3e-4 if cid == 'R709' else (2e-5 if cid != 'PQ' else 5e-5)
        mono = cid == 'ACESCC' or np.all(np.diff(lin[:, 0]) > 0)  # ACEScc clamps below 0 by definition
        check(f'{cid:<8} round trip / monotonic', err < tol and mono, f'max err {err:.1e}')


def test_gamuts(cst):
    print('\nGamut matrices vs colour-science: every input x output x white-point adaptation')
    eye = np.eye(3); worst = 0; fails = []
    params, refs = [], []
    for a, ga in enumerate(GAMUT_IDS):
        for b, gb in enumerate(GAMUT_IDS):
            for cat, cn in ((0, 'Bradford'), (1, 'CAT02'), (2, None)):
                params.append([a, 0, b, 0, cat])
                refs.append(colour.matrix_RGB_to_RGB(ref_space(ga), ref_space(gb), chromatic_adaptation_transform=cn))
    out = cst.run(np.repeat(params, 3, 0), np.tile(eye, (len(params), 1))).reshape(-1, 3, 3)
    for p, o, r in zip(params, out, refs):
        e = np.abs(o.T - r).max(); worst = max(worst, e)
        if e > 2e-5: fails.append((GAMUT_IDS[p[0]], GAMUT_IDS[p[2]], p[4], e))
    check(f'{len(params)} gamut / adaptation combinations', not fails, f'max err {worst:.1e}' + (f', fails {fails[:3]}' if fails else ''))
    x = np.random.default_rng(3).uniform(0, 1, (500, 3))
    lin_pass = cst.run([[G['AWG3'], 0, G['AWG3'], 0, 0]], x)
    check('same gamut, Linear -> Linear is bit-exact', np.array_equal(lin_pass.astype(np.float32), x.astype(np.float32)))
    w = cst.run([[a, 0, b, 0, 0] for a in range(len(GAMUT_IDS)) for b in range(len(GAMUT_IDS))],
                np.ones((len(GAMUT_IDS) ** 2, 3)))
    ok_white = np.abs(w - 1).max()
    check('white (1,1,1) maps to white for every pair (Bradford)', ok_white < 1e-5, f'max dev {ok_white:.1e}')


def test_end_to_end(cst, n):
    print('\nEnd-to-end conversions vs colour-science')
    x = np.random.default_rng(0).uniform(0, 1, (n, 3))
    cases = [('KWG', 'KL3', 'AWG3', 'LOGC3'), ('KWG', 'KL3', 'DWG', 'DI'), ('KWG', 'KL3', 'AWG4', 'LOGC4'),
             ('DGAMUT', 'DLOG', 'AWG3', 'LOGC3'), ('DGAMUT', 'DLOG', 'DWG', 'DI'), ('SG3C', 'SLOG3', 'KWG', 'KL3'),
             ('AWG3', 'LOGC3', 'AP0', 'LIN'), ('RWG', 'L3G10', 'AP1', 'ACESCCT'), ('KWG', 'KL3', 'REC709', 'G24')]
    for gi, ci, go, co in cases:
        # reference decode = inverse of reference encode, done numerically through colour where available
        inv = {'KL3': lambda y: np.where(y < 0, y * 0.017178 - 0.008239, (10 ** ((y - 0.092864) / 0.296 / 0.907136) - 1) / 66.64),
               'DLOG': M.log_decoding_DJIDLog, 'SLOG3': M.log_decoding_SLog3, 'LOGC3': M.log_decoding_ARRILogC3,
               'L3G10': M.log_decoding_Log3G10}[ci]
        lin = colour.RGB_to_RGB(inv(x), ref_space(gi), ref_space(go), chromatic_adaptation_transform='Bradford')
        ref = REF_ENC[co](lin) if co not in ('G24',) else np.sign(lin) * np.abs(lin) ** (1 / 2.4)
        if co == 'ACESCCT':
            ref = M.log_encoding_ACEScct(lin)
        got = cst.run([[G[gi], C[ci], G[go], C[co], 0]], x)
        got_lin = cst.run([[G[go], C[co], G[go], C['LIN'], 0]], got)          # decode with the same output curve
        e_lin = pixel_rel(got_lin, lin)
        normal = (np.abs(lin).max(1) < 16) & (lin.min(1) > -0.01)             # up to ~6.5 stops over grey
        e_cv = np.abs(got[normal] - ref[normal]).max()
        check(f'{gi}/{ci} -> {go}/{co}', e_lin < 2e-5 and e_cv < 2e-4,
              f'linear {e_lin:.1e} rel, code {e_cv * 1023:.2f} 10-bit CV')


def test_robustness(cst, remap):
    print('\nRobustness: no NaN / Inf for any curve pair, any input in [-100, 100]')
    vals = np.array([-100, -10, -1, -0.5, -0.01, 0, 1e-6, 0.01, 0.18, 0.5, 1, 1.5, 2, 4, 10, 100.0])
    grid = np.array(np.meshgrid(vals, vals, vals)).reshape(3, -1).T
    bad = 0; total = 0
    params = [[gi, ci, go, co, 0] for ci in range(len(CURVE_IDS)) for co in range(len(CURVE_IDS))
              for gi, go in ((0, 3), (17, 8), (3, 3))]
    for p in params:
        o = cst.run([p], grid); total += o.size; bad += (~np.isfinite(o)).sum()
    check(f'Color Space Transform mk2: {len(params)} settings x {len(grid)} pixels', bad == 0, f'{bad} non-finite of {total}')
    bad = 0; total = 0
    for p in [[s, t, m, e, x] for s in range(5) for t in range(4) for m in (0, 1) for e in (0, 7, 10) for x in (-3, 0, 3)]:
        o = remap.run([p], grid); total += o.size; bad += (~np.isfinite(o)).sum()
    check('Color Remap mk2: every source/target/mode, EIs, exposure +-3', bad == 0, f'{bad} non-finite of {total}')


def test_remap(cst, remap, n):
    print('\nColor Remap mk2 vs Color Space Transform mk2 and ARRI reference')
    x = np.random.default_rng(1).uniform(0, 1, (n, 3))
    eis = sorted(B._LOGC3)
    for s_idx, (sg, sc, inv) in enumerate((('KWG', 'KL3', None), ('DGAMUT', 'DLOG', None), ('KWG8K', 'KL3', None),
                                            ('KWGVST', 'KL3', None), ('KBT2020', 'KL3', None))):
        lin_src = (cst.run([[G[sg], C[sc], G['AWG3'], C['LIN'], 0]], x))
        worst = 0
        for i, ei in enumerate(eis):
            got = remap.run([[s_idx, 0, 0, i, 0]], x)
            ref = M.log_encoding_ARRILogC3(lin_src, EI=ei)
            worst = max(worst, np.abs(got - ref).max())
        check(f'{sg}/{sc} -> LogC3 at all 11 EIs (vs colour-science ARRI LogC3 per EI)', worst < 5e-5, f'max err {worst:.1e}')
        for t, (go, co) in enumerate((('AWG3', 'LOGC3'), ('AWG4', 'LOGC4'), ('DWG', 'DI'), ('KWG', 'KL3'))):
            full = np.abs(remap.run([[s_idx, t, 0, 7, 0]], x) - cst.run([[G[sg], C[sc], G[go], C[co], 0]], x)).max()
            col = np.abs(remap.run([[s_idx, t, 1, 7, 0]], x) - cst.run([[G[sg], C[sc], G[go], C[sc], 0]], x)).max()
            check(f'{sg} -> {go}/{co}: Color+Gamma and Color only == CST', full < 1e-6 and col < 1e-6, f'{full:.1e} / {col:.1e}')
    r = np.repeat(np.linspace(0, 1, 21)[:, None], 3, 1)
    g = max(np.abs(remap.run([[s, t, 1, 7, 0]], r) - r).max() for s in range(5) for t in range(4))
    check('Color only: neutrals pass through untouched', g < 1e-6, f'{g:.1e}')
    kl = kl3_enc(0.18)
    e = remap.run([[0, 0, 0, 7, 1.0]], [[kl] * 3])[0, 0]
    check('Exposure +1 stop: 18% grey -> LogC3(0.36)', abs(e - M.log_encoding_ARRILogC3(0.36)) < 2e-5, f'{e:.5f}')
    ident = np.abs(remap.run([[0, 3, 0, 7, 0]], x) - x).max()
    check('KineLog3 -> KineLog3 is identity', ident < 1e-5, f'{ident:.1e}')


def test_backends(builds, n):
    print('\nCross-backend agreement (same results on every GPU API)')
    rng = np.random.default_rng(5)
    x = rng.uniform(-0.05, 1.05, (n, 3))
    for which in ('cst', 'remap'):
        if which == 'cst':
            P = np.column_stack([rng.integers(0, len(GAMUT_IDS), n), rng.integers(0, len(CURVE_IDS), n),
                                 rng.integers(0, len(GAMUT_IDS), n), rng.integers(0, len(CURVE_IDS), n), rng.integers(0, 3, n)])
        else:
            P = np.column_stack([rng.integers(0, 5, n), rng.integers(0, 4, n), rng.integers(0, 2, n),
                                 rng.integers(0, 11, n), rng.uniform(-3, 3, n)])
        ref = builds['cpp'][which].run(P, x)
        if which == 'cst':   # decode outputs to linear with the same (C++) output curve to compare colour
            dec = lambda o: builds['cpp']['cst'].run(np.column_stack([P[:, 2], P[:, 3], P[:, 2], np.zeros(n), np.zeros(n)]), o)
        for name, b in builds.items():
            if name == 'cpp':
                continue
            o = b[which].run(P, x)
            # code values compared over the legal signal range 0..1; sub-black / super-white values sit on steep
            # linear toes where float32 noise is magnified but invisible (colour accuracy there: linear check below)
            inr = (ref >= 0) & (ref <= 1) & (o >= 0) & (o <= 1)
            e_cv = np.abs(o - ref)[inr].max()
            msg = f'code {e_cv * 1023:.3f} 10-bit CV in 0..1'
            ok = e_cv < (2e-4 if 'fast' in name else 1e-4)   # 0.2 / 0.1 of a 10-bit code value
            if which == 'cst':
                # PQ output is judged on code values only: its x^78.84 makes a linear round trip amplify the
                # (spec-permitted) ULP differences of OpenCL pow() far beyond anything visible in the code value
                np_ = P[:, 3] != C['PQ']
                e_lin = pixel_rel(dec(o)[np_], dec(ref)[np_]); msg += f', linear {e_lin:.1e} rel (non-PQ)'
                # OpenCL 1.2 lets exp/log/pow be 3-16 ULP (C libm: ~1 ULP); 1e-4 = 0.01 %, far below visible
                ok &= e_lin < (1e-4 if 'opencl' in name else 1e-6)
            check(f'{which}: {name} == cpp ({n} random settings x pixels)', ok, msg)


def test_extras(builds_avail, n):
    print('\nExtras: KineLog3 -> LogC3 DCTL, chart-match pipeline and .cube')
    import json, subprocess, tempfile
    ex = os.path.join(ROOT, 'extras', 'kinelog3-to-logc3')
    sys.path.insert(0, ex)
    import kl3_logc3 as K
    d = os.path.join(ex, 'KineLog3_to_LogC3.dctl')
    x = np.random.default_rng(2).uniform(0, 1, (n, 3))
    eis = sorted(K.LOGC3)
    bs = {'cpp': H.NativeDCTL(d, 'cpp'), 'c99': H.NativeDCTL(d, 'c99')}
    if 'opencl' in builds_avail:
        bs['opencl'] = H.OpenCLDCTL(d)
    for name, b in bs.items():
        worst = max(np.abs(b.run([[i, 0, 1.0, 0.0]], x) - K.transform(x, ei)).max() for i, ei in enumerate(eis))
        check(f'KineLog3_to_LogC3.dctl [{name}] == Python reference, all EIs', worst < 1e-4, f'max err {worst:.1e}')
    tmp = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, os.path.join(ex, 'kl3_logc3.py'), 'match', '--csv',
                        os.path.join(ex, 'test', 'kine.csv'), os.path.join(ex, 'test', 'alexa.csv'), '--out', tmp],
                       capture_output=True, text=True)
    mean_after = float([l for l in r.stdout.splitlines() if l.strip().startswith('MEAN')][0].split()[-1])
    check('chart match solves the sample chart (mean dE2000 after < 0.5)', r.returncode == 0 and mean_after < 0.5, f'{mean_after:.2f}')
    cm = H.NativeDCTL(os.path.join(tmp, 'KineLog3_to_LogC3_chartmatch.dctl'), 'cpp')
    Mm = np.array(json.load(open(os.path.join(tmp, 'chart_match.json')))['model'])
    e = np.abs(cm.run([[7, 1, 1.0, 0.0]], x) - K.transform(x, 800, Mm)).max()
    check('generated chart-match DCTL == Python model', e < 1e-4, f'max err {e:.1e}')
    lut = np.loadtxt(os.path.join(ex, 'KineLog3_KWG_to_LogC3_AWG3_EI800.cube'), skiprows=5)
    g = np.linspace(0, 1, 65); bb, gg, rr = np.meshgrid(g, g, g, indexing='ij')
    exact = np.clip(K.transform(np.stack([rr, gg, bb], -1).reshape(-1, 3), 800), 0, 1)
    e = np.abs(lut - exact).max()
    check('.cube nodes == exact transform (65^3, R fastest)', e < 1e-6, f'max err {e:.1e}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true')
    ap.add_argument('--no-opencl', action='store_true')
    a = ap.parse_args()
    n = 400 if a.quick else 3000
    t0 = time.time()
    print('Building DCTLs ...')
    builds = {'cpp': {'cst': H.NativeDCTL(CST, 'cpp'), 'remap': H.NativeDCTL(REMAP, 'cpp')},
              'c99': {'cst': H.NativeDCTL(CST, 'c99'), 'remap': H.NativeDCTL(REMAP, 'c99')}}
    print('  C++14 and C99 builds OK (-Wall -Wextra -Werror)')
    if not a.no_opencl and H.opencl_available():
        builds['opencl'] = {'cst': H.OpenCLDCTL(CST), 'remap': H.OpenCLDCTL(REMAP)}
        builds['opencl-fastmath'] = {'cst': H.OpenCLDCTL(CST, True), 'remap': H.OpenCLDCTL(REMAP, True)}
        print('  OpenCL builds OK (CL1.2, -Werror, with and without -cl-fast-relaxed-math)')
    else:
        print('  OpenCL not available - skipping OpenCL backend (pip install pyopencl pocl-binary-distribution)')
    cst, remap = builds['cpp']['cst'], builds['cpp']['remap']
    test_spec_anchors(cst)
    test_curves(cst, 300)
    test_round_trip(cst)
    test_gamuts(cst)
    test_end_to_end(cst, n)
    test_remap(cst, remap, n)
    test_robustness(cst, remap)
    test_backends(builds, n)
    test_extras(builds, n)
    fails = [r for r in RESULTS if not r[1]]
    print(f'\n{len(RESULTS) - len(fails)}/{len(RESULTS)} checks passed in {time.time() - t0:.0f}s')
    for f in fails:
        print('  FAILED:', f[0], f[2])
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        tb = traceback.format_exc()
        print(tb, flush=True)
        gha('error', 'Test suite crashed', tb[-3000:])
        sys.exit(2)
