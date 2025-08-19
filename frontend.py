import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QProgressBar, QMessageBox, QFrame, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

ESP32_IP = "192.168.4.1"
SCAN_INTERVAL = 10  # segundos

class Card(QFrame):
    def __init__(self, title, widget=None):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #23272e;
                border-radius: 12px;
                border: 1px solid #3f3f46;
                margin: 8px;
                padding: 16px;
            }
        """)
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("color: #00bfff; font-size: 17px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(label)
        if widget:
            layout.addWidget(widget)
        self.setLayout(layout)

class WiFiManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.esp32_ip = ESP32_IP
        self.connected = False
        self.local_ip = ""
        self.subnet_mask = "255.255.255.240"
        self.network_range = ""
        self.setWindowTitle("ESP32-S3 WiFi Manager")
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #181a20;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton {
                background-color: #00bfff;
                color: white;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
            QLineEdit {
                background-color: #23272e;
                border: 2px solid #3f3f46;
                border-radius: 8px;
                padding: 10px;
                color: #e0e0e0;
            }
            QTableWidget {
                background-color: #23272e;
                border-radius: 8px;
                color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #23272e;
                color: #00bfff;
                font-weight: bold;
                border: none;
                padding: 10px;
            }
            QGroupBox {
                border: 1px solid #3f3f46;
                border-radius: 10px;
                margin-top: 10px;
                font-size: 15px;
                color: #00bfff;
            }
        """)
        self.setup_ui()
        self.setup_timer()
        self.refresh_status()

    def setup_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: WiFi & connection
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # WiFi scan card
        self.wifi_table = QTableWidget(0, 3)
        self.wifi_table.setHorizontalHeaderLabels(["SSID", "Señal (dBm)", "Seguridad"])
        self.wifi_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.wifi_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.wifi_table.setAlternatingRowColors(True)
        self.wifi_table.setMaximumHeight(220)
        scan_btn = QPushButton("🔍 Escanear redes Wi-Fi")
        scan_btn.clicked.connect(self.scan_wifi)
        left_layout.addWidget(Card("Redes Wi-Fi Cercanas", self.wifi_table))
        left_layout.addWidget(scan_btn)

        # WiFi connect card
        connect_group = QGroupBox("Conectar a Red Wi-Fi")
        connect_layout = QHBoxLayout()
        self.ssid_entry = QLineEdit()
        self.ssid_entry.setPlaceholderText("SSID seleccionado...")
        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Contraseña")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        connect_btn = QPushButton("Conectar")
        connect_btn.clicked.connect(self.connect_wifi)
        connect_layout.addWidget(QLabel("SSID:"))
        connect_layout.addWidget(self.ssid_entry)
        connect_layout.addWidget(QLabel("Clave:"))
        connect_layout.addWidget(self.password_entry)
        connect_layout.addWidget(connect_btn)
        connect_group.setLayout(connect_layout)
        left_layout.addWidget(connect_group)

        # Connection status
        self.status_label = QLabel("Estado: Desconectado")
        self.status_label.setStyleSheet("font-size: 15px; margin-top: 10px; color: #00bfff;")
        left_layout.addWidget(self.status_label)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # Right panel: Info & devices
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Tabs for info/devices
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { background: #23272e; color: #00bfff; font-weight: bold; padding: 10px 24px; border-radius: 8px; } QTabBar::tab:selected { background: #00bfff; color: #23272e; }")

        # Tab 1: Info
        info_tab = QWidget()
        info_layout = QVBoxLayout()
        self.ip_info_label = QLabel("IP Local: --")
        self.subnet_label = QLabel("Subred: --")
        self.range_label = QLabel("Rango IP: --")
        info_layout.addWidget(Card("Información de Red", QWidget()))
        info_layout.itemAt(0).widget().layout().addWidget(self.ip_info_label)
        info_layout.itemAt(0).widget().layout().addWidget(self.subnet_label)
        info_layout.itemAt(0).widget().layout().addWidget(self.range_label)
        info_tab.setLayout(info_layout)
        tabs.addTab(info_tab, "🌐 Info Red")

        # Tab 2: Devices
        devices_tab = QWidget()
        devices_layout = QVBoxLayout()
        self.devices_table = QTableWidget(0, 3)
        self.devices_table.setHorizontalHeaderLabels(["IP", "MAC", "Hostname"])
        self.devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.devices_table.setAlternatingRowColors(True)
        devices_layout.addWidget(Card("Dispositivos Activos en la Subred", self.devices_table))
        
        # Botón para actualizar dispositivos
        update_devices_btn = QPushButton("Actualizar Dispositivos")
        update_devices_btn.setStyleSheet("margin-top: 10px;")
        update_devices_btn.clicked.connect(self.refresh_devices)
        devices_layout.addWidget(update_devices_btn)
        
        devices_tab.setLayout(devices_layout)
        tabs.addTab(devices_tab, "🖥️ Dispositivos")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        right_layout.addWidget(tabs)
        right_layout.addWidget(self.progress_bar)
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 700])

        main_layout.addWidget(splitter)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Table row select
        self.wifi_table.cellClicked.connect(self.on_wifi_row_selected)

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(SCAN_INTERVAL * 1000)

    def scan_wifi(self):
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        try:
            resp = requests.get(f"http://{self.esp32_ip}/scan", timeout=8)
            data = resp.json()
            networks = data.get("networks", [])
            self.wifi_table.setRowCount(len(networks))
            for i, net in enumerate(networks):
                ssid = net.get("ssid", "")
                rssi = net.get("rssi", "")
                encryption = net.get("encryption", "")
                self.wifi_table.setItem(i, 0, QTableWidgetItem(ssid))
                self.wifi_table.setItem(i, 1, QTableWidgetItem(str(rssi)))
                self.wifi_table.setItem(i, 2, QTableWidgetItem(encryption))
            self.status_label.setText(f"Escaneo completado: {len(networks)} redes encontradas")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo escanear redes Wi-Fi:\n{e}")
        self.progress_bar.hide()

    def on_wifi_row_selected(self, row, col):
        ssid_item = self.wifi_table.item(row, 0)
        if ssid_item:
            self.ssid_entry.setText(ssid_item.text())

    def connect_wifi(self):
        ssid = self.ssid_entry.text().strip()
        password = self.password_entry.text().strip()
        if not ssid:
            QMessageBox.warning(self, "Advertencia", "Seleccione o ingrese un SSID")
            return
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        try:
            resp = requests.post(f"http://{self.esp32_ip}/connect", data={"ssid": ssid, "password": password}, timeout=15)
            data = resp.json()
            if data.get("success"):
                self.connected = True
                self.status_label.setText(f"Conectado a {data.get('ssid', ssid)} ({data.get('ip', '')})")
                self.local_ip = data.get("ip", "")
                self.refresh_status()
            else:
                self.status_label.setText("Error al conectar")
                QMessageBox.critical(self, "Error", "No se pudo conectar a la red Wi-Fi")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de conexión:\n{e}")
        self.progress_bar.hide()

    def refresh_status(self):
        try:
            resp = requests.get(f"http://{self.esp32_ip}/status", timeout=5)
            data = resp.json()
            if data.get("connected"):
                self.connected = True
                self.local_ip = data.get("ip", "")
                self.status_label.setText(f"Conectado a {data.get('ssid', '')} ({self.local_ip})")
                self.ip_info_label.setText(f"IP Local: {self.local_ip}")
                self.subnet_label.setText(f"Subred: {self.subnet_mask}")
                self.calculate_network_range()
                self.range_label.setText(f"Rango IP: {self.network_range}")
                self.refresh_devices()
            else:
                self.connected = False
                self.status_label.setText("Desconectado")
                self.ip_info_label.setText("IP Local: --")
                self.range_label.setText("Rango IP: --")
                self.devices_table.setRowCount(0)
        except Exception:
            self.status_label.setText("ESP32 no accesible")
            self.ip_info_label.setText("IP Local: --")
            self.range_label.setText("Rango IP: --")
            self.devices_table.setRowCount(0)

    def calculate_network_range(self):
        # Calcula el rango de IPs de la subred /28
        try:
            ip_parts = list(map(int, self.local_ip.split(".")))
            mask_parts = list(map(int, self.subnet_mask.split(".")))
            ip_int = sum([ip_parts[i] << (8 * (3 - i)) for i in range(4)])
            mask_int = sum([mask_parts[i] << (8 * (3 - i)) for i in range(4)])
            network = ip_int & mask_int
            broadcast = network | (~mask_int & 0xFFFFFFFF)
            net_ip = ".".join(str((network >> (8 * i)) & 0xFF) for i in reversed(range(4)))
            broad_ip = ".".join(str((broadcast >> (8 * i)) & 0xFF) for i in reversed(range(4)))
            self.network_range = f"{net_ip} - {broad_ip}"
        except Exception:
            self.network_range = "--"

    def refresh_devices(self):
        try:
            resp = requests.get(f"http://{self.esp32_ip}/devices", timeout=8)
            data = resp.json()
            devices = data.get("devices", [])
            self.devices_table.setRowCount(len(devices))
            for i, dev in enumerate(devices):
                ip = dev.get("ip", "")
                mac = dev.get("mac", "")
                hostname = dev.get("hostname", "")
                self.devices_table.setItem(i, 0, QTableWidgetItem(ip))
                self.devices_table.setItem(i, 1, QTableWidgetItem(mac))
                self.devices_table.setItem(i, 2, QTableWidgetItem(hostname))
        except Exception:
            self.devices_table.setRowCount(0)

def main():
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 12)
    app.setFont(font)
    window = WiFiManagerUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
