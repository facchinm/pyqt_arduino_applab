#!/usr/bin/env bash
# Push the app to the board over adb and (re)start it.
set -euo pipefail

APP_NAME=pyqt-led-control
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST=/home/arduino/ArduinoApps/$APP_NAME
# Host X display to draw on (:10 = arduino's xrdp session, :0 = local screen). Empty = VNC.
X_DISPLAY=${X_DISPLAY-10}

HOST_LIBS="libGLdispatch.so.0 libGLX.so.0 libGL.so.1 libxkbcommon.so.0 libxkbcommon-x11.so.0
  libxcb-cursor.so.0 libxcb-icccm.so.4 libxcb-image.so.0 libxcb-keysyms.so.1 libxcb-render-util.so.0
  libxcb-shape.so.0 libxcb-xkb.so.1 libxcb-util.so.1 libSM.so.6 libICE.so.6"

adb shell "mkdir -p $DEST"
adb push "$SRC_DIR/app.yaml" "$SRC_DIR/README.md" "$SRC_DIR/python" "$SRC_DIR/sketch" "$DEST/"

adb shell "mkdir -p $DEST/python/lib && cd /usr/lib/aarch64-linux-gnu && cp -L $(echo $HOST_LIBS) $DEST/python/lib/"

adb shell "pkill -f '[s]ocat UNIX-LISTEN:$DEST/.x11' ; rm -rf $DEST/.x11"
if [[ -n "$X_DISPLAY" ]]; then
  # Wildcard the cookie's host family so it matches the container's hostname.
  adb shell "mkdir -m 700 $DEST/.x11 && \
    xauth -f ~/.Xauthority nlist :$X_DISPLAY | sed 's/^..../ffff/' | xauth -f $DEST/.x11/Xauthority nmerge - && \
    setsid nohup socat UNIX-LISTEN:$DEST/.x11/X$X_DISPLAY,fork UNIX-CONNECT:/tmp/.X11-unix/X$X_DISPLAY >/dev/null 2>&1 < /dev/null &"
fi

adb shell "arduino-app-cli app restart user:$APP_NAME"
