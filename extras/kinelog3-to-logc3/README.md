# Extras: KineLog3 → ARRI LogC3, with color-chart match

| File | What it is |
|---|---|
| `KineLog3_to_LogC3.dctl` | Kinefinity KineLog3 / KWG to ARRI LogC3 / AWG3, with an EI selector (160–1600), exposure trim and a chart-match switch (identity until you generate one). |
| `KineLog3_KWG_to_LogC3_AWG3_EI800.cube` | The same transform at EI 800 as a 65³ LUT, with output clamped to 0–1. Accurate to about 2 10-bit code values inside Rec.709; use the DCTL for extreme saturation. |
| `kl3_logc3.py` | Rebuilds the DCTL and `.cube` at any EI, and solves a chart match. |

## Chart match: make one camera match another on a ColorChecker
The spec transform puts both cameras into the same color language. A chart match goes further and corrects the small differences in how the two sensors see color.

1. Shoot a ColorChecker 24 on both cameras under the same light, with the same white balance and sensible exposure.
2. Export one ungraded frame from each camera, as 16-bit TIFF or EXR with no LUT and data levels.
3. Run:
```bash
pip install -r requirements.txt
# corners: TL = dark skin, TR = bluish green, BR = black, BL = white (pixel coords)
python3 kl3_logc3.py match --images kine.tif alexa.tif \
    --kine-corners 187,171 966,130 993,630 214,671 \
    --alexa-corners 209,136 988,163 971,663 192,636 \
    --ei 800 --out my_match
```
Instead of images, you can pass two CSVs of 24 R,G,B log values sampled in Resolve: `--csv kine.csv alexa.csv` (see `test/` for examples).

What the tool does:
* writes `debug_*.png` so you can check that every sample box sits inside its patch;
* prints the ΔE2000 for each patch, before and after the match;
* writes `KineLog3_to_LogC3_chartmatch.dctl`, a matching `.cube`, and `chart_match.json`.

The model is a degree-2 **root-polynomial** fit in linear AWG3. It is exposure-invariant, constrained so grey maps exactly to grey, and refined to minimise ΔE2000. Use `--model matrix` for a plain 3×3, which is better for noisy or unevenly lit charts. The DCTL's *Chart Match Amount* slider blends the fit back toward the spec transform.

## Other commands
```bash
python3 kl3_logc3.py check                      # print reference values and round-trip errors
python3 kl3_logc3.py build --ei 1280 --out out  # rebuild the DCTL + .cube at another EI
```
