#!/usr/bin/env bash
# Push the app to the board over adb and (re)start it.
set -euo pipefail

APP_NAME=pyqt-led-control
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST=/home/arduino/ArduinoApps/$APP_NAME

adb shell "mkdir -p $DEST"
adb push "$SRC_DIR/app.yaml" "$SRC_DIR/README.md" "$SRC_DIR/bricks" "$SRC_DIR/python" "$SRC_DIR/sketch" "$DEST/"

adb shell "arduino-app-cli app restart user:$APP_NAME"
