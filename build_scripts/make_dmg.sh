#!/bin/bash
# Build an unsigned drag-to-Applications .dmg from dist/PikaXPS.app
set -e
cd "$(dirname "$0")/.."

APP="dist/PikaXPS.app"
DMG="dist/PikaXPS-macOS.dmg"
[ -d "$APP" ] || { echo "missing $APP — build the app first"; exit 1; }

STAGE="$(mktemp -d)"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

rm -f "$DMG"
hdiutil create -volname "PikaXPS" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$STAGE"
echo "built $DMG"
du -h "$DMG"
