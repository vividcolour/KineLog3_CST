#!/usr/bin/env python3
"""
KineLog3 / Kinefinity Wide Gamut  ->  ARRI LogC3 / ARRI Wide Gamut 3
(Kinefinity MAVO Edge 6K -> ARRI ALEXA Mini LF)

  build   write the spec-accurate DCTL + .cube (optionally with a chart-match model)
  match   solve a chart-match model from a ColorChecker shot on both cameras
  check   print reference values / round-trip errors

Sources
  KineLog3 curve + Kinefinity Wide Gamut primaries:
      Kinefinity, "KineLog3 Technical Specifications" v2 (24 Sep 2025), PDF:
      https://github.com/thatcherfreeman/dwg-transforms/blob/main/specs/KineLog3%20Technical%20Specifications%20v2.pdf
      Verified: derived KWG->XYZ, XYZ->KWG and KWG->BT.2020 match the published matrices to
      all 4 printed decimals; 18%/90% grey encode to 39.19 / 57.22 IRE (spec 39.2 / 57.2).
  ARRI LogC3 (SUP 3.x, scene-linear exposure factor) + ARRI Wide Gamut 3:
      ARRI, "ALEXA Log C Curve - Usage in VFX" white paper
"""
import argparse, csv, json, os, sys
import numpy as np

# ---------------------------------------------------------------- KineLog3
KL3 = dict(a=66.64, b=0.296, c=0.907136, d=0.092864, cut=-0.008239, s=0.017178)

def kl3_decode(v):
    v = np.asarray(v, float); p = KL3
    return np.where(v < 0.0, v * p['s'] + p['cut'],
                    (10.0 ** (((v - p['d']) / p['b']) / p['c']) - 1.0) / p['a'])

def kl3_encode(x):
    x = np.asarray(x, float); p = KL3
    return np.where(x < p['cut'], (x - p['cut']) / p['s'],
                    np.log10(np.maximum(p['a'] * x + 1.0, 1e-12)) * p['b'] * p['c'] + p['d'])

# ---------------------------------------------------------------- ARRI LogC3
# SUP 3.x, "Linear Scene Exposure Factor": EI -> (cut, a, b, c, d, e, f)
LOGC3 = {
    160:  (0.005561, 5.555556, 0.080216, 0.269036, 0.381991, 5.842037, 0.092778),
    200:  (0.006208, 5.555556, 0.076621, 0.266007, 0.382478, 5.776265, 0.092782),
    250:  (0.006871, 5.555556, 0.072941, 0.262978, 0.382966, 5.710494, 0.092786),
    320:  (0.007622, 5.555556, 0.068768, 0.259627, 0.383508, 5.637732, 0.092791),
    400:  (0.008318, 5.555556, 0.064901, 0.256598, 0.383999, 5.571960, 0.092795),
    500:  (0.009031, 5.555556, 0.060939, 0.253569, 0.384493, 5.506188, 0.092800),
    640:  (0.009840, 5.555556, 0.056443, 0.250219, 0.385040, 5.433426, 0.092805),
    800:  (0.010591, 5.555556, 0.052272, 0.247190, 0.385537, 5.367655, 0.092809),
    1000: (0.011361, 5.555556, 0.047996, 0.244161, 0.386036, 5.301883, 0.092814),
    1280: (0.012235, 5.555556, 0.043137, 0.240810, 0.386590, 5.229121, 0.092819),
    1600: (0.013047, 5.555556, 0.038625, 0.237781, 0.387093, 5.163350, 0.092824),
}

def logc3_encode(x, ei=800):
    cut, a, b, c, d, e, f = LOGC3[ei]; x = np.asarray(x, float)
    return np.where(x > cut, c * np.log10(np.maximum(a * x + b, 1e-12)) + d, e * x + f)

def logc3_decode(t, ei=800):
    cut, a, b, c, d, e, f = LOGC3[ei]; t = np.asarray(t, float)
    return np.where(t > e * cut + f, (10.0 ** ((t - d) / c) - b) / a, (t - f) / e)

# ---------------------------------------------------------------- Gamuts
D65 = (0.3127, 0.3290)
KWG  = ((0.7571, 0.2282), (0.2139, 1.1480), (0.0536, -0.2236))   # Kinefinity Wide Gamut
AWG3 = ((0.6840, 0.3130), (0.2210, 0.8480), (0.0861, -0.1020))   # ARRI Wide Gamut 3

def npm(prim, white=D65):
    """RGB -> XYZ normalised primary matrix (SMPTE RP 177)."""
    xyz = lambda x, y: np.array([x / y, 1.0, (1 - x - y) / y])
    P = np.stack([xyz(*p) for p in prim], axis=1)
    S = np.linalg.solve(P, xyz(*white))
    return P * S

KWG_TO_XYZ  = npm(KWG)
AWG3_TO_XYZ = npm(AWG3)
KWG_TO_AWG3 = np.linalg.inv(AWG3_TO_XYZ) @ KWG_TO_XYZ   # same white -> no CAT

# ---------------------------------------------------------------- chart-match models
def rp_expand(rgb, model):
    """Feature expansion. 'matrix' = 3 terms, 'rpcc2' = root-polynomial degree 2 (6 terms,
    exposure invariant: scaling input by k scales output by k)."""
    rgb = np.atleast_2d(rgb)
    if model == 'matrix':
        return rgb
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    sq = lambda u: np.sqrt(np.maximum(u, 0.0))
    return np.stack([r, g, b, sq(r * g), sq(g * b), sq(r * b)], axis=1)

def identity_model():
    M = np.zeros((3, 6)); M[:, :3] = np.eye(3)
    return M

def apply_model(rgb_lin_awg3, M):
    feats = rp_expand(rgb_lin_awg3, 'rpcc2')
    return feats @ M.T

# ---------------------------------------------------------------- full transform
def transform(kl3_rgb, ei=800, M=None, exposure_stops=0.0):
    shape = np.shape(kl3_rgb)
    lin = kl3_decode(np.reshape(kl3_rgb, (-1, 3)))
    awg = lin @ KWG_TO_AWG3.T
    if M is not None:
        awg = apply_model(awg, M)
    awg = awg * 2.0 ** exposure_stops
    return logc3_encode(awg, ei).reshape(shape)

# ---------------------------------------------------------------- writers
def write_cube(path, ei, M, exposure_stops, size=65, title=None):
    g = np.linspace(0.0, 1.0, size)
    # .cube order: R changes fastest
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')
    rgb = np.stack([r, gg, b], axis=-1).reshape(-1, 3)
    # clamp to legal LogC3 range: impossible corner inputs (e.g. KineLog3 1,0,0) otherwise
    # reach -40 and ruin trilinear/tetrahedral interpolation in the neighbouring cells
    out = np.clip(transform(rgb, ei, M, exposure_stops), 0.0, 1.0)
    with open(path, 'w') as fh:
        fh.write(f'TITLE "{title or os.path.basename(path)}"\n')
        fh.write(f'# KineLog3/Kinefinity Wide Gamut -> ARRI LogC3 EI{ei}/AWG3\n')
        fh.write('LUT_3D_SIZE %d\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n' % size)
        for v in out:
            fh.write('%.7f %.7f %.7f\n' % tuple(v))

def _fmt_mat(M, indent='        '):
    rows = []
    for row in M:
        rows.append(indent + '{' + ', '.join('%.10ff' % x for x in row) + '}')
    return ',\n'.join(rows)

def write_dctl(path, M=None, default_ei=800, note=''):
    eis = sorted(LOGC3)
    ei_ids = ', '.join(f'EI{e}' for e in eis)
    ei_names = ', '.join(f'EI {e}' for e in eis)
    ei_branches = '\n'.join(
        f'    {"if" if i == 0 else "else if"} (ei_idx == EI{e}) {{ cut={p[0]}f; a={p[1]}f; b={p[2]}f; c={p[3]}f; d={p[4]}f; e={p[5]}f; f={p[6]}f; }}'
        for i, (e, p) in enumerate((e, LOGC3[e]) for e in eis))
    has_cm = M is not None
    Mcm = M if has_cm else identity_model()
    src = f'''// KineLog3 / Kinefinity Wide Gamut  ->  ARRI LogC3 / ARRI Wide Gamut 3
// Kinefinity MAVO Edge 6K -> ARRI ALEXA Mini LF
//
// Part of Color Space Transform mk2 (extras). Built from Kinefinity's "KineLog3 Technical Specifications" v2 PDF
// and ARRI's LogC3 (SUP 3.x) / AWG3 specification. Generated by kl3_logc3.py.
// Input : KineLog3 / KWG (camera-original, no other transforms before this node)
// Output: ARRI LogC3 / AWG3 at the chosen EI -> feed straight into any ALEXA LogC3 LUT/CST.
// {note}
// clang-format off
DEFINE_UI_PARAMS(ei, LogC3 EI, DCTLUI_COMBO_BOX, {eis.index(default_ei)}, {{{ei_ids}}}, {{{ei_names}}})
DEFINE_UI_PARAMS(use_cm, Chart Match, DCTLUI_CHECK_BOX, {1 if has_cm else 0})
DEFINE_UI_PARAMS(cm_mix, Chart Match Amount, DCTLUI_SLIDER_FLOAT, 1.0, 0.0, 1.0, 0.01)
DEFINE_UI_PARAMS(exposure, Exposure Trim (stops), DCTLUI_SLIDER_FLOAT, 0.0, -3.0, 3.0, 0.01)
// clang-format on

__DEVICE__ float kl3_to_lin(float v) {{
    const float a = 66.64f, b = 0.296f, c = 0.907136f, d = 0.092864f;
    const float cut = -0.008239f, s = 0.017178f;
    return v < 0.0f ? v * s + cut : (_exp10f(((v - d) / b) / c) - 1.0f) / a;
}}

__DEVICE__ float lin_to_logc3(float x, int ei_idx) {{
    float cut, a, b, c, d, e, f;
{ei_branches}
    else {{ cut=0.010591f; a=5.555556f; b=0.052272f; c=0.247190f; d=0.385537f; e=5.367655f; f=0.092809f; }}
    return x > cut ? c * _log10f(a * x + b) + d : e * x + f;
}}

__DEVICE__ float sqrt0(float x) {{ return _sqrtf(_fmaxf(x, 0.0f)); }}

__DEVICE__ float3 transform(int p_Width, int p_Height, int p_X, int p_Y, float p_R, float p_G, float p_B) {{
    // KWG -> AWG3 (both D65, derived from published primaries)
    const float m[3][3] = {{
{_fmt_mat(KWG_TO_AWG3)}
    }};
    // Chart-match model, root-polynomial (r, g, b, sqrt(rg), sqrt(gb), sqrt(rb)) in linear AWG3.
    // Identity unless generated by `kl3_logc3.py match`.
    const float cm[3][6] = {{
{_fmt_mat(Mcm)}
    }};

    float r = kl3_to_lin(p_R), g = kl3_to_lin(p_G), b = kl3_to_lin(p_B);

    float R = m[0][0] * r + m[0][1] * g + m[0][2] * b;
    float G = m[1][0] * r + m[1][1] * g + m[1][2] * b;
    float B = m[2][0] * r + m[2][1] * g + m[2][2] * b;

    if (use_cm) {{
        float f[6] = {{R, G, B, sqrt0(R * G), sqrt0(G * B), sqrt0(R * B)}};
        float o[3];
        for (int i = 0; i < 3; i++) {{
            o[i] = 0.0f;
            for (int j = 0; j < 6; j++) o[i] += cm[i][j] * f[j];
        }}
        R = R + cm_mix * (o[0] - R);
        G = G + cm_mix * (o[1] - G);
        B = B + cm_mix * (o[2] - B);
    }}

    float k = _exp2f(exposure);
    int ei_sel = (int)ei;
    return make_float3(lin_to_logc3(R * k, ei_sel), lin_to_logc3(G * k, ei_sel), lin_to_logc3(B * k, ei_sel));
}}
'''
    with open(path, 'w') as fh:
        fh.write(src)

# ---------------------------------------------------------------- chart sampling
def read_csv_patches(path):
    rows = []
    with open(path) as fh:
        for row in csv.reader(fh):
            try:
                vals = [float(x) for x in row if x.strip() != ''][-3:]
            except ValueError:
                continue  # header
            if len(vals) == 3:
                rows.append(vals)
    a = np.array(rows, float)
    if a.shape != (24, 3):
        sys.exit(f'{path}: expected 24 RGB rows, got {a.shape}')
    if a.max() > 1.5:  # 8/10/12/16-bit code values
        a = a / (1023.0 if a.max() <= 1023 else 4095.0 if a.max() <= 4095 else 65535.0)
    return a

def read_image(path):
    os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR', '1')
    import cv2
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
    if im is None:
        sys.exit(f'cannot read {path}')
    im = im[..., :3][..., ::-1].astype(np.float64)
    if im.dtype != np.float32 and im.max() > 1.5:
        im /= 65535.0 if im.max() > 255 else 255.0
    return im

def sample_chart(img, corners, debug_path=None, inset=0.3):
    """corners: TL (dark skin), TR (bluish green), BR (black), BL (white) in pixels."""
    import cv2
    src = np.array(corners, np.float32)
    W, H = 600, 400
    dst = np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float32)
    Hm = cv2.getPerspectiveTransform(src, dst)
    warp = cv2.warpPerspective(img.astype(np.float32), Hm, (W, H), flags=cv2.INTER_AREA)
    out, boxes = [], []
    cw, ch = W / 6, H / 4
    for row in range(4):
        for col in range(6):
            x0, y0 = col * cw + cw * inset, row * ch + ch * inset
            x1, y1 = (col + 1) * cw - cw * inset, (row + 1) * ch - ch * inset
            patch = warp[int(y0):int(y1), int(x0):int(x1)].reshape(-1, 3)
            out.append(np.median(patch, axis=0)); boxes.append((x0, y0, x1, y1))
    if debug_path:
        vis = np.clip(warp / max(warp.max(), 1e-6), 0, 1)
        vis = (vis[..., ::-1] * 255).astype(np.uint8).copy()
        for (x0, y0, x1, y1) in boxes:
            cv2.rectangle(vis, (int(x0), int(y0)), (int(x1), int(y1)), (0, 0, 255), 2)
        cv2.imwrite(debug_path, vis)
    return np.array(out)

# ---------------------------------------------------------------- colour metrics
def awg3_to_lab(lin_awg3, grey_Y):
    """CIELAB (D65), scene scaled so the chart grey patch (neutral 5) sits at its nominal Y."""
    XYZ = lin_awg3 @ AWG3_TO_XYZ.T
    XYZ = XYZ * (0.1906 / grey_Y)   # put patch 22 (neutral 5) at its nominal ~19% Y
    w = AWG3_TO_XYZ.sum(axis=1)
    f = lambda t: np.where(t > (6 / 29) ** 3, np.cbrt(t), t / (3 * (6 / 29) ** 2) + 4 / 29)
    fx, fy, fz = (f(XYZ[:, i] / w[i]) for i in range(3))
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=1)

def de2000(lab1, lab2):
    L1, a1, b1 = lab1.T; L2, a2, b2 = lab2.T
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dhp = h2p - h1p
    dhp = np.where(C1p * C2p == 0, 0, np.where(dhp > 180, dhp - 360, np.where(dhp < -180, dhp + 360, dhp)))
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    hbp = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) > 180,
                   np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2), hs / 2))
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dth = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))

# ---------------------------------------------------------------- solver
NEUTRALS = list(range(18, 24))   # white .. black
GREY = 21                        # neutral 5 (.70 D)

def solve(src, ref, model='rpcc2', preserve_neutral=True, exposure_match=True):
    """src, ref: (24,3) linear AWG3. Returns (3,6) model matrix and exposure gain applied."""
    gain = 1.0
    if exposure_match:
        gain = ref[GREY, 1] / max(src[GREY, 1], 1e-9)   # match exposure on grey, green channel
    s = src * gain
    nfeat = 3 if model == 'matrix' else 6
    F = rp_expand(s, model)
    # weight by 1/luminance -> minimise relative (stop-ish) error, not dominated by white
    Y = np.maximum((ref @ AWG3_TO_XYZ.T)[:, 1], 1e-4)
    w = 1.0 / Y
    M = np.zeros((3, nfeat))
    for ch in range(3):
        A = F * w[:, None]; y = ref[:, ch] * w
        if preserve_neutral:
            # equality constraint: model(grey_src) == grey_ref  (keeps neutrals neutral at grey)
            C = F[GREY:GREY + 1]; dv = ref[GREY:GREY + 1, ch]
            K = np.block([[A.T @ A, C.T], [C, np.zeros((1, 1))]])
            rhs = np.concatenate([A.T @ y, dv])
            M[ch] = np.linalg.solve(K, rhs)[:nfeat]
        else:
            M[ch] = np.linalg.lstsq(A, y, rcond=None)[0]
    # optional refinement directly on mean dE2000
    try:
        from scipy.optimize import minimize
        grey_Y = (ref[GREY] @ AWG3_TO_XYZ.T)[1]
        lab_ref = awg3_to_lab(ref, grey_Y)
        def cost(p):
            Mp = p.reshape(3, nfeat)
            pred = F @ Mp.T
            c = np.mean(de2000(awg3_to_lab(pred, grey_Y), lab_ref) ** 2)
            if preserve_neutral:
                c += 1e4 * np.sum((F[GREY] @ Mp.T - ref[GREY]) ** 2) / grey_Y ** 2
            return c
        res = minimize(cost, M.ravel(), method='Nelder-Mead' if nfeat == 3 else 'Powell',
                       options=dict(maxiter=20000, xtol=1e-7, ftol=1e-10))
        if res.fun <= cost(M.ravel()):
            M = res.x.reshape(3, nfeat)
    except ImportError:
        pass
    if model == 'matrix':
        M = np.hstack([M, np.zeros((3, 3))])
    return M, gain

def report(src_lin, ref_lin, M, gain, title):
    grey_Y = (ref_lin[GREY] @ AWG3_TO_XYZ.T)[1]
    lab_ref = awg3_to_lab(ref_lin, grey_Y)
    before = de2000(awg3_to_lab(src_lin * gain, grey_Y), lab_ref)
    after = de2000(awg3_to_lab(apply_model(src_lin * gain, M), grey_Y), lab_ref)
    names = ['dark skin', 'light skin', 'blue sky', 'foliage', 'blue flower', 'bluish green',
             'orange', 'purplish blue', 'moderate red', 'purple', 'yellow green', 'orange yellow',
             'blue', 'green', 'red', 'yellow', 'magenta', 'cyan',
             'white', 'neutral 8', 'neutral 6.5', 'neutral 5', 'neutral 3.5', 'black']
    print(f'\n{title}\n  {"patch":<15}{"dE00 spec-only":>16}{"dE00 matched":>14}')
    for n, b_, a_ in zip(names, before, after):
        print(f'  {n:<15}{b_:16.2f}{a_:14.2f}')
    print(f'  {"MEAN":<15}{before.mean():16.2f}{after.mean():14.2f}')
    print(f'  {"MAX":<15}{before.max():16.2f}{after.max():14.2f}')
    return before, after

# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    b = sub.add_parser('build', help='write DCTL + .cube')
    b.add_argument('--ei', type=int, default=800, choices=sorted(LOGC3))
    b.add_argument('--size', type=int, default=65)
    b.add_argument('--model', help='chart-match JSON from `match` (optional)')
    b.add_argument('--out', default='.')

    m = sub.add_parser('match', help='solve chart match (Kine -> ALEXA)')
    g = m.add_mutually_exclusive_group(required=True)
    g.add_argument('--csv', nargs=2, metavar=('KINE.csv', 'ALEXA.csv'),
                   help='24 rows of R,G,B log code values, patch order dark skin..black')
    g.add_argument('--images', nargs=2, metavar=('KINE.tif', 'ALEXA.tif'),
                   help='camera-original log frames (16-bit TIFF / EXR / DPX via OpenCV)')
    m.add_argument('--kine-corners', nargs=4, metavar='X,Y')
    m.add_argument('--alexa-corners', nargs=4, metavar='X,Y',
                   help='corners TL(dark skin) TR(bluish green) BR(black) BL(white)')
    m.add_argument('--ei', type=int, default=800, choices=sorted(LOGC3), help='EI the ALEXA chart was shot at')
    m.add_argument('--out-ei', type=int, help='EI for generated LUT (default = --ei)')
    m.add_argument('--model', choices=['matrix', 'rpcc2'], default='rpcc2')
    m.add_argument('--no-exposure-match', action='store_true',
                   help='keep the exposure difference instead of matching on the grey patch')
    m.add_argument('--out', default='.')

    sub.add_parser('check', help='print reference values')
    a = ap.parse_args()

    if a.cmd == 'check':
        np.set_printoptions(precision=10, suppress=True)
        print('KWG -> XYZ\n', KWG_TO_XYZ, '\nAWG3 -> XYZ\n', AWG3_TO_XYZ, '\nKWG -> AWG3\n', KWG_TO_AWG3)
        print('row sums (must be 1):', KWG_TO_AWG3.sum(1))
        for refl in (0.0, 0.18, 0.90):
            print(f'{refl:4.2f} reflectance: KineLog3 {float(kl3_encode(refl)):.4f}  ->  LogC3 EI800 '
                  f'{float(logc3_encode(refl)):.4f}  (via transform {transform(np.array([float(kl3_encode(refl))]*3))[0]:.4f})')
        v = np.linspace(-0.05, 1.0, 10001)
        print('KineLog3 round-trip max err:', np.abs(kl3_encode(kl3_decode(v)) - v).max())
        print('LogC3 round-trip max err:', max(np.abs(logc3_encode(logc3_decode(v, e), e) - v).max() for e in LOGC3))
        return

    os.makedirs(a.out, exist_ok=True)
    if a.cmd == 'build':
        M, note, exp = None, '', 0.0
        if a.model:
            j = json.load(open(a.model)); M = np.array(j['model']); exp = 0.0
            note = 'Chart-match model: ' + j.get('note', '')
        tag = '_chartmatch' if M is not None else ''
        write_dctl(os.path.join(a.out, f'KineLog3_to_LogC3{tag}.dctl'), M, a.ei, note)
        write_cube(os.path.join(a.out, f'KineLog3_KWG_to_LogC3_AWG3_EI{a.ei}{tag}.cube'), a.ei, M, exp, a.size)
        print('wrote', a.out)
        return

    if a.cmd == 'match':
        if a.csv:
            k_log, r_log = read_csv_patches(a.csv[0]), read_csv_patches(a.csv[1])
        else:
            if not (a.kine_corners and a.alexa_corners):
                sys.exit('--images needs --kine-corners and --alexa-corners')
            pc = lambda cs: [tuple(float(t) for t in c.split(',')) for c in cs]
            k_log = sample_chart(read_image(a.images[0]), pc(a.kine_corners), os.path.join(a.out, 'debug_kine.png'))
            r_log = sample_chart(read_image(a.images[1]), pc(a.alexa_corners), os.path.join(a.out, 'debug_alexa.png'))
            print('check debug_kine.png / debug_alexa.png: every red box must sit inside its patch')
        src = kl3_decode(k_log) @ KWG_TO_AWG3.T     # Kine -> linear AWG3 (spec)
        ref = logc3_decode(r_log, a.ei)             # ALEXA linear AWG3
        M, gain = solve(src, ref, a.model, True, not a.no_exposure_match)
        report(src, ref, M, gain, f'Chart match ({a.model}), exposure gain {np.log2(gain):+.2f} stops on Kine')
        # Fold the exposure gain into the model only if requested (rpcc2/matrix are both 1-homogeneous)
        if a.no_exposure_match:
            Mout = M
        else:
            Mout = M * gain
        note = f'{a.model}, solved from chart; exposure offset {np.log2(gain):+.2f} st folded in'
        json.dump(dict(model=Mout.tolist(), model_type=a.model, kine_exposure_gain=gain,
                       alexa_ei=a.ei, note=note), open(os.path.join(a.out, 'chart_match.json'), 'w'), indent=2)
        ei = a.out_ei or a.ei
        write_dctl(os.path.join(a.out, 'KineLog3_to_LogC3_chartmatch.dctl'), Mout, ei, note)
        write_cube(os.path.join(a.out, f'KineLog3_KWG_to_LogC3_AWG3_EI{ei}_chartmatch.cube'), ei, Mout, 0.0)
        print('\nwrote chart_match.json, DCTL and .cube to', a.out)

if __name__ == '__main__':
    main()
