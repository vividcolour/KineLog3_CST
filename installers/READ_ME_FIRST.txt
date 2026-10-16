COLOR SPACE TRANSFORM mk2  -  v__VERSION__
=====================================

A Color Space Transform for DaVinci Resolve that adds camera color spaces the stock
CST doesn't have, plus the usual ARRI, Sony, RED, Canon, Panasonic, Fujifilm,
Blackmagic, ACES and display spaces.

  Kinefinity KineLog3:  MAVO Edge 6K, MAVO mark2 LF, KineOS 8 BT.2020 mode (exact)
                        MAVO Edge 8K, Vista (curve exact; primaries provisional until
                        Kinefinity publishes them - see docs/SPECIFICATION.md on GitHub)
  DJI D-Log / D-Gamut:  Ronin 4D 6K & 8K, Zenmuse X9 (incl. Inspire 3), Zenmuse X7

Requires DaVinci Resolve STUDIO (the free version of Resolve cannot run DCTLs).
Works on macOS (Apple Silicon and Intel) and Windows, any GPU (Metal / CUDA / OpenCL).


INSTALL - THE EASY WAY
----------------------
1. Unzip this download.
2. macOS:   double-click  "install-macos.command"
            If macOS says it can't be opened: right-click it > Open > Open,
            or System Settings > Privacy & Security > "Open Anyway".
            You may be asked for your Mac password.
   Windows: double-click  "install-windows.bat"  and click Yes when Windows asks
            for administrator permission. (If SmartScreen appears: More info > Run anyway.)
3. In Resolve: Project Settings > Color Management > Lookup Tables > Update Lists
   (or just restart Resolve).


INSTALL - MANUALLY (any version of Resolve, any OS)
---------------------------------------------------
1. In Resolve open Project Settings > Color Management > Lookup Tables and click
   "Open LUT Folder".
2. Drag "Color Space Transform mk2.dctl" and "Color Remap mk2.dctl" (and the Extras
   folder if you want it) into that folder.
3. Click "Update Lists".


USE
---
On a Color page node: Effects > ResolveFX Color > DCTL, then choose
"Color Space Transform mk2" or "Color Remap mk2" in the DCTL List.
(Or right-click a node > LUT > Color Space Transform mk2 > ...)

Color Space Transform mk2  -  works like the stock CST: pick Input Color Space / Gamma
    and Output Color Space / Gamma. Pure conversion (no tone or gamut mapping), so for a
    display image follow it with a stock CST that does the tone mapping, e.g.
      [CST mk2: Kinefinity WG / KineLog3 -> DaVinci WG / DaVinci Intermediate]
      [stock CST: DaVinci WG / Intermediate -> Rec.709 / Gamma 2.4, Tone Mapping on]

Pick the entry that matches your camera, e.g. "Kinefinity WG - Edge 8K - provisional",
or "Kinefinity BT.2020 - KineOS 8" if you recorded ProRes in the BT.2020 gamut.

Color Remap mk2  -  one-click Kinefinity KineLog3 or DJI D-Log footage to
    ARRI LogC3 (any EI), ARRI LogC4, DaVinci Intermediate or KineLog3.
    "Color only" moves only the colors and keeps the original log curve.

Extras  -  KineLog3 -> LogC3 DCTL with an optional color-chart match, and a .cube LUT
    of the same transform for apps / Resolve versions that can't run DCTLs.


UNINSTALL
---------
Run "uninstall-macos.command" or "uninstall-windows.bat", or delete the
"Color Space Transform mk2" folder from Resolve's LUT folder.


Full documentation, sources and tests:  see the project's GitHub page.
MIT licence (see LICENSE.txt). Not affiliated with Blackmagic Design, Kinefinity,
DJI, ARRI or any other camera manufacturer; trademarks belong to their owners.
