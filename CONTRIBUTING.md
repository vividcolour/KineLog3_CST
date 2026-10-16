# Contributing / building from source

## Layout
| Path | What |
|---|---|
| `dctl/` | The two DCTLs. **These are generated, so don't edit them by hand.** |
| `tools/build_dctl.py` | Source of truth: color-space and curve tables plus the DCTL templates. |
| `tools/build_spec.py`, `tools/SPECIFICATION.template.md` | Generate `docs/SPECIFICATION.md` from the same tables. |
| `tools/package_release.py` | Builds the release files into `dist/`. |
| `tests/` | Test suite and the harness that compiles DCTLs as C++, C99 and OpenCL. |
| `installers/` | macOS, Windows and Linux install / uninstall scripts and the in-zip read-me files. |
| `extras/kinelog3-to-logc3/` | KineLog3 → LogC3 DCTL, `.cube`, and the color-chart match tool. |

## Make a change
```bash
pip install -r tests/requirements.txt
python3 tools/build_dctl.py        # regenerate dctl/*.dctl
python3 tools/build_spec.py        # regenerate docs/SPECIFICATION.md
python3 tests/run_tests.py         # 109 checks: C++, C99 and OpenCL builds
python3 tools/package_release.py   # optional: build the release files into dist/
```
CI fails if `dctl/` or `docs/` isn't regenerated, or if any check fails.

To add a color space or curve, add a row to `GAMUTS` or `CURVES` in `tools/build_dctl.py`. **Always append** so saved Resolve node settings keep their menu indices. Then add its reference to `tests/run_tests.py`.

## Release
1. Bump `VERSION` and add a `CHANGELOG.md` entry, then push to `main`.
2. On GitHub, go to **Releases > Draft a new release**, create the tag `v<VERSION>` and publish it. Or push the tag with `git tag v<VERSION> && git push origin v<VERSION>`.
3. The **release** workflow then:
   * reruns the tests;
   * builds the DCTLs, both zips and `SHA256SUMS.txt`;
   * attaches them to the release.
