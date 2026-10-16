#!/bin/bash
# Color Space Transform mk2 - macOS uninstaller.
DEST="/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Color Space Transform mk2"
if [ -d "$DEST" ]; then
  rm -rf "$DEST" 2>/dev/null || sudo rm -rf "$DEST"
  echo "Removed: $DEST"
else
  echo "Nothing to remove (not installed)."
fi
echo; read -r -p "Press Return to close this window." _
