# Color Space Transform mk2

A **Color Space Transform DCTL for DaVinci Resolve** that works like the stock CST node, and adds camera color spaces the stock CST doesn't have:

- **Kinefinity KineLog3**: MAVO Edge 6K, MAVO mark2 LF, MAVO Edge 8K and Vista, including KineOS 8's BT.2020 mode.
- **DJI D-Log / D-Gamut**: Ronin 4D 6K and 8K, Zenmuse X9 (incl. Inspire 3), X7.

### Supported cameras
| Camera | Status |
|---|---|
| Kinefinity MAVO Edge 6K, MAVO mark2 LF | ✅ Kinefinity's published KineLog3 + Kinefinity Wide Gamut |
| Kinefinity MAVO Edge 6K / 8K, MAVO mark2, recording KineOS 8 **BT.2020** gamut | ✅ Exact: KineLog3 + standard BT.2020 |
| Kinefinity **MAVO Edge 8K**, **Vista** (native gamut) | ⚠️ Curve exact; **primaries provisional**, since Kinefinity hasn't published them yet ([why and how to verify](docs/SPECIFICATION.md#33-kinefinity-wide-gamut-native-gamut)) |
| DJI Ronin 4D 6K & 8K, Zenmuse X9-6K / X9-8K (Inspire 3), Zenmuse X7 | ✅ DJI's published D-Log + D-Gamut, correct at every EI |
| Older KineLOG/KineLOG2 cameras, Kinefinity HLG, DJI D-Log M / D-Log2 | ❌ Not supported (see the spec) |

The complete formulas, constants, color-space tables, sources and verification status are in **[docs/SPECIFICATION.md](docs/SPECIFICATION.md)**.

It also includes ARRI, Sony, RED, Canon, Panasonic, Fujifilm, Blackmagic, ACES and display spaces.

It runs on **macOS and Windows** with any GPU (Metal, CUDA or OpenCL) and needs **DaVinci Resolve Studio**.

[![tests](../../actions/workflows/tests.yml/badge.svg)](../../actions/workflows/tests.yml)

---

## Download & install

1. Go to **[Releases](../../releases/latest)** and download `Color-Space-Transform-mk2-vX.Y.Z.zip` from **Assets**. Don't download "Source code".
2. Unzip it, then run the installer for your system:

   | | |
   |---|---|
   | **macOS** | Double-click **`install-macos.command`**. If macOS blocks it, right-click it and choose **Open**, then **Open** again, or use *System Settings > Privacy & Security > Open Anyway*. Enter your password if asked. |
   | **Windows** | Double-click **`install-windows.bat`** and click **Yes** when it asks for administrator permission. If SmartScreen appears, choose *More info > Run anyway*. |
   | **Linux** | Run `./install-linux.sh` |

3. In Resolve, go to **Project Settings > Color Management > Lookup Tables > Update Lists**, or restart Resolve.

**To install manually:** in Resolve, go to *Project Settings > Color Management > Lookup Tables*, click **Open LUT Folder**, drag the two `.dctl` files in, then click **Update Lists**.

**To uninstall:** run `uninstall-macos.command` or `uninstall-windows.bat`, or delete the `Color Space Transform mk2` folder from Resolve's LUT folder.

---

## What's included

### Color Space Transform mk2
On a node, add *Effects > ResolveFX Color > DCTL* and choose **Color Space Transform mk2**.

| Control | Options |
|---|---|
| Input Color Space / Output Color Space | Kinefinity WG (Edge 6K / MM2 LF, Edge 8K, Vista), Kinefinity BT.2020 (KineOS 8), ARRI Wide Gamut 3, ARRI Wide Gamut 4, DaVinci Wide Gamut, Rec.709 / sRGB, Rec.2020, P3-D65, DCI-P3, ACES AP0, ACES AP1, Sony S-Gamut3, S-Gamut3.Cine, RED Wide Gamut RGB, Panasonic V-Gamut, Canon Cinema Gamut, Blackmagic Wide Gamut, Fujifilm F-Gamut, **DJI D-Gamut** |
| Input Gamma / Output Gamma | Linear, **KineLog3**, ARRI LogC3 (EI 800), ARRI LogC4, DaVinci Intermediate, Sony S-Log3, RED Log3G10, Panasonic V-Log, Canon Log 3, Blackmagic Film Gen 5, Fujifilm F-Log2, ACEScct, ACEScc, Rec.709, sRGB, Gamma 2.2, 2.4 and 2.6, ST 2084 PQ (1.0 = 100 nits), **DJI D-Log** |
| White Point Adaptation | Bradford (default), CAT02 or None. It only matters for ACES and DCI-P3; everything else is D65. |

It does a pure conversion, with no tone mapping, gamut mapping or clipping. For a display image, follow it with a stock CST that does the tone mapping:

```
[Color Space Transform mk2: Kinefinity WG / KineLog3 → DaVinci WG / DaVinci Intermediate]
            ↓  grade here
[stock CST: DaVinci WG / Intermediate → Rec.709 / Gamma 2.4, Tone Mapping: DaVinci]
```

### Color Remap mk2
This converts Kinefinity or DJI footage in one node, with nothing to set up.

| Control | Options |
|---|---|
| Source | Kinefinity KineLog3: Edge 6K / MM2 LF, Edge 8K, Vista or BT.2020 mode. Or DJI D-Log / D-Gamut. |
| Target | ARRI LogC3 / AWG3, ARRI LogC4 / AWG4, DaVinci WG / Intermediate, Kinefinity KineLog3 / KWG |
| Remap | **Color + Gamma** gives a full conversion. **Color only** converts each pixel's color but keeps the original log curve, so tonality and contrast stay as shot. |
| LogC3 EI | 160–1600. Set it to the EI the ALEXA was rated at, so footage drops straight into an ALEXA pipeline. |
| Exposure Trim | ±3 stops, applied in linear light. |

### Extras: [`extras/kinelog3-to-logc3`](extras/kinelog3-to-logc3)
- **`KineLog3_to_LogC3.dctl`** converts KineLog3 to LogC3 (any EI), with an optional **color-chart match**. Shoot a ColorChecker on both cameras and `kl3_logc3.py match` fits a correction and writes a new DCTL and `.cube`.
- **`KineLog3_KWG_to_LogC3_AWG3_EI800.cube`** is a 65³ LUT of the same transform, for software that can't run DCTLs.

---

## Accuracy

Every formula comes from the manufacturer's published specification; the only exceptions are the Edge 8K and Vista primaries, which are marked provisional. Each push runs [`tests/run_tests.py`](tests/run_tests.py), **109 checks** in all. It builds the DCTLs outside Resolve in three ways: as C++ (a stand-in for CUDA and Metal), as strict C99, and as real OpenCL kernels.

| Check | Result |
|---|---|
| KineLog3 18% grey / 90% white | 39.2 / 57.2 IRE, matching Kinefinity's spec |
| KWG→XYZ and KWG→Rec.2020 vs Kinefinity's published matrices | match to every printed decimal |
| DJI D-Log 18% grey | 408 (10-bit), matching DJI's X9 white paper |
| D-Gamut→XYZ vs DJI's published matrix | within 2×10⁻⁴ (the paper prints 4 decimals) |
| All 20 transfer functions, both directions, vs [colour-science](https://www.colour-science.org) | within about 1×10⁻⁶ |
| All 972 combinations of input gamut, output gamut and white-point adaptation | within 2.3×10⁻⁶ |
| End-to-end conversions (e.g. KineLog3→LogC3, D-Log→DaVinci Intermediate) | under 0.1 of a 10-bit code value |
| Color Remap at all 11 LogC3 EIs | matches ARRI LogC3 per EI |
| Robustness: every curve pair, inputs from −100 to 100 | 0 NaN / Inf in 19.2 M output values |
| C++ vs C99 vs OpenCL | agree within 0.1 of a 10-bit code value (0.2 with OpenCL fast-math) |

**Run the tests yourself:**
```bash
pip install -r tests/requirements.txt
python3 tests/run_tests.py
```

### Notes
- **The KineLog3 v1 spec's matrices aren't white-balanced.** Kinefinity's first spec (Oct 2025) printed matrices whose rows sum to 1.02–1.03, which would shift neutrals. This project uses the corrected v2 spec.
- **DJI D-Log is the same at every EI on the X9-6K and X9-8K.** Below native EI (6K: 800 / 5000; 8K: 800 / 4000), DJI feeds the curve a scaled sensor signal, so 18% grey stays at 408 and only the highlight clip drops. Above native EI, it adds analog gain. So one decode is correct at every EI.
- **ARRI LogC3 in the CST uses EI 800**, as Resolve's stock CST does. Use **Color Remap mk2** for other EIs.
- **The LogC3, ACEScc and BT.709 curves** follow their standards, including ACEScc's clamp below zero and the tiny 0.018 knee step in BT.709.
- **Decoded linear values are clamped to ±65504**, the half-float range, as ACES does. Out-of-range input can then never produce NaN pixels.

---

## Sources
- Kinefinity, *KineLog3 Technical Specifications* v2 (24 Sep 2025): [PDF](https://github.com/thatcherfreeman/dwg-transforms/blob/main/specs/KineLog3%20Technical%20Specifications%20v2.pdf)
- DJI, *White Paper on D-Log and D-Gamut of DJI Cinema Color System*, Zenmuse X9 / Ronin 4D, Rev 1.0 (2022): [PDF](https://dl.djicdn.com/downloads/DJI_Ronin_4D/X9_D_Log_D_Gamut_Whitepaper.pdf); and the 2017 X7 edition: [PDF](https://dl.djicdn.com/downloads/zenmuse+x7/20171010/D-Log_D-Gamut_Whitepaper.pdf)
- ARRI, *LogC3 / LogC4 / AWG3 / AWG4* specifications; Blackmagic, *DaVinci Wide Gamut / Intermediate* and *Gen 5*; Sony, RED, Panasonic, Canon, Fujifilm and AMPAS (ACES) published specifications, as implemented in [colour-science](https://github.com/colour-science/colour) 0.4.7.

## Building from source
The `.dctl` files in `dctl/` are generated. To change them, edit [`tools/build_dctl.py`](tools/build_dctl.py) (it holds the tables of color spaces and curves), then:
```bash
python3 tools/build_dctl.py        # regenerate dctl/*.dctl
python3 tests/run_tests.py         # verify
python3 tools/package_release.py   # build dist/Color-Space-Transform-mk2-vX.Y.Z.zip
```
To release, bump `VERSION`, update `CHANGELOG.md`, then `git tag vX.Y.Z && git push --tags`. GitHub Actions tests the release, builds the zip and publishes it.

## FAQ
**Does it work in the free version of Resolve?** No. DCTLs need Resolve Studio. The `.cube` in Extras works in the free version.

**It doesn't show up in the DCTL list.** Click *Update Lists* or restart Resolve. If you installed manually, check that the files are inside Resolve's LUT folder, not a folder next to it.

**Why not just use the stock CST?** It has no KineLog3 or Kinefinity Wide Gamut. Use this node for the camera-specific input, then the stock CST for tone mapping.

## License
[MIT](LICENSE). This project is not affiliated with Blackmagic Design, Kinefinity, DJI, ARRI, Sony, RED, Canon, Panasonic, Fujifilm or AMPAS. All trademarks belong to their owners.
