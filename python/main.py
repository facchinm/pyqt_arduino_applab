import ctypes
import glob
import os
import sys
import time

from arduino.app_utils import Bridge

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Populated by the x11-display brick (the only host dir mounted in this container is the app folder).
X11_DIR = os.path.join(APP_DIR, ".x11")


def preload_bundled_libs():
    pending = sorted(glob.glob(os.path.join(X11_DIR, "lib", "*.so*")))
    while pending:
        failed = []
        for path in pending:
            try:
                ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
            except OSError:
                failed.append(path)
        if len(failed) == len(pending):
            raise OSError(f"Cannot load bundled libs: {failed}")
        pending = failed


def setup_display():
    deadline = time.monotonic() + 30
    while not (sockets := glob.glob(os.path.join(X11_DIR, "X*[0-9]"))) and time.monotonic() < deadline:
        time.sleep(0.5)
    if sockets:
        name = os.path.basename(sockets[0])
        os.makedirs("/tmp/.X11-unix", exist_ok=True)
        link = os.path.join("/tmp/.X11-unix", name)
        if not os.path.lexists(link):
            os.symlink(sockets[0], link)
        os.environ["DISPLAY"] = ":" + name[1:]
        os.environ["XAUTHORITY"] = os.path.join(X11_DIR, "Xauthority")
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    elif not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "vnc:size=800x480:port=5900")


setup_display()
preload_bundled_libs()

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino UNO Q - PyQt Demo")
        self.resize(800, 480)
        self.led_on = False

        title = QLabel("PyQt + Arduino App Lab")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.led_button = QPushButton("Turn LED ON")
        self.led_button.setMinimumHeight(60)
        self.led_button.setStyleSheet("font-size: 20px;")
        self.led_button.clicked.connect(self.toggle_led)

        self.analog_label = QLabel("A0: --")
        self.analog_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.analog_label.setStyleSheet("font-size: 20px;")

        self.analog_bar = QProgressBar()
        self.analog_bar.setRange(0, 1023)

        self.status = QLabel("")
        self.status.setStyleSheet("color: gray;")

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.led_button)
        layout.addWidget(self.analog_label)
        layout.addWidget(self.analog_bar)
        layout.addStretch()
        layout.addWidget(self.status)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_analog)
        self.timer.start(500)

    def toggle_led(self):
        new_state = not self.led_on
        try:
            Bridge.call("set_led_state", new_state)
        except Exception as e:
            self.status.setText(f"LED call failed: {e}")
            return
        self.led_on = new_state
        self.led_button.setText("Turn LED OFF" if self.led_on else "Turn LED ON")
        self.status.setText(f"LED {'ON' if self.led_on else 'OFF'}")

    def poll_analog(self):
        try:
            value = int(Bridge.call("read_analog"))
        except Exception as e:
            self.status.setText(f"Analog read failed: {e}")
            return
        self.analog_label.setText(f"A0: {value}")
        self.analog_bar.setValue(value)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
