import sys
import os
import serial
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QMovie, QFont


class SerialWorker(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, port="COM6", baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True
        self.ser = None

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        except Exception as e:
            print(f"Błąd otwarcia portu: {e}")

    def run(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode("utf-8").strip()
                    if line:
                        self.data_received.emit(line)
            except Exception as e:
                print(f"Błąd odczytu: {e}")
                self.running = False

    def send_data(self, data):
        """Wysyła dane do STM32"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(data.encode("utf-8"))
            except Exception as e:
                print(f"Błąd wysyłania: {e}")

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.wait()


class GardenApp(QWidget):
    def __init__(self):
        super().__init__()

        self.gif_sciezka = "plants.gif"
        self.main_font = QFont("Segoe UI", 11)

        self.setWindowTitle("Smart Garden")
        self.setMinimumSize(350, 480)
        self.setStyleSheet("background-color: #f1f8e9;")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(35, 35, 35, 35)
        self.layout.setSpacing(25)

        self.title_label = QLabel("GARDEN STATUS")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #558b2f; font-weight: 800; letter-spacing: 2px; font-size: 14px;")
        self.layout.addWidget(self.title_label)

        self.moisture_label = QLabel("Soil Moisture: --%")
        self.moisture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.moisture_label.setStyleSheet("""
            QLabel {
                font-size: 26px; 
                font-weight: 300; 
                color: #2e7d32; 
                background-color: #ffffff; 
                border-radius: 20px;
                padding: 20px;
                border: 1px solid #c8e6c9;
            }
        """)
        self.layout.addWidget(self.moisture_label)

        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(self.gif_sciezka):
            self.movie = QMovie(self.gif_sciezka)
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        else:
            self.gif_label.setText("🍃")
            self.gif_label.setStyleSheet("font-size: 50px;")
        self.layout.addWidget(self.gif_label)

        self.water_button = QPushButton("START WATERING")
        self.water_button.setFont(self.main_font)
        self.water_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.water_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 15px;
                border-radius: 25px;
                text-transform: uppercase;
            }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:pressed { background-color: #1b5e20; }
        """)
        self.water_button.clicked.connect(self.force_watering)
        self.layout.addWidget(self.water_button)

        self.setLayout(self.layout)

        self.serial_thread = SerialWorker(port="COM6", baudrate=115200)
        self.serial_thread.data_received.connect(self.update_moisture)
        self.serial_thread.start()

    def update_moisture(self, data):
        if "Error" in data:
            self.moisture_label.setText("Conn. Error")
        else:
            text = data if "%" in data else f"Soil Moisture: {data}%"
            self.moisture_label.setText(text)

    def force_watering(self):
        self.moisture_label.setText("Status: Watering...")
        self.moisture_label.setStyleSheet(self.moisture_label.styleSheet() + "color: #0288d1;")

        self.serial_thread.send_data("1")

    def closeEvent(self, event):
        self.serial_thread.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = GardenApp()
    window.show()
    sys.exit(app.exec())
