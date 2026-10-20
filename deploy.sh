#!/usr/bin/env bash
# Push the app to the board and (re)start it. Uses adb, or ssh if BOARD=user@host is set.
set -euo pipefail

APP_NAME=pyqt-led-control
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST=/home/arduino/ArduinoApps/$APP_NAME
FILES=("$SRC_DIR/app.yaml" "$SRC_DIR/README.md" "$SRC_DIR/bricks" "$SRC_DIR/python" "$SRC_DIR/sketch")

if [[ -n "${BOARD:-}" ]]; then
  ssh "$BOARD" "mkdir -p $DEST"
  scp -rq "${FILES[@]}" "$BOARD:$DEST/"
  ssh "$BOARD" "arduino-app-cli app restart user:$APP_NAME"
else
  adb shell "mkdir -p $DEST"
  adb push "${FILES[@]}" "$DEST/"
  adb shell "arduino-app-cli app restart user:$APP_NAME"
fi
