COLOR SPACE TRANSFORM mk2  -  v__VERSION__  (DCTL-only download, no scripts)
==========================================================================

Requires DaVinci Resolve STUDIO (the free version of Resolve cannot run DCTLs).
The .cube in Extras works in the free version.

INSTALL
1. In Resolve open Project Settings > Color Management > Lookup Tables and click
   "Open LUT Folder".
2. Drag "Color Space Transform mk2.dctl" and "Color Remap mk2.dctl" (and the Extras
   folder if you want it) into that folder.
3. Click "Update Lists" (or restart Resolve).

USE
On a Color page node: Effects > ResolveFX Color > DCTL, then pick the DCTL from the list.

  Color Space Transform mk2 - like the stock CST, with Kinefinity KineLog3 and DJI D-Log added.
                              Pure conversion: follow it with a stock CST for tone mapping.
  Color Remap mk2           - one node: Kinefinity / DJI footage -> ARRI LogC3 (any EI),
                              LogC4, DaVinci Intermediate or KineLog3.

Supported cameras, documentation and sources: https://github.com/vividcolour/KineLog3_CST
MIT licence (LICENSE.txt). Not affiliated with Blackmagic Design, Kinefinity, DJI, ARRI or
any other manufacturer; trademarks belong to their owners.
