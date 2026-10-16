#!/bin/bash
# Color Space Transform mk2 - Linux installer (DaVinci Resolve installed in /opt/resolve).
cd "$(dirname "$0")" || exit 1
DEST="${RESOLVE_LUT_DIR:-/opt/resolve/LUT}/Color Space Transform mk2"
sudo mkdir -p "$DEST/Extras" &&
sudo cp -f "Color Space Transform mk2.dctl" "Color Remap mk2.dctl" "$DEST/" &&
sudo cp -f Extras/* "$DEST/Extras/" && echo "Installed to: $DEST" && echo "Restart Resolve or Update Lists."
