# PyQt LED Control

Arduino App Lab sample (UNO Q) with a PyQt6 UI.

- **sketch/** (MCU): exposes `set_led_state` and `read_analog` over the Bridge.
- **python/** (Linux side): PyQt6 window with an LED toggle button and a live A0 reading.

## Deploy

```sh
./deploy.sh
```

This pushes the app to `/home/arduino/ArduinoApps/pyqt-led-control` via `adb push`,
copies `libGL`/`libxkbcommon` (missing from the App Lab base image) from the board
into `python/lib`, and runs `arduino-app-cli app restart user:pyqt-led-control`.
Logs: `adb shell arduino-app-cli app logs --follow user:pyqt-led-control`.

## Viewing the UI

The App Lab Python container normally has no display, so Qt is started with the
VNC platform plugin on port 5900. Connect with any VNC client to `<board-ip>:5900`.

If `DISPLAY` or `WAYLAND_DISPLAY` is set (e.g. running on a desktop session with
display access), the window opens natively instead.
