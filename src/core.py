import sys
from typing import Callable
from requests import get

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

from ui.app_ui import Ui_MainWindow
from ui.app_ui_cam_widget import Ui_cam_widget

class CameraWidget(QWidget):
    def __init__(self, camera_ip : str, did : int = 1) -> None:
        super().__init__()
        self.ui = Ui_cam_widget()
        self.ui.setupUi(self)

        self.ip = camera_ip
        self.did = did

        self.is_online_timer = QTimer()
        self.online_flag = False

        self.led_status = False

        self._hook_buttons()
        self._config_name()
        self._create_media_player()
        self._config_online_check()

    def _hook_buttons(self):
        button_to_function : dict[QPushButton, Callable] = {
            self.ui.toggle_led : self._led_toggle,
            self.ui.move_up : lambda: self._send_command("ptzd"),
            self.ui.move_down : lambda: self._send_command("ptzu"),
            self.ui.move_left : lambda: self._send_command("ptzr"),
            self.ui.move_right : lambda: self._send_command("ptzl"),
            self.ui.move_up_left : lambda: self._send_command("ptzdr"),
            self.ui.move_up_right : lambda: self._send_command("ptzdl"),
            self.ui.move_down_left : lambda: self._send_command("ptzur"),
            self.ui.move_down_right : lambda: self._send_command("ptul")
        }

        for btn, func in button_to_function.items():
            btn.clicked.connect(func)        

    def _led_toggle(self):
        if self.led_status:
            self._send_command("ledoff")
            self.led_status = False
        else:
            self._send_command("ledon")
            self.led_status = True

    def _send_command(self, cmd : str):
        response = get(f"http://{self.ip}:8080/cgi-bin/webui?command={cmd}")

    def _config_name(self):
        online = "Online" if self.online_flag else "Offline"
        name = f"CAM{self.did} - {self.ip} - {online}"
        self.ui.cam_id.setText(name)

    def _create_media_player(self):
        self.video_widget = QVideoWidget(self.ui.display_frame)
        self.video_widget.resize(self.ui.display_frame.size())
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)

        self.media_player = QMediaPlayer(self.ui.display_frame)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setSource(QUrl(f"rtsp://{self.ip}/vs0"))
        self.media_player.play()

    def _config_online_check(self):
        self.is_online_timer.setInterval(2000)
        self.is_online_timer.timeout.connect(self._online_check_function)
        self.is_online_timer.start()

    def _online_check_function(self):
        self.online_flag = self.media_player.isPlaying()
        self._config_name()


class CoreUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.diag = None
        self.cameras : list[CameraWidget] = []

        self.hook_buttons()

    def add_new_device(self):
        ip = self.ui.cam_ip.text()

        for cam in self.cameras:
            if cam.ip == ip:
                return

        did = len(self.cameras) + 1
        camera = CameraWidget(ip, did)
        self.cameras.append(camera)
        self.ui.main_layout.addWidget(camera)

    def hook_buttons(self):
        button_to_function : dict[QPushButton, Callable] = {
            self.ui.add_cam : self.add_new_device
        }

        for btn, func in button_to_function.items():
            btn.clicked.connect(func)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoreUI()
    window.show()
    sys.exit(app.exec())
