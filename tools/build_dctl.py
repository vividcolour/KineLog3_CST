#!/usr/bin/env python3
"""Builds dctl/Color Space Transform mk2.dctl and dctl/Color Remap mk2.dctl.

Run:  python3 tools/build_dctl.py
"""
import os

VERSION = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'VERSION')).read().strip()

# (enum id, UI label, primaries rx ry gx gy bx by, white wx wy)
GAMUTS = [
    # Kinefinity Wide Gamut, Kinefinity "KineLog3 Technical Specifications" v2 - published for MAVO Edge 6K / MM2 LF
    ('KWG',    'Kinefinity WG - Edge 6K - MM2 LF', (0.7571, 0.2282, 0.2139, 1.1480, 0.0536, -0.2236), (0.3127, 0.3290)),
    ('AWG3',   'ARRI Wide Gamut 3',       (0.684, 0.313, 0.221, 0.848, 0.0861, -0.102), (0.3127, 0.3290)),
    ('AWG4',   'ARRI Wide Gamut 4',       (0.7347, 0.2653, 0.1424, 0.8576, 0.0991, -0.0308), (0.3127, 0.3290)),
    ('DWG',    'DaVinci Wide Gamut',      (0.8, 0.313, 0.1682, 0.9877, 0.079, -0.1155), (0.3127, 0.3290)),
    ('REC709', 'Rec.709 - sRGB',          (0.64, 0.33, 0.30, 0.60, 0.15, 0.06), (0.3127, 0.3290)),
    ('REC2020','Rec.2020',                (0.708, 0.292, 0.170, 0.797, 0.131, 0.046), (0.3127, 0.3290)),
    ('P3D65',  'P3-D65',                  (0.680, 0.320, 0.265, 0.690, 0.150, 0.060), (0.3127, 0.3290)),
    ('P3DCI',  'DCI-P3',                  (0.680, 0.320, 0.265, 0.690, 0.150, 0.060), (0.314, 0.351)),
    ('AP0',    'ACES AP0',                (0.7347, 0.2653, 0.0, 1.0, 0.0001, -0.077), (0.32168, 0.33767)),
    ('AP1',    'ACES AP1',                (0.713, 0.293, 0.165, 0.830, 0.128, 0.044), (0.32168, 0.33767)),
    ('SG3',    'Sony S-Gamut3',           (0.73, 0.28, 0.14, 0.855, 0.10, -0.05), (0.3127, 0.3290)),
    ('SG3C',   'Sony S-Gamut3.Cine',      (0.766, 0.275, 0.225, 0.800, 0.089, -0.087), (0.3127, 0.3290)),
    ('RWG',    'RED Wide Gamut RGB',      (0.780308, 0.304253, 0.121595, 1.493994, 0.095612, -0.084589), (0.3127, 0.3290)),
    ('VGAMUT', 'Panasonic V-Gamut',       (0.73, 0.28, 0.165, 0.84, 0.10, -0.03), (0.3127, 0.3290)),
    ('CINEMA', 'Canon Cinema Gamut',      (0.74, 0.27, 0.17, 1.14, 0.08, -0.10), (0.3127, 0.3290)),
    ('BMDWG',  'Blackmagic Wide Gamut',   (0.7177215, 0.3171181, 0.228041, 0.861569, 0.1005841, -0.0820452), (0.312717, 0.3290312)),
    ('FGAMUT', 'Fujifilm F-Gamut',        (0.708, 0.292, 0.170, 0.797, 0.131, 0.046), (0.3127, 0.3290)),
    # DJI D-Gamut: DJI X7 (2017) and Zenmuse X9 / Ronin 4D (2022) white papers - unchanged on X9
    ('DGAMUT', 'DJI D-Gamut',             (0.71, 0.31, 0.21, 0.88, 0.09, -0.08), (0.3127, 0.3290)),
    # --- added v1.1.0 (appended so saved node settings keep their indices) ---
    # PROVISIONAL: Kinefinity has not published native-gamut primaries for these cameras. Until it does they use the
    # published Kinefinity Wide Gamut (Kinefinity states Vista's KineLog3 inherits the MAVO Edge color science).
    # When primaries are published, change only these two rows. See docs/SPECIFICATION.md section 3.2.
    ('KWG8K',  'Kinefinity WG - Edge 8K - provisional', (0.7571, 0.2282, 0.2139, 1.1480, 0.0536, -0.2236), (0.3127, 0.3290)),
    ('KWGVST', 'Kinefinity WG - Vista - provisional',   (0.7571, 0.2282, 0.2139, 1.1480, 0.0536, -0.2236), (0.3127, 0.3290)),
    # KineOS 8 "BT.2020" ProRes gamut (MAVO Edge 6K / 8K, MAVO mark2): standard ITU-R BT.2020 primaries - exact
    ('KBT2020','Kinefinity BT.2020 - KineOS 8',       (0.708, 0.292, 0.170, 0.797, 0.131, 0.046), (0.3127, 0.3290)),
]

CURVES = [
    ('LIN',     'Linear'),
    ('KL3',     'KineLog3'),
    ('LOGC3',   'ARRI LogC3 EI800'),
    ('LOGC4',   'ARRI LogC4'),
    ('DI',      'DaVinci Intermediate'),
    ('SLOG3',   'Sony S-Log3'),
    ('L3G10',   'RED Log3G10'),
    ('VLOG',    'Panasonic V-Log'),
    ('CLOG3',   'Canon Log 3'),
    ('BMDG5',   'Blackmagic Film Gen 5'),
    ('FLOG2',   'Fujifilm F-Log2'),
    ('ACESCCT', 'ACEScct'),
    ('ACESCC',  'ACEScc'),
    ('R709',    'Rec.709 Scene'),
    ('SRGB',    'sRGB'),
    ('G22',     'Gamma 2.2'),
    ('G24',     'Gamma 2.4'),
    ('G26',     'Gamma 2.6'),
    ('PQ',      'ST2084 PQ 100 nits'),
    ('DLOG',    'DJI D-Log'),
]

def combo(var, label, prefix, items, default):
    ids = ', '.join(prefix + i[0] for i in items)
    names = ', '.join(i[1] for i in items)
    return f'DEFINE_UI_PARAMS({var}, {label}, DCTLUI_COMBO_BOX, {default}, {{{ids}}}, {{{names}}})'

def gamut_fn():
    lines = []
    for i, (gid, name, p, w) in enumerate(GAMUTS):
        kw = 'if' if i == 0 else 'else if'
        vals = ', '.join(f'{v}f' for v in p + w)
        lines.append(f'    {kw} (g == {i}) return cst_prims({vals}); // {name}')
    lines.append('    return cst_prims(0.64f, 0.33f, 0.30f, 0.60f, 0.15f, 0.06f, 0.3127f, 0.3290f);')
    return '\n'.join(lines)

def curve_ids():
    return '\n'.join(f'#define C_{cid} {i}' for i, (cid, _) in enumerate(CURVES))

DCTL = r'''// Color Space Transform mk2 v__VERSION__ - a Resolve-style Color Space Transform with extra camera color spaces.
// MIT licence - see the project README for documentation and sources.
//
// Works like Resolve's Color Space Transform node (input gamut + gamma -> output gamut + gamma),
// with Kinefinity KineLog3 / Kinefinity Wide Gamut (MAVO Edge 6K, MM2 LF; Edge 8K + Vista provisional; KineOS 8
// BT.2020 mode) and DJI D-Log / D-Gamut (Ronin 4D 6K/8K, Zenmuse X9, X7) added. Pure color-science conversion:
// no tone mapping, gamut mapping or clipping - do that in a stock CST after this node, e.g.
//     [Color Space Transform mk2: KWG/KineLog3 -> DWG/DaVinci Intermediate] -> [CST: DWG/DI -> Rec.709/Gamma 2.4, tone mapping on]
//
// KineLog3 + Kinefinity Wide Gamut: Kinefinity "KineLog3 Technical Specifications" v2 (24 Sep 2025).
// DJI D-Log + D-Gamut: DJI "White Paper on D-Log and D-Gamut of DJI Cinema Color System" (Zenmuse X9, 2022).
// Full specification, sources and verification status: docs/SPECIFICATION.md
// Other curves/primaries: manufacturer specifications (checked against colour-science 0.4.7).
// Generated by tools/build_dctl.py - edit that, not this file.

// clang-format off
__INPUT_GAMUT__
__INPUT_CURVE__
__OUTPUT_GAMUT__
__OUTPUT_CURVE__
DEFINE_UI_PARAMS(cat_method, White Point Adaptation, DCTLUI_COMBO_BOX, 0, {CAT_BRADFORD, CAT_CAT02, CAT_NONE}, {Bradford, CAT02, None})
// clang-format on

__CURVE_IDS__

typedef struct { float3 x, y, z; } cst_mat3_t;
typedef struct { float rx, ry, gx, gy, bx, by, wx, wy; } cst_prim_t;

__DEVICE__ cst_mat3_t cst_make_mat3(float3 a, float3 b, float3 c) { cst_mat3_t m; m.x = a; m.y = b; m.z = c; return m; }
__DEVICE__ float cst_dot3(float3 a, float3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
__DEVICE__ float3 cst_mul(cst_mat3_t m, float3 v) { return make_float3(cst_dot3(m.x, v), cst_dot3(m.y, v), cst_dot3(m.z, v)); }
__DEVICE__ cst_mat3_t cst_transpose(cst_mat3_t m) {
    return cst_make_mat3(make_float3(m.x.x, m.y.x, m.z.x), make_float3(m.x.y, m.y.y, m.z.y), make_float3(m.x.z, m.y.z, m.z.z));
}
__DEVICE__ cst_mat3_t cst_mmul(cst_mat3_t a, cst_mat3_t b) {
    cst_mat3_t t = cst_transpose(b);
    return cst_make_mat3(make_float3(cst_dot3(a.x, t.x), cst_dot3(a.x, t.y), cst_dot3(a.x, t.z)),
                     make_float3(cst_dot3(a.y, t.x), cst_dot3(a.y, t.y), cst_dot3(a.y, t.z)),
                     make_float3(cst_dot3(a.z, t.x), cst_dot3(a.z, t.y), cst_dot3(a.z, t.z)));
}
__DEVICE__ float3 cst_sdiv(float3 v, float d) { return make_float3(v.x / d, v.y / d, v.z / d); }
__DEVICE__ cst_mat3_t cst_inv(cst_mat3_t m) {
    float a = m.x.x, b = m.x.y, c = m.x.z, d = m.y.x, e = m.y.y, f = m.y.z, g = m.z.x, h = m.z.y, i = m.z.z;
    float A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g;
    float det = a * A + b * B + c * C;
    return cst_make_mat3(cst_sdiv(make_float3(A, -(b * i - c * h), b * f - c * e), det),
                     cst_sdiv(make_float3(B, a * i - c * g, -(a * f - c * d)), det),
                     cst_sdiv(make_float3(C, -(a * h - b * g), a * e - b * d), det));
}
__DEVICE__ cst_mat3_t cst_diag(float3 v) {
    return cst_make_mat3(make_float3(v.x, 0.0f, 0.0f), make_float3(0.0f, v.y, 0.0f), make_float3(0.0f, 0.0f, v.z));
}

__DEVICE__ cst_prim_t cst_prims(float rx, float ry, float gx, float gy, float bx, float by, float wx, float wy) {
    cst_prim_t p; p.rx = rx; p.ry = ry; p.gx = gx; p.gy = gy; p.bx = bx; p.by = by; p.wx = wx; p.wy = wy; return p;
}

__DEVICE__ cst_prim_t cst_gamut_prims(int g) {
__GAMUTS__
}

__DEVICE__ float3 cst_xy_to_XYZ(float x, float y) { return make_float3(x / y, 1.0f, (1.0f - x - y) / y); }

// RGB -> XYZ normalised primary matrix (SMPTE RP 177)
__DEVICE__ cst_mat3_t cst_npm(cst_prim_t p) {
    cst_mat3_t P = cst_transpose(cst_make_mat3(cst_xy_to_XYZ(p.rx, p.ry), cst_xy_to_XYZ(p.gx, p.gy), cst_xy_to_XYZ(p.bx, p.by)));
    float3 S = cst_mul(cst_inv(P), cst_xy_to_XYZ(p.wx, p.wy));
    return cst_mmul(P, cst_diag(S));
}

__DEVICE__ cst_mat3_t cst_cat_matrix(float3 ws, float3 wd, int method) {
    cst_mat3_t M;
    if (method == 0) {  // Bradford
        M = cst_make_mat3(make_float3(0.8951f, 0.2664f, -0.1614f), make_float3(-0.7502f, 1.7135f, 0.0367f),
                      make_float3(0.0389f, -0.0685f, 1.0296f));
    } else if (method == 1) {  // CAT02
        M = cst_make_mat3(make_float3(0.7328f, 0.4296f, -0.1624f), make_float3(-0.7036f, 1.6975f, 0.0061f),
                      make_float3(0.0030f, 0.0136f, 0.9834f));
    } else {
        return cst_diag(make_float3(1.0f, 1.0f, 1.0f));
    }
    float3 d = cst_mul(M, wd), sv = cst_mul(M, ws);
    return cst_mmul(cst_inv(M), cst_mmul(cst_diag(make_float3(d.x / sv.x, d.y / sv.y, d.z / sv.z)), M));
}

__DEVICE__ cst_mat3_t cst_gamut_matrix(int gi, int go, int method) {
    if (gi == go) return cst_diag(make_float3(1.0f, 1.0f, 1.0f));  // same gamut: exact passthrough
    cst_prim_t pi = cst_gamut_prims(gi), po = cst_gamut_prims(go);
    cst_mat3_t m = cst_mmul(cst_inv(cst_npm(po)), cst_mmul(cst_cat_matrix(cst_xy_to_XYZ(pi.wx, pi.wy), cst_xy_to_XYZ(po.wx, po.wy), method), cst_npm(pi)));
    return m;
}

// ------------------------------------------------------------------ transfer functions
__DEVICE__ float cst_spow(float x, float p) { return x < 0.0f ? -_powf(-x, p) : _powf(x, p); }

// LogC4 constants
#define LC4_A ((262144.0f - 16.0f) / 117.45f)
#define LC4_B ((1023.0f - 95.0f) / 1023.0f)
#define LC4_C (95.0f / 1023.0f)

__DEVICE__ float cst_lc4_s(void) { return (7.0f * _logf(2.0f) * _exp2f(7.0f - 14.0f * LC4_C / LC4_B)) / (LC4_A * LC4_B); }
__DEVICE__ float cst_lc4_t(void) { return (_exp2f(14.0f * (-LC4_C / LC4_B) + 6.0f) - 64.0f) / LC4_A; }

// curve -> scene linear (raw)
__DEVICE__ float cst_to_linear_raw(float y, int c) {
    if (c == C_LIN) return y;
    if (c == C_KL3) {
        const float a = 66.64f, b = 0.296f, cc = 0.907136f, d = 0.092864f, cut = -0.008239f, s = 0.017178f;
        return y < 0.0f ? y * s + cut : (_exp10f(((y - d) / b) / cc) - 1.0f) / a;
    }
    if (c == C_LOGC3) {
        const float cut = 0.010591f, a = 5.555556f, b = 0.052272f, cc = 0.247190f, d = 0.385537f, e = 5.367655f, f = 0.092809f;
        return y > e * cut + f ? (_exp10f((y - d) / cc) - b) / a : (y - f) / e;
    }
    if (c == C_LOGC4) return y >= 0.0f ? (_exp2f(14.0f * (y - LC4_C) / LC4_B + 6.0f) - 64.0f) / LC4_A : y * cst_lc4_s() + cst_lc4_t();
    if (c == C_DI) {
        const float a = 0.0075f, b = 7.0f, cc = 0.07329248f, m = 10.44426855f, log_cut = 0.02740668f;
        return y <= log_cut ? y / m : _exp2f(y / cc - b) - a;
    }
    if (c == C_SLOG3)
        return y >= 171.2102946929f / 1023.0f ? _exp10f((y * 1023.0f - 420.0f) / 261.5f) * 0.19f - 0.01f
                                             : (y * 1023.0f - 95.0f) * 0.01125f / (171.2102946929f - 95.0f);
    if (c == C_L3G10) {
        const float a = 0.224282f, b = 155.975327f, cc = 0.01f, g = 15.1927f;
        return y < 0.0f ? y / g - cc : (_exp10f(y / a) - 1.0f) / b - cc;
    }
    if (c == C_VLOG) return y < 0.181f ? (y - 0.125f) / 5.6f : _exp10f((y - 0.598206f) / 0.241514f) - 0.00873f;
    if (c == C_CLOG3) {
        float x;
        if (y < 0.097465473f) x = -(_exp10f((0.12783901f - y) / 0.36726845f) - 1.0f) / 14.98325f;
        else if (y <= 0.15277891f) x = (y - 0.12512219f) / 1.9754798f;
        else x = (_exp10f((y - 0.12240537f) / 0.36726845f) - 1.0f) / 14.98325f;
        return x * 0.9f;
    }
    if (c == C_BMDG5) {
        const float A = 0.08692876065491224f, B = 0.005494072432257808f, C = 0.5300133392291939f;
        const float D = 8.283605932402494f, E = 0.09246575342465753f, LIN_CUT = 0.005f;
        return y < D * LIN_CUT + E ? (y - E) / D : _expf((y - C) / A) - B;
    }
    if (c == C_FLOG2) {
        const float a = 5.555556f, b = 0.064829f, cc = 0.245281f, d = 0.384316f, e = 8.799461f, f = 0.092864f;
        const float cut2 = 0.100686685370811f;
        return y >= cut2 ? (_exp10f((y - d) / cc) - b) / a : (y - f) / e;
    }
    if (c == C_ACESCCT)
        return y <= 0.155251141552511f ? (y - 0.0729055341958355f) / 10.5402377416545f : _exp2f(y * 17.52f - 9.72f);
    if (c == C_ACESCC) {
        if (y < (9.72f - 15.0f) / 17.52f) return (_exp2f(y * 17.52f - 9.72f) - _exp2f(-16.0f)) * 2.0f;
        return _exp2f(y * 17.52f - 9.72f);
    }
    if (c == C_R709) {
        float a = _fabs(y), x = a < 0.081f ? a / 4.5f : _powf((a + 0.099f) / 1.099f, 1.0f / 0.45f);
        return y < 0.0f ? -x : x;
    }
    if (c == C_SRGB) {
        float a = _fabs(y), x = a <= 0.04045f ? a / 12.92f : _powf((a + 0.055f) / 1.055f, 2.4f);
        return y < 0.0f ? -x : x;
    }
    if (c == C_G22) return cst_spow(y, 2.2f);
    if (c == C_G24) return cst_spow(y, 2.4f);
    if (c == C_G26) return cst_spow(y, 2.6f);
    if (c == C_PQ) {
        const float m1 = 0.1593017578125f, m2 = 78.84375f, c1 = 0.8359375f, c2 = 18.8515625f, c3 = 18.6875f;
        float p = _powf(_fmaxf(_fabs(y), 0.0f), 1.0f / m2);
        float x = 100.0f * _powf(_fmaxf(p - c1, 0.0f) / (c2 - c3 * p), 1.0f / m1);  // 1.0 = 100 nits
        return y < 0.0f ? -x : x;
    }
    if (c == C_DLOG) {
        // DJI D-Log (X7 2017 / Zenmuse X9 + Ronin 4D 2022 white papers). Decode cut is the exact
        // branch join (paper rounds it to 0.14); log constants are the exact inverse of the encode.
        return y <= 0.139895f ? (y - 0.0929f) / 6.025f : (_exp10f((y - 0.584555f) / 0.256663f) - 0.0108f) / 0.9892f;
    }
    return y;
}

// curve -> scene linear, clamped to +/-65504 (half-float range, as ACES does) so out-of-range input
// can never overflow to inf and turn into NaN in the matrix stage
__DEVICE__ float cst_to_linear(float y, int c) { return _fminf(_fmaxf(cst_to_linear_raw(y, c), -65504.0f), 65504.0f); }

// scene linear -> curve
__DEVICE__ float cst_from_linear(float x, int c) {
    if (c == C_LIN) return x;
    if (c == C_KL3) {
        const float a = 66.64f, b = 0.296f, cc = 0.907136f, d = 0.092864f, cut = -0.008239f, s = 0.017178f;
        return x < cut ? (x - cut) / s : _log10f(a * x + 1.0f) * b * cc + d;
    }
    if (c == C_LOGC3) {
        const float cut = 0.010591f, a = 5.555556f, b = 0.052272f, cc = 0.247190f, d = 0.385537f, e = 5.367655f, f = 0.092809f;
        return x > cut ? cc * _log10f(a * x + b) + d : e * x + f;
    }
    if (c == C_LOGC4) return x >= cst_lc4_t() ? ((_log2f(LC4_A * x + 64.0f) - 6.0f) / 14.0f) * LC4_B + LC4_C : (x - cst_lc4_t()) / cst_lc4_s();
    if (c == C_DI) {
        const float a = 0.0075f, b = 7.0f, cc = 0.07329248f, m = 10.44426855f, lin_cut = 0.00262409f;
        return x > lin_cut ? (_log2f(x + a) + b) * cc : x * m;
    }
    if (c == C_SLOG3)
        return x >= 0.01125f ? (420.0f + _log10f((x + 0.01f) / 0.19f) * 261.5f) / 1023.0f
                             : (x * (171.2102946929f - 95.0f) / 0.01125f + 95.0f) / 1023.0f;
    if (c == C_L3G10) {
        const float a = 0.224282f, b = 155.975327f, cc = 0.01f, g = 15.1927f;
        float t = x + cc;
        return t < 0.0f ? t * g : a * _log10f(t * b + 1.0f);
    }
    if (c == C_VLOG) return x < 0.01f ? 5.6f * x + 0.125f : 0.241514f * _log10f(x + 0.00873f) + 0.598206f;
    if (c == C_CLOG3) {
        float t = x / 0.9f;
        if (t < -0.014f) return -0.36726845f * _log10f(-t * 14.98325f + 1.0f) + 0.12783901f;
        if (t <= 0.014f) return 1.9754798f * t + 0.12512219f;
        return 0.36726845f * _log10f(t * 14.98325f + 1.0f) + 0.12240537f;
    }
    if (c == C_BMDG5) {
        const float A = 0.08692876065491224f, B = 0.005494072432257808f, C = 0.5300133392291939f;
        const float D = 8.283605932402494f, E = 0.09246575342465753f, LIN_CUT = 0.005f;
        return x < LIN_CUT ? D * x + E : A * _logf(x + B) + C;
    }
    if (c == C_FLOG2) {
        const float a = 5.555556f, b = 0.064829f, cc = 0.245281f, d = 0.384316f, e = 8.799461f, f = 0.092864f;
        const float cut1 = 0.000889f;
        return x >= cut1 ? cc * _log10f(a * x + b) + d : e * x + f;
    }
    if (c == C_ACESCCT) return x <= 0.0078125f ? 10.5402377416545f * x + 0.0729055341958355f : (_log2f(x) + 9.72f) / 17.52f;
    if (c == C_ACESCC) {
        if (x <= 0.0f) return (-16.0f + 9.72f) / 17.52f;
        if (x < _exp2f(-15.0f)) return (_log2f(_exp2f(-16.0f) + x * 0.5f) + 9.72f) / 17.52f;
        return (_log2f(x) + 9.72f) / 17.52f;
    }
    if (c == C_R709) {
        float a = _fabs(x), y = a < 0.018f ? 4.5f * a : 1.099f * _powf(a, 0.45f) - 0.099f;
        return x < 0.0f ? -y : y;
    }
    if (c == C_SRGB) {
        float a = _fabs(x), y = a <= 0.0031308f ? 12.92f * a : 1.055f * _powf(a, 1.0f / 2.4f) - 0.055f;
        return x < 0.0f ? -y : y;
    }
    if (c == C_G22) return cst_spow(x, 1.0f / 2.2f);
    if (c == C_G24) return cst_spow(x, 1.0f / 2.4f);
    if (c == C_G26) return cst_spow(x, 1.0f / 2.6f);
    if (c == C_PQ) {
        const float m1 = 0.1593017578125f, m2 = 78.84375f, c1 = 0.8359375f, c2 = 18.8515625f, c3 = 18.6875f;
        float l = _powf(_fabs(x) / 100.0f, m1);
        float y = _powf((c1 + c2 * l) / (1.0f + c3 * l), m2);
        return x < 0.0f ? -y : y;
    }
    if (c == C_DLOG) return x <= 0.0078f ? 6.025f * x + 0.0929f : _log10f(x * 0.9892f + 0.0108f) * 0.256663f + 0.584555f;
    return x;
}

__DEVICE__ float3 transform(int p_Width, int p_Height, int p_X, int p_Y, float p_R, float p_G, float p_B) {
    int ic = (int)input_curve, oc = (int)output_curve;
    float3 lin = make_float3(cst_to_linear(p_R, ic), cst_to_linear(p_G, ic), cst_to_linear(p_B, ic));
    float3 rgb = cst_mul(cst_gamut_matrix((int)input_gamut, (int)output_gamut, (int)cat_method), lin);
    return make_float3(cst_from_linear(rgb.x, oc), cst_from_linear(rgb.y, oc), cst_from_linear(rgb.z, oc));
}
'''

def build(path):
    s = DCTL
    s = s.replace('__INPUT_GAMUT__', combo('input_gamut', 'Input Color Space', 'IG_', GAMUTS, 0))
    s = s.replace('__INPUT_CURVE__', combo('input_curve', 'Input Gamma', 'IC_', CURVES, 1))
    s = s.replace('__OUTPUT_GAMUT__', combo('output_gamut', 'Output Color Space', 'OG_', GAMUTS, 3))
    s = s.replace('__OUTPUT_CURVE__', combo('output_curve', 'Output Gamma', 'OC_', CURVES, 4))
    s = s.replace('__GAMUTS__', gamut_fn()).replace('__CURVE_IDS__', curve_ids())
    open(path, 'w').write(s.replace('__VERSION__', VERSION))



# ---------------------------------------------------------------- Color Remap mk2 (one-node KineLog3 / D-Log -> ARRI / DWG / Kine)
# ARRI LogC3, SUP 3.x, "Linear Scene Exposure Factor": EI -> (cut, a, b, c, d, e, f)
_LOGC3 = {
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

REMAP_HEADER = r'''// Color Remap mk2 v__VERSION__ - Kinefinity KineLog3 or DJI D-Log -> ARRI / DaVinci / Kinefinity, one node, no setup.
// Companion to Color Space Transform mk2. MIT licence - see the project README.
//
// Source (all Kinefinity sources use the KineLog3 curve):
//   Kinefinity Edge 6K / MM2 LF   - Kinefinity Wide Gamut, as published by Kinefinity
//   DJI D-Log / D-Gamut           - Ronin 4D 6K & 8K, Zenmuse X9-6K / X9-8K (Inspire 3), X7. Same curve at every EI
//   Kinefinity Edge 8K            - PROVISIONAL: native primaries not yet published, uses Kinefinity Wide Gamut
//   Kinefinity Vista              - PROVISIONAL: native primaries not yet published, uses Kinefinity Wide Gamut
//   Kinefinity BT.2020 mode       - KineOS 8 "BT.2020" ProRes gamut on any MAVO Edge / mark2 camera - exact
// Target:
//   ARRI LogC3 / AWG3     (ALEXA Mini LF, ALEXA LF, Mini, SXT...)  - pick the EI the ALEXA was rated at
//   ARRI LogC4 / AWG4     (ALEXA 35, ALEXA 265)
//   DaVinci WG / Intermediate
//   Kinefinity Wide Gamut / KineLog3              (e.g. match DJI footage to a Kinefinity A-cam)
// Remap:
//   Color + Gamma  : full conversion. Output is genuine LogC3/LogC4/DI footage.
//   Color only     : primaries are converted to the target gamut but the source log curve is kept,
//                    i.e. only the color of each pixel moves; tonality/contrast stay as shot.
//
// KineLog3 + Kinefinity Wide Gamut: Kinefinity "KineLog3 Technical Specifications" v2 (24 Sep 2025).
// DJI D-Log + D-Gamut: DJI "White Paper on D-Log and D-Gamut of DJI Cinema Color System" (Zenmuse X9, 2022).
// Generated by tools/build_dctl.py - edit that, not this file.

// clang-format off
DEFINE_UI_PARAMS(source, Source, DCTLUI_COMBO_BOX, 0, {S_KINE, S_DJI, S_KINE8K, S_VISTA, S_KBT2020}, {Kinefinity KineLog3 - Edge 6K - MM2 LF, DJI D-Log - D-Gamut, Kinefinity KineLog3 - Edge 8K - provisional, Kinefinity KineLog3 - Vista - provisional, Kinefinity KineLog3 - BT.2020 mode})
DEFINE_UI_PARAMS(target, Target, DCTLUI_COMBO_BOX, 0, {T_LOGC3, T_LOGC4, T_DWG, T_KINE}, {ARRI LogC3 - AWG3, ARRI LogC4 - AWG4, DaVinci WG - Intermediate, Kinefinity KineLog3 - KWG})
DEFINE_UI_PARAMS(mode, Remap, DCTLUI_COMBO_BOX, 0, {MODE_FULL, MODE_COLOR}, {Color + Gamma, Color only})
__EI_COMBO__
DEFINE_UI_PARAMS(exposure, Exposure Trim stops, DCTLUI_SLIDER_FLOAT, 0.0, -3.0, 3.0, 0.01)
// clang-format on
'''

REMAP_TRANSFORM = r'''
__DEVICE__ float cst_lin_to_logc3_ei(float x, int ei_idx) {
    float cut, a, b, c, d, e, f;
__EI_BRANCHES__
    return x > cut ? c * _log10f(a * x + b) + d : e * x + f;
}

__DEVICE__ float3 transform(int p_Width, int p_Height, int p_X, int p_Y, float p_R, float p_G, float p_B) {
    int t = (int)target;
    int g = t == 0 ? 1 : (t == 1 ? 2 : (t == 2 ? 3 : 0));  // AWG3, AWG4, DWG, KWG in cst_gamut_prims()
    int src = (int)source;
    int sg = 0;                                              // KWG (Edge 6K / MM2 LF)
    if (src == 1) sg = __G_DGAMUT__;                         // DJI D-Gamut
    else if (src == 2) sg = __G_KWG8K__;                     // Edge 8K (provisional)
    else if (src == 3) sg = __G_KWGVST__;                    // Vista (provisional)
    else if (src == 4) sg = __G_KBT2020__;                   // KineOS 8 BT.2020 mode
    int sc = src == 1 ? C_DLOG : C_KL3;
    float k = _exp2f(exposure);
    float3 lin = make_float3(cst_to_linear(p_R, sc), cst_to_linear(p_G, sc), cst_to_linear(p_B, sc));
    float3 rgb = cst_mul(cst_gamut_matrix(sg, g, 0), lin);
    rgb = make_float3(rgb.x * k, rgb.y * k, rgb.z * k);
    if ((int)mode == 1) return make_float3(cst_from_linear(rgb.x, sc), cst_from_linear(rgb.y, sc), cst_from_linear(rgb.z, sc));
    if (t == 0) {
        int e = (int)ei;
        return make_float3(cst_lin_to_logc3_ei(rgb.x, e), cst_lin_to_logc3_ei(rgb.y, e), cst_lin_to_logc3_ei(rgb.z, e));
    }
    int oc = t == 1 ? C_LOGC4 : (t == 2 ? C_DI : C_KL3);
    return make_float3(cst_from_linear(rgb.x, oc), cst_from_linear(rgb.y, oc), cst_from_linear(rgb.z, oc));
}
'''

def build_remap(path):
    eis = sorted(_LOGC3)
    ei_combo = (f'DEFINE_UI_PARAMS(ei, LogC3 EI, DCTLUI_COMBO_BOX, {eis.index(800)}, '
                f'{{{", ".join(f"EI{e}" for e in eis)}}}, {{{", ".join(f"EI {e}" for e in eis)}}})')
    br = []
    for i, e in enumerate(eis):
        p = _LOGC3[e]
        br.append(f'    {"if" if i == 0 else "else if"} (ei_idx == {i}) {{ cut={p[0]}f; a={p[1]}f; b={p[2]}f; c={p[3]}f; d={p[4]}f; e={p[5]}f; f={p[6]}f; }}  // EI {e}')
    br.append('    else { cut=0.010591f; a=5.555556f; b=0.052272f; c=0.247190f; d=0.385537f; e=5.367655f; f=0.092809f; }')
    body = DCTL[DCTL.index('__CURVE_IDS__'):DCTL.index('__DEVICE__ float3 transform(')]
    body = body.replace('__CURVE_IDS__', curve_ids()).replace('__GAMUTS__', gamut_fn())
    s = REMAP_HEADER.replace('__EI_COMBO__', ei_combo) + '\n' + body + REMAP_TRANSFORM.replace('__EI_BRANCHES__', '\n'.join(br))
    for gid in ('DGAMUT', 'KWG8K', 'KWGVST', 'KBT2020'):
        s = s.replace(f'__G_{gid}__', str([g_[0] for g_ in GAMUTS].index(gid)))
    open(path, 'w').write(s.replace('__VERSION__', VERSION))


CST_NAME = 'Color Space Transform mk2.dctl'
REMAP_NAME = 'Color Remap mk2.dctl'

if __name__ == '__main__':
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dctl')
    os.makedirs(out_dir, exist_ok=True)
    for fn, name in ((build, CST_NAME), (build_remap, REMAP_NAME)):
        path = os.path.join(out_dir, name)
        fn(path)
        print('wrote', path)
