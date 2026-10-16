"""Synthetic end-to-end test: fake an ALEXA + a 'different' Kine sensor shooting the same chart."""
import sys, os, numpy as np, colour
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kl3_logc3 as k
out = os.path.dirname(os.path.abspath(__file__))
cc = colour.CCS_COLOURCHECKERS['ColorChecker24 - After November 2014']
XYZ = colour.xyY_to_XYZ(np.array(list(cc.data.values())))
XYZ = colour.chromatic_adaptation(XYZ, colour.xy_to_XYZ(cc.illuminant), colour.xy_to_XYZ(k.D65))
ref = XYZ @ np.linalg.inv(k.AWG3_TO_XYZ).T                 # "ALEXA" linear AWG3
# Kine sensor = ALEXA seen through a different spectral response: a cross-talk matrix +
# mild non-linear hue twist + 0.4 stop under-exposure. Neutral-preserving.
rng = np.random.default_rng(1)
E = np.eye(3) + rng.normal(0, 0.06, (3, 3)); E /= E.sum(1, keepdims=True)
twist = lambda x: x + 0.05 * (np.sqrt(np.maximum(x[:, [0]] * x[:, [1]], 0)) - (x[:, [0]] + x[:, [1]]) / 2) * np.array([1, -1, 0.5])
kine_awg = twist(ref @ E.T) * 2 ** -0.4
kine_kwg = kine_awg @ np.linalg.inv(k.KWG_TO_AWG3).T
kl = k.kl3_encode(kine_kwg); al = k.logc3_encode(ref, 800)
np.savetxt(os.path.join(out, 'kine.csv'), kl, delimiter=',', header='R,G,B', comments='', fmt='%.6f')
np.savetxt(os.path.join(out, 'alexa.csv'), al, delimiter=',', header='R,G,B', comments='', fmt='%.6f')
# also render 16-bit TIFF chart frames, slightly rotated, to exercise the image sampler
import cv2
def render(vals, path, rot):
    W, H = 1200, 800; img = np.full((H, W, 3), 0.05)
    x0, y0, cw, ch = 200, 150, 130, 125
    for i, v in enumerate(vals):
        r, c = divmod(i, 6); img[y0+r*ch+8:y0+(r+1)*ch-8, x0+c*cw+8:x0+(c+1)*cw-8] = v
    Mr = cv2.getRotationMatrix2D((W/2, H/2), rot, 1.0)
    img = cv2.warpAffine(img, Mr, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0.05,)*3)
    img += np.random.default_rng(2).normal(0, 0.002, img.shape)
    cv2.imwrite(path, (np.clip(img, 0, 1)[..., ::-1] * 65535).astype(np.uint16))
    corners = np.array([[x0, y0], [x0+6*cw, y0], [x0+6*cw, y0+4*ch], [x0, y0+4*ch]], float)
    return (np.hstack([corners, np.ones((4, 1))]) @ Mr.T)
for name, vals, rot in (('kine', kl, 3.0), ('alexa', al, -2.0)):
    cs = render(vals, os.path.join(out, f'{name}.tif'), rot)
    print(name, ' '.join(f'{x:.0f},{y:.0f}' for x, y in cs))
