#!/bin/bash
# Color Space Transform mk2 - macOS installer.
# Double-click this file (first time: right-click > Open, or System Settings > Privacy & Security > Open Anyway).
cd "$(dirname "$0")" || exit 1
NAME="Color Space Transform mk2"
LUTROOT="/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"
DEST="$LUTROOT/$NAME"

pause() { echo; read -r -p "Press Return to close this window." _; }

echo "== $NAME installer =="
if [ ! -f "Color Space Transform mk2.dctl" ]; then
  echo "Can't find the .dctl files next to this installer."
  echo "Unzip the download first, then run the installer from the unzipped folder."
  pause; exit 1
fi
if [ ! -d "$LUTROOT" ]; then
  echo "DaVinci Resolve's LUT folder was not found:"
  echo "  $LUTROOT"
  echo "Install/open DaVinci Resolve once, or copy the .dctl files manually (see READ ME FIRST.txt)."
  pause; exit 1
fi

SUDO=""
if ! mkdir -p "$DEST/Extras" 2>/dev/null || [ ! -w "$DEST" ]; then
  echo "Administrator permission is needed to write to Resolve's LUT folder."
  SUDO="sudo"
fi
$SUDO mkdir -p "$DEST/Extras" &&
$SUDO cp -f "Color Space Transform mk2.dctl" "Color Remap mk2.dctl" "$DEST/" &&
$SUDO cp -f Extras/* "$DEST/Extras/" || { echo "Install failed."; pause; exit 1; }

echo
echo "Installed to: $DEST"
echo "In Resolve: Project Settings > Color Management > Lookup Tables > Update Lists (or restart Resolve)."
echo "Then add a ResolveFX 'DCTL' effect to a node and pick '$NAME/...' from the list."
pause
