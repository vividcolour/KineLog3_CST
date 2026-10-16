# Changelog

## v1.1.0
- **New camera entries** in both DCTLs. They're appended to the lists, so existing node settings are unchanged.
  - **Kinefinity BT.2020 - KineOS 8**: exact. It's for ProRes recorded in KineOS 8's BT.2020 gamut on MAVO Edge 6K / 8K and MAVO mark2.
  - **Kinefinity WG - Edge 8K - provisional** and **Kinefinity WG - Vista - provisional**: the curve is exact; the primaries are provisional until Kinefinity publishes them.
- **Color Remap mk2:** new sources Edge 8K, Vista and BT.2020 mode. The Edge 6K / MM2 LF source is relabelled.
- **New `docs/SPECIFICATION.md`:**
  - every formula, constant, color space and setting index, generated from the DCTL source table;
  - the camera support matrix;
  - DJI EI analysis for the X9-6K and X9-8K;
  - analysis of the Kinefinity spec v1 → v2 matrix correction;
  - the verification summary and open items.
- **Tests:** 109 checks, now including the new entries, every Remap source, and the v1-spec check.

## v1.0.0
First public release.

- **Color Space Transform mk2:** a Resolve-style Color Space Transform DCTL.
  - 18 color spaces and 20 transfer functions.
  - Adds Kinefinity KineLog3 / Kinefinity Wide Gamut and DJI D-Log / D-Gamut (Ronin 4D, Zenmuse X9).
  - White point adaptation: Bradford, CAT02 or none.
- **Color Remap mk2:** a one-node conversion from KineLog3 or D-Log.
  - Targets: ARRI LogC3 (EI 160–1600), ARRI LogC4, DaVinci Intermediate or KineLog3.
  - Modes: "Color + Gamma" or "Color only".
- **Extras:**
  - KineLog3 → LogC3 DCTL with a color-chart match tool;
  - 65³ `.cube` of the same transform.
- **Installers:** macOS and Windows (one double-click, with automatic admin elevation on Windows), plus Linux.
- **Test suite:** 90 checks against colour-science and manufacturer reference values, built as C++, C99 and OpenCL kernels.
