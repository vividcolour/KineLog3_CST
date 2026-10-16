"""
Compile a Resolve DCTL outside Resolve so it can be tested.

Backends
  cpp     g++ -std=c++14   (stands in for CUDA / Metal, which are C++-based)
  c99     gcc -std=c99     (catches any C++-only construct)
  opencl  real OpenCL C kernel via pyopencl (pocl CPU device works; used by Resolve on AMD/Intel GPUs)

Each DEFINE_UI_PARAMS becomes a value set per pixel, so one build can evaluate any combination of
UI settings:  run(params_list, rgb) -> rgb_out, where params_list[i] is the UI values for pixel i.
"""
import os, re, subprocess, tempfile
import numpy as np

_UI = re.compile(r'^DEFINE_UI_PARAMS\((.*)\)\s*$', re.M)


def parse_ui(src):
    """Return (names, enum_lines, src_without_ui)."""
    names, enums, types = [], [], []
    def rep(m):
        args = [a.strip() for a in re.split(r',(?![^{]*})', m.group(1))]
        names.append(args[0])
        types.append('int' if args[2] in ('DCTLUI_COMBO_BOX', 'DCTLUI_CHECK_BOX') else 'float')
        if args[2] == 'DCTLUI_COMBO_BOX':
            enums.append('enum { %s };' % args[4].strip('{}'))
        return ''
    out = _UI.sub(rep, src)
    return names, types, enums, out


C_PRELUDE = r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#define __DEVICE__ static
typedef struct { float x, y, z; } float3;
static float3 make_float3(float a, float b, float c) { float3 v; v.x = a; v.y = b; v.z = c; return v; }
#define _exp10f(x) powf(10.0f, (x))
#define _log10f log10f
#define _log2f log2f
#define _logf logf
#define _expf expf
#define _exp2f exp2f
#define _powf powf
#define _fabs fabsf
#define _fmaxf fmaxf
#define _fminf fminf
#define _sqrtf sqrtf
'''

OCL_PRELUDE = r'''
#define __DEVICE__
#define make_float3(a, b, c) ((float3)((a), (b), (c)))
#define _exp10f exp10
#define _log10f log10
#define _log2f log2
#define _logf log
#define _expf exp
#define _exp2f exp2
#define _powf pow
#define _fabs fabs
#define _fmaxf fmax
#define _fminf fmin
#define _sqrtf sqrt
'''


def _patch_transform(src, extra_arg, names, types):
    """UI params become locals at the top of transform(), filled from the UI array (same scoping as Resolve:
    visible in transform, shadowable by helper-function arguments of the same name)."""
    sig = '__DEVICE__ float3 transform(int p_Width, int p_Height, int p_X, int p_Y, float p_R, float p_G, float p_B) {'
    assert sig in src, 'transform() signature not found'
    decl = ''.join(f'\n    {t} {n} = ({t})UI[{i}];' for i, (n, t) in enumerate(zip(names, types)))
    return src.replace(sig, f'__DEVICE__ float3 transform({extra_arg}, int p_Width, int p_Height, int p_X, int p_Y, float p_R, float p_G, float p_B) {{' + decl)


class NativeDCTL:
    """cpp or c99 build. Reads lines of '<params...> r g b' on stdin."""

    def __init__(self, dctl_path, lang='cpp', workdir=None):
        src = open(dctl_path).read()
        self.names, types, enums, body = parse_ui(src)
        body = _patch_transform(body, 'const float* UI', self.names, types)
        n = len(self.names)
        main = r'''
int main(void) {
    float P[%d]; float r, g, b; int i;
    for (;;) {
        for (i = 0; i < %d; i++) if (scanf("%%f", &P[i]) != 1) return 0;
        if (scanf("%%f %%f %%f", &r, &g, &b) != 3) return 0;
        float3 o = transform(P, 0, 0, 0, 0, r, g, b);
        printf("%%.9g %%.9g %%.9g\n", o.x, o.y, o.z);
    }
}
''' % (n, n)
        code = C_PRELUDE + '\n'.join(enums) + '\n' + body + main
        self.dir = workdir or tempfile.mkdtemp(prefix='dctl_')
        ext, cc = ('cpp', ['g++', '-std=c++14']) if lang == 'cpp' else ('c', ['gcc', '-std=c99'])
        cfile = os.path.join(self.dir, f'{os.path.basename(dctl_path)}.{lang}.{ext}'.replace(' ', '_'))
        self.exe = cfile + '.bin'
        open(cfile, 'w').write(code)
        cmd = cc + ['-O2', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter', '-Wno-unused-function',
                    '-Wno-unused-variable', '-Wno-unused-but-set-variable', '-o', self.exe, cfile, '-lm']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f'{lang} compile failed:\n{r.stderr[:4000]}')

    def run(self, params, rgb):
        params = np.atleast_2d(np.asarray(params, float)); rgb = np.atleast_2d(np.asarray(rgb, float))
        if len(params) == 1 and len(rgb) > 1:
            params = np.repeat(params, len(rgb), 0)
        data = np.hstack([params, rgb])
        inp = '\n'.join(' '.join(repr(float(v)) for v in row) for row in data)
        out = subprocess.run([self.exe], input=inp, capture_output=True, text=True, check=True).stdout
        return np.array([[float(v) for v in l.split()] for l in out.splitlines()]).reshape(-1, 3)


class OpenCLDCTL:
    def __init__(self, dctl_path, fast_math=False):
        import pyopencl as cl
        self.cl = cl
        src = open(dctl_path).read()
        self.names, types, enums, body = parse_ui(src)
        body = _patch_transform(body, '__global const float* UI', self.names, types)
        n = len(self.names)
        kernel = r'''
__kernel void run_dctl(__global const float* params, __global const float* rgb, __global float* out) {
    int i = get_global_id(0);
    float3 o = transform(params + i * %d, 0, 0, 0, 0, rgb[3 * i], rgb[3 * i + 1], rgb[3 * i + 2]);
    out[3 * i] = o.x; out[3 * i + 1] = o.y; out[3 * i + 2] = o.z;
}
''' % n
        code = OCL_PRELUDE + '\n'.join(enums) + '\n' + body + kernel
        self.ctx = cl.create_some_context(interactive=False)
        self.q = cl.CommandQueue(self.ctx)
        opts = ['-cl-std=CL1.2', '-Werror'] + (['-cl-fast-relaxed-math'] if fast_math else [])
        self.prg = cl.Program(self.ctx, code).build(options=opts)
        self.build_log = self.prg.get_build_info(self.ctx.devices[0], cl.program_build_info.LOG)

    def run(self, params, rgb):
        cl = self.cl
        params = np.atleast_2d(np.asarray(params, np.float32)); rgb = np.atleast_2d(np.asarray(rgb, np.float32))
        if len(params) == 1 and len(rgb) > 1:
            params = np.repeat(params, len(rgb), 0)
        params = np.ascontiguousarray(params, np.float32); rgb = np.ascontiguousarray(rgb, np.float32)
        mf = cl.mem_flags
        bp = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=params)
        bi = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=rgb)
        out = np.empty_like(rgb)
        bo = cl.Buffer(self.ctx, mf.WRITE_ONLY, out.nbytes)
        self.prg.run_dctl(self.q, (len(rgb),), None, bp, bi, bo)
        cl.enqueue_copy(self.q, out, bo)
        return out.astype(float)


def opencl_available():
    try:
        import pyopencl as cl
        return any(p.get_devices() for p in cl.get_platforms())
    except Exception:
        return False
