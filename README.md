# PyQt LED Control

Arduino App Lab sample (UNO Q) with a PyQt6 UI.

- **sketch/** (MCU): exposes `set_led_state` and `read_analog` over the Bridge.
- **python/** (Linux side): PyQt6 window with an LED toggle button and a live A0 reading.
- **bricks/x11-display/** (custom brick): sidecar container that relays the board's X
  display `:10` and copies the Qt system libs missing from the App Lab base image into
  `<app>/.x11`, the only host path the main container can see.

## Deploy

```sh
./deploy.sh
```

This pushes the app to `/home/arduino/ArduinoApps/pyqt-led-control` via `adb push`
and runs `arduino-app-cli app restart user:pyqt-led-control`.
Logs: `adb shell arduino-app-cli app logs --follow user:pyqt-led-control`.

## Viewing the UI

The window opens on the board's X display `:10` (change `X_DISPLAY` and the
healthcheck in `bricks/x11-display/brick_compose.yaml`, e.g. to `0` for the local screen).
If the relay socket doesn't appear within 30 s, Qt falls back to VNC on port 5900.
