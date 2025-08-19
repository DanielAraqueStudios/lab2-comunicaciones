import sys
import requests
import json
import threading
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                            QLineEdit, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QGroupBox, QCheckBox, QTextEdit,
                            QProgressBar, QMessageBox, QFrame, QSplitter,
                            QTabWidget, QComboBox, QSpinBox, QSystemTrayIcon,
                            QMenu, QStatusBar)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter, QAction

class NetworkScannerThread(QThread):
    """Hilo para operaciones de red en segundo plano"""
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, esp32_ip, operation, data=None):
        super().__init__()
        self.esp32_ip = esp32_ip
        self.operation = operation
        self.data = data
        self.running = True
    
    def run(self):
        try:
            if self.operation == "scan_wifi":
                response = requests.get(f"http://{self.esp32_ip}/scan", timeout=10)
            elif self.operation == "connect":
                response = requests.post(f"http://{self.esp32_ip}/connect", 
                                       data=self.data, timeout=30)
            elif self.operation == "status":
                response = requests.get(f"http://{self.esp32_ip}/status", timeout=5)
            elif self.operation == "devices":
                response = requests.get(f"http://{self.esp32_ip}/devices", timeout=10)
            elif self.operation == "disconnect":
                response = requests.post(f"http://{self.esp32_ip}/disconnect", timeout=10)
            
            if response.status_code == 200:
                self.data_updated.emit(response.json())
            else:
                self.error_occurred.emit(f"Error del servidor: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Error de conexión: {str(e)}")
    
    def stop(self):
        self.running = False

class ModernCard(QFrame):
    """Widget de tarjeta moderna con sombra y efectos"""
    def __init__(self, title="", content_widget=None):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ModernCard {
                background-color: #2d2d30;
                border: 1px solid #3f3f46;
                border-radius: 12px;
                margin: 8px;
                padding: 16px;
            }
            ModernCard:hover {
                border: 1px solid #007acc;
                background-color: #323237;
            }
        """)
        
        layout = QVBoxLayout()
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 12px;
                    padding: 0px;
                }
            """)
            layout.addWidget(title_label)
        
        if content_widget:
            layout.addWidget(content_widget)
        
        self.setLayout(layout)

class StatusIndicator(QLabel):
    """Indicador de estado con colores dinámicos"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 16)
        self.set_status("disconnected")
    
    def set_status(self, status):
        colors = {
            "connected": "#4CAF50",
            "connecting": "#FF9800", 
            "disconnected": "#F44336",
            "error": "#9C27B0"
        }
        
        color = colors.get(status, "#757575")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 8px;
                border: 2px solid {color}40;
            }}
        """)

class WiFiManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.esp32_ip = "192.168.4.1"
        self.connected = False
        self.auto_refresh = True
        self.refresh_interval = 10
        
        # Configurar la aplicación
        self.setWindowTitle("🛡️ ESP32-S3 WiFi Manager Pro")
        self.setGeometry(100, 100, 1400, 900)
        
        # Aplicar tema oscuro
        self.apply_dark_theme()
        
        # Configurar interfaz
        self.setup_ui()
        
        # Configurar timers
        self.setup_timers()
        
        # Estado inicial
        self.update_status()
    
    def apply_dark_theme(self):
        """Aplicar tema oscuro moderno"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            
            QPushButton {import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import threading
import time
from datetime import datetime
import ipaddress

class WiFiManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-S3 WiFi Manager & Network Scanner")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Variables
        self.esp32_ip = "192.168.4.1"  # IP del punto de acceso del ESP32
        self.connected = False
        self.auto_refresh = True
        self.refresh_interval = 10  # segundos
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear interfaz
        self.create_widgets()
        
        # Iniciar actualizaciones automáticas
        self.start_auto_refresh()
    
    def setup_styles(self):
        """Configurar estilos modernos para la interfaz"""
        self.style = ttk.Style()
        
        # Configurar tema oscuro personalizado
        self.style.theme_use('clam')
        
        # Colores
        bg_color = '#2c3e50'
        fg_color = '#ecf0f1'
        accent_color = '#3498db'
        success_color = '#27ae60'
        warning_color = '#f39c12'
        danger_color = '#e74c3c'
        
        # Configurar estilos
        self.style.configure('Title.TLabel', 
                           background=bg_color, 
                           foreground=fg_color,
                           font=('Arial', 16, 'bold'))
        
        self.style.configure('Subtitle.TLabel',
                           background=bg_color,
                           foreground=accent_color,
                           font=('Arial', 12, 'bold'))
        
        self.style.configure('Info.TLabel',
                           background=bg_color,
                           foreground=fg_color,
                           font=('Arial', 10))
        
        self.style.configure('Success.TLabel',
                           background=bg_color,
                           foreground=success_color,
                           font=('Arial', 10, 'bold'))
        
        self.style.configure('Warning.TLabel',
                           background=bg_color,
                           foreground=warning_color,
                           font=('Arial', 10, 'bold'))
        
        self.style.configure('Custom.TButton',
                           background=accent_color,
                           foreground='white',
                           font=('Arial', 10, 'bold'),
                           padding=10)
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal con scroll
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título principal
        title_label = ttk.Label(main_frame, 
                               text="🛡️ ESP32-S3 WiFi Manager & Network Scanner", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Frame para configuración de ESP32
        config_frame = self.create_config_section(main_frame)
        config_frame.pack(fill='x', pady=(0, 20))
        
        # Frame para redes WiFi
        wifi_frame = self.create_wifi_section(main_frame)
        wifi_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Frame para dispositivos de red
        devices_frame = self.create_devices_section(main_frame)
        devices_frame.pack(fill='both', expand=True)
    
    def create_config_section(self, parent):
        """Crear sección de configuración del ESP32"""
        frame = tk.LabelFrame(parent, text="Configuración ESP32", 
                             bg='#34495e', fg='#ecf0f1', 
                             font=('Arial', 12, 'bold'), padx=10, pady=10)
        
        # IP del ESP32
        ip_frame = tk.Frame(frame, bg='#34495e')
        ip_frame.pack(fill='x', pady=5)
        
        tk.Label(ip_frame, text="IP del ESP32:", 
                bg='#34495e', fg='#ecf0f1', font=('Arial', 10)).pack(side='left')
        
        self.ip_entry = tk.Entry(ip_frame, font=('Arial', 10), width=15)
        self.ip_entry.insert(0, self.esp32_ip)
        self.ip_entry.pack(side='left', padx=(10, 0))
        
        # Botón para actualizar IP
        update_ip_btn = tk.Button(ip_frame, text="Actualizar IP",
                                 bg='#3498db', fg='white', font=('Arial', 9, 'bold'),
                                 command=self.update_esp32_ip)
        update_ip_btn.pack(side='left', padx=(10, 0))
        
        # Estado de conexión
        self.connection_status = tk.Label(frame, text="Estado: Desconectado",
                                         bg='#34495e', fg='#e74c3c', 
                                         font=('Arial', 10, 'bold'))
        self.connection_status.pack(pady=5)
        
        return frame
    
    def create_wifi_section(self, parent):
        """Crear sección de redes WiFi"""
        frame = tk.LabelFrame(parent, text="Redes WiFi Disponibles", 
                             bg='#34495e', fg='#ecf0f1', 
                             font=('Arial', 12, 'bold'), padx=10, pady=10)
        
        # Botones de control
        control_frame = tk.Frame(frame, bg='#34495e')
        control_frame.pack(fill='x', pady=(0, 10))
        
        scan_btn = tk.Button(control_frame, text="🔍 Escanear Redes",
                            bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                            command=self.scan_wifi_networks)
        scan_btn.pack(side='left', padx=(0, 10))
        
        refresh_btn = tk.Button(control_frame, text="🔄 Actualizar",
                               bg='#f39c12', fg='white', font=('Arial', 10, 'bold'),
                               command=self.refresh_all_data)
        refresh_btn.pack(side='left', padx=(0, 10))
        
        disconnect_btn = tk.Button(control_frame, text="🔌 Desconectar",
                                  bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
                                  command=self.disconnect_wifi)
        disconnect_btn.pack(side='left')
        
        # Lista de redes WiFi
        columns = ('SSID', 'Señal (dBm)', 'Seguridad', 'Canal')
        self.wifi_tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
        
        # Configurar encabezados
        for col in columns:
            self.wifi_tree.heading(col, text=col)
            self.wifi_tree.column(col, width=150)
        
        # Scrollbar para la lista
        wifi_scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.wifi_tree.yview)
        self.wifi_tree.configure(yscrollcommand=wifi_scrollbar.set)
        
        # Empaquetar Treeview y scrollbar
        tree_frame = tk.Frame(frame, bg='#34495e')
        tree_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.wifi_tree.pack(side='left', fill='both', expand=True)
        wifi_scrollbar.pack(side='right', fill='y')
        
        # Bind para doble clic
        self.wifi_tree.bind('<Double-1>', self.on_wifi_select)
        
        # Frame para conexión
        connect_frame = tk.Frame(frame, bg='#34495e')
        connect_frame.pack(fill='x')
        
        tk.Label(connect_frame, text="Contraseña:", 
                bg='#34495e', fg='#ecf0f1', font=('Arial', 10)).pack(side='left')
        
        self.password_entry = tk.Entry(connect_frame, font=('Arial', 10), 
                                      width=20, show='*')
        self.password_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        
        connect_btn = tk.Button(connect_frame, text="Conectar",
                               bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                               command=self.connect_to_wifi)
        connect_btn.pack(side='right', padx=(10, 0))
        
        return frame
    
    def create_devices_section(self, parent):
        """Crear sección de dispositivos de red"""
        frame = tk.LabelFrame(parent, text="Dispositivos en la Red", 
                             bg='#34495e', fg='#ecf0f1', 
                             font=('Arial', 12, 'bold'), padx=10, pady=10)
        
        # Información de red
        self.network_info = tk.Label(frame, text="Red: No conectado",
                                    bg='#34495e', fg='#95a5a6', 
                                    font=('Arial', 10))
        self.network_info.pack(pady=(0, 10))
        
        # Lista de dispositivos
        device_columns = ('IP', 'Tipo', 'MAC', 'Estado', 'Última conexión')
        self.devices_tree = ttk.Treeview(frame, columns=device_columns, 
                                        show='headings', height=10)
        
        # Configurar encabezados
        for col in device_columns:
            self.devices_tree.heading(col, text=col)
            self.devices_tree.column(col, width=120)
        
        # Scrollbar para dispositivos
        devices_scrollbar = ttk.Scrollbar(frame, orient='vertical', 
                                         command=self.devices_tree.yview)
        self.devices_tree.configure(yscrollcommand=devices_scrollbar.set)
        
        # Frame para dispositivos
        devices_tree_frame = tk.Frame(frame, bg='#34495e')
        devices_tree_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.devices_tree.pack(side='left', fill='both', expand=True)
        devices_scrollbar.pack(side='right', fill='y')
        
        # Estadísticas
        self.stats_label = tk.Label(frame, text="Dispositivos encontrados: 0",
                                   bg='#34495e', fg='#3498db', 
                                   font=('Arial', 10, 'bold'))
        self.stats_label.pack()
        
        # Auto-refresh control
        refresh_control_frame = tk.Frame(frame, bg='#34495e')
        refresh_control_frame.pack(fill='x', pady=(10, 0))
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = tk.Checkbutton(refresh_control_frame, 
                                           text="Actualización automática (10s)",
                                           variable=self.auto_refresh_var,
                                           bg='#34495e', fg='#ecf0f1',
                                           selectcolor='#2c3e50',
                                           font=('Arial', 9),
                                           command=self.toggle_auto_refresh)
        auto_refresh_check.pack(side='left')
        
        self.last_update_label = tk.Label(refresh_control_frame, 
                                         text="Última actualización: --",
                                         bg='#34495e', fg='#95a5a6', 
                                         font=('Arial', 9))
        self.last_update_label.pack(side='right')
        
        return frame
    
    def update_esp32_ip(self):
        """Actualizar la IP del ESP32"""
        new_ip = self.ip_entry.get().strip()
        if new_ip:
            self.esp32_ip = new_ip
            self.refresh_all_data()
    
    def scan_wifi_networks(self):
        """Escanear redes WiFi disponibles"""
        try:
            response = requests.get(f"http://{self.esp32_ip}/scan", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.populate_wifi_list(data['networks'])
            else:
                messagebox.showerror("Error", f"Error del servidor: {response.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error de Conexión", 
                               f"No se pudo conectar al ESP32:\n{str(e)}")
    
    def populate_wifi_list(self, networks):
        """Poblar la lista de redes WiFi"""
        # Limpiar lista existente
        for item in self.wifi_tree.get_children():
            self.wifi_tree.delete(item)
        
        # Agregar redes
        for network in networks:
            signal_strength = network['rssi']
            signal_quality = "Excelente" if signal_strength > -50 else \
                            "Buena" if signal_strength > -60 else \
                            "Regular" if signal_strength > -70 else "Débil"
            
            self.wifi_tree.insert('', 'end', values=(
                network['ssid'],
                f"{signal_strength} dBm ({signal_quality})",
                network['encryption'],
                network.get('channel', 'N/A')
            ))
    
    def on_wifi_select(self, event):
        """Manejar selección de red WiFi"""
        selection = self.wifi_tree.selection()
        if selection:
            item = self.wifi_tree.item(selection[0])
            ssid = item['values'][0]
            # Autocompletar SSID si es necesario
            print(f"Red seleccionada: {ssid}")
    
    def connect_to_wifi(self):
        """Conectar a la red WiFi seleccionada"""
        selection = self.wifi_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una red WiFi")
            return
        
        item = self.wifi_tree.item(selection[0])
        ssid = item['values'][0]
        password = self.password_entry.get()
        
        if not password and "Secured" in item['values'][2]:
            messagebox.showwarning("Advertencia", "Ingrese la contraseña para la red")
            return
        
        try:
            # Mostrar progreso
            self.connection_status.config(text="Estado: Conectando...", fg='#f39c12')
            self.root.update()
            
            data = {'ssid': ssid, 'password': password}
            response = requests.post(f"http://{self.esp32_ip}/connect", 
                                   data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    self.connected = True
                    self.connection_status.config(
                        text=f"Estado: Conectado a {result['ssid']} ({result['ip']})", 
                        fg='#27ae60')
                    messagebox.showinfo("Éxito", 
                                      f"Conectado exitosamente a {ssid}\nIP: {result['ip']}")
                    self.password_entry.delete(0, tk.END)
                    self.refresh_devices()
                else:
                    self.connection_status.config(text="Estado: Error de conexión", fg='#e74c3c')
                    messagebox.showerror("Error", "No se pudo conectar a la red")
            else:
                self.connection_status.config(text="Estado: Error", fg='#e74c3c')
                messagebox.showerror("Error", f"Error del servidor: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.connection_status.config(text="Estado: Error de comunicación", fg='#e74c3c')
            messagebox.showerror("Error de Conexión", 
                               f"Error de comunicación con ESP32:\n{str(e)}")
    
    def disconnect_wifi(self):
        """Desconectar de la red WiFi"""
        try:
            response = requests.post(f"http://{self.esp32_ip}/disconnect", timeout=10)
            if response.status_code == 200:
                self.connected = False
                self.connection_status.config(text="Estado: Desconectado", fg='#e74c3c')
                
                # Limpiar lista de dispositivos
                for item in self.devices_tree.get_children():
                    self.devices_tree.delete(item)
                
                self.network_info.config(text="Red: No conectado")
                self.stats_label.config(text="Dispositivos encontrados: 0")
                
                messagebox.showinfo("Info", "Desconectado de la red WiFi")
            else:
                messagebox.showerror("Error", f"Error del servidor: {response.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Error de comunicación: {str(e)}")
    
    def refresh_devices(self):
        """Actualizar lista de dispositivos"""
        try:
            response = requests.get(f"http://{self.esp32_ip}/devices", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.populate_devices_list(data)
                self.update_network_info(data.get('networkInfo', {}))
            else:
                print(f"Error al obtener dispositivos: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al obtener dispositivos: {e}")
    
    def populate_devices_list(self, data):
        """Poblar lista de dispositivos"""
        # Limpiar lista existente
        for item in self.devices_tree.get_children():
            self.devices_tree.delete(item)
        
        devices = data.get('devices', [])
        
        for device in devices:
            device_type = device.get('type', 'Unknown')
            status = "🟢 Activo" if device.get('active', False) else "🔴 Inactivo"
            
            # Formatear última conexión
            last_seen = device.get('lastSeen')
            if last_seen:
                last_seen_str = datetime.fromtimestamp(last_seen/1000).strftime('%H:%M:%S')
            else:
                last_seen_str = "N/A"
            
            self.devices_tree.insert('', 'end', values=(
                device.get('ip', 'N/A'),
                device_type,
                device.get('mac', 'Unknown'),
                status,
                last_seen_str
            ))
        
        # Actualizar estadísticas
        self.stats_label.config(text=f"Dispositivos encontrados: {len(devices)}")
        
        # Actualizar timestamp
        now = datetime.now().strftime('%H:%M:%S')
        self.last_update_label.config(text=f"Última actualización: {now}")
    
    def update_network_info(self, network_info):
        """Actualizar información de la red"""
        if network_info:
            subnet = network_info.get('subnet', 'N/A')
            network = network_info.get('network', 'N/A')
            broadcast = network_info.get('broadcast', 'N/A')
            gateway = network_info.get('gateway', 'N/A')
            
            info_text = f"Red: {network}/{subnet} | Gateway: {gateway} | Rango: {network} - {broadcast}"
            self.network_info.config(text=info_text)
    
    def refresh_all_data(self):
        """Actualizar todos los datos"""
        self.check_connection_status()
        if self.connected:
            self.refresh_devices()
    
    def check_connection_status(self):
        """Verificar estado de conexión"""
        try:
            response = requests.get(f"http://{self.esp32_ip}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('connected', False):
                    self.connected = True
                    ssid = data.get('ssid', 'Unknown')
                    ip = data.get('ip', 'Unknown')
                    rssi = data.get('rssi', 0)
                    
                    signal_quality = "Excelente" if rssi > -50 else \
                                    "Buena" if rssi > -60 else \
                                    "Regular" if rssi > -70 else "Débil"
                    
                    status_text = f"Conectado a {ssid} ({ip}) - Señal: {signal_quality}"
                    self.connection_status.config(text=f"Estado: {status_text}", fg='#27ae60')
                else:
                    self.connected = False
                    self.connection_status.config(text="Estado: Desconectado", fg='#e74c3c')
            else:
                self.connection_status.config(text="Estado: Error de comunicación", fg='#e74c3c')
        except requests.exceptions.RequestException:
            self.connection_status.config(text="Estado: ESP32 no accesible", fg='#e74c3c')
    
    def toggle_auto_refresh(self):
        """Activar/desactivar actualización automática"""
        self.auto_refresh = self.auto_refresh_var.get()
    
    def start_auto_refresh(self):
        """Iniciar el hilo de actualización automática"""
        def auto_refresh_thread():
            while True:
                if self.auto_refresh:
                    try:
                        self.refresh_all_data()
                    except:
                        pass  # Ignorar errores en el hilo de fondo
                time.sleep(self.refresh_interval)
        
        # Iniciar hilo daemon
        refresh_thread = threading.Thread(target=auto_refresh_thread, daemon=True)
        refresh_thread.start()

def main():
    """Función principal"""
    root = tk.Tk()
    app = WiFiManagerGUI(root)
    
    # Configurar el cierre de la aplicación
    def on_closing():
        app.auto_refresh = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Mostrar instrucciones iniciales
    messagebox.showinfo("Instrucciones de Uso", 
                       """ESP32-S3 WiFi Manager - Instrucciones:

1. Asegúrate de que el ESP32-S3 esté encendido y ejecutando el código
2. Conecta tu PC a la red WiFi 'ESP32-WiFiConfig' (contraseña: 12345678)
3. La IP por defecto es 192.168.4.1
4. Haz clic en 'Escanear Redes' para ver redes disponibles
5. Selecciona una red, ingresa la contraseña y conecta
6. Una vez conectado, verás los dispositivos en la red automáticamente

Características:
- Escaneo automático de dispositivos cada 10 segundos
- Detección de rango de red con máscara /28 (255.255.255.240)
- Interfaz moderna con indicadores visuales de estado""")
    
    root.mainloop()

if __name__ == "__main__":
    main()
                background-color: #0d7377;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 11px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #14a085;
            }
            
            QPushButton:pressed {
                background-color: #0a5d61;
            }
            
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
            
            QPushButton.primary {
                background-color: #007acc;
            }
            
            QPushButton.primary:hover {
                background-color: #1e88e5;
            }
            
            QPushButton.success {
                background-color: #4caf50;
            }
            
            QPushButton.success:hover {
                background-color: #66bb6a;
            }
            
            QPushButton.warning {
                background-color: #ff9800;
            }
            
            QPushButton.warning:hover {
                background-color: #ffb74d;
            }
            
            QPushButton.danger {
                background-color: #f44336;
            }
            
            QPushButton.danger:hover {
                background-color: #ef5350;
            }
            
            QLineEdit {
                background-color: #2d2d30;
                border: 2px solid #3f3f46;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: #ffffff;
            }
            
            QLineEdit:focus {
                border-color: #007acc;
                background-color: #323237;
            }
            
            QTableWidget {
                background-color: #2d2d30;
                alternate-background-color: #323237;
                selection-background-color: #007acc;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                gridline-color: #3f3f46;
            }
            
            QTableWidget::item {
                padding: 12px;
                border: none;
            }
            
            QTableWidget::item:selected {
                background-color: #007acc;
            }
            
            QHeaderView::section {
                background-color: #252526;
                color: #ffffff;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #007acc;
                font-weight: bold;
            }
            
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #ffffff;
                border: 2px solid #3f3f46;
                border-radius: 12px;
                margin-top: 20px;
                padding-top: 20px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px 0 8px;
                color: #007acc;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #3f3f46;
                background-color: #2d2d30;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border-color: #007acc;
            }
            
            QTabWidget::pane {
                border: 1px solid #3f3f46;
                border-radius: 8px;
                background-color: #2d2d30;
            }
            
            QTabBar::tab {
                background-color: #252526;
                color: #ffffff;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            
            QTabBar::tab:selected {
                background-color: #007acc;
            }
            
            QTabBar::tab:hover {
                background-color: #323237;
            }
            
            QProgressBar {
                border: 2px solid #3f3f46;
                border-radius: 8px;
                background-color: #2d2d30;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 6px;
            }
            
            QStatusBar {
                background-color: #252526;
                color: #ffffff;
                border-top: 1px solid #3f3f46;
            }
            
            QTextEdit {
                background-color: #2d2d30;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
            }
        """)
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal con splitter
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo - Control
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # Panel derecho - Monitoreo
        right_panel = self.create_monitoring_panel()
        splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([600, 800])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # Configurar barra de estado
        self.setup_status_bar()
    
    def create_control_panel(self):
        """Crear panel de control izquierdo"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Título con estado
        header_layout = QHBoxLayout()
        title = QLabel("🛡️ Control Panel")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #007acc; margin-bottom: 20px;")
        
        self.status_indicator = StatusIndicator()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        
        layout.addLayout(header_layout)
        
        # Configuración ESP32
        esp32_card = self.create_esp32_config_card()
        layout.addWidget(esp32_card)
        
        # Redes WiFi
        wifi_card = self.create_wifi_card()
        layout.addWidget(wifi_card)
        
        # Configuraciones avanzadas
        settings_card = self.create_settings_card()
        layout.addWidget(settings_card)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_esp32_config_card(self):
        """Crear tarjeta de configuración ESP32"""
        content = QWidget()
        layout = QVBoxLayout()
        
        # IP Configuration
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("ESP32 IP:"))
        self.ip_entry = QLineEdit(self.esp32_ip)
        self.ip_entry.setPlaceholderText("192.168.4.1")
        ip_layout.addWidget(self.ip_entry)
        
        update_ip_btn = QPushButton("🔄 Actualizar")
        update_ip_btn.setProperty("class", "primary")
        update_ip_btn.clicked.connect(self.update_esp32_ip)
        ip_layout.addWidget(update_ip_btn)
        
        layout.addLayout(ip_layout)
        
        # Estado de conexión
        self.connection_label = QLabel("Estado: Verificando...")
        self.connection_label.setStyleSheet("font-size: 13px; margin: 8px 0px; padding: 8px; background-color: #323237; border-radius: 6px;")
        layout.addWidget(self.connection_label)
        
        # Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        content.setLayout(layout)
        return ModernCard("⚙️ Configuración ESP32", content)
    
    def create_wifi_card(self):
        """Crear tarjeta de WiFi"""
        content = QWidget()
        layout = QVBoxLayout()
        
        # Botones de control WiFi
        buttons_layout = QHBoxLayout()
        
        scan_btn = QPushButton("🔍 Escanear")
        scan_btn.setProperty("class", "success")
        scan_btn.clicked.connect(self.scan_wifi_networks)
        buttons_layout.addWidget(scan_btn)
        
        disconnect_btn = QPushButton("🔌 Desconectar")
        disconnect_btn.setProperty("class", "danger")
        disconnect_btn.clicked.connect(self.disconnect_wifi)
        buttons_layout.addWidget(disconnect_btn)
        
        layout.addLayout(buttons_layout)
        
        # Tabla de redes WiFi
        self.wifi_table = QTableWidget()
        self.wifi_table.setColumnCount(4)
        self.wifi_table.setHorizontalHeaderLabels(["SSID", "Señal", "Seguridad", "Canal"])
        
        # Configurar tabla
        header = self.wifi_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.wifi_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.wifi_table.setAlternatingRowColors(True)
        self.wifi_table.cellDoubleClicked.connect(self.on_wifi_double_click)
        
        layout.addWidget(self.wifi_table)
        
        # Conexión
        connect_layout = QVBoxLayout()
        
        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Contraseña de la red WiFi...")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        connect_layout.addWidget(self.password_entry)
        
        connect_btn = QPushButton("🔗 Conectar a Red Seleccionada")
        connect_btn.setProperty("class", "primary")
        connect_btn.clicked.connect(self.connect_to_wifi)
        connect_layout.addWidget(connect_btn)
        
        layout.addLayout(connect_layout)
        
        content.setLayout(layout)
        return ModernCard("📶 Redes WiFi", content)
    
    def create_settings_card(self):
        """Crear tarjeta de configuraciones"""
        content = QWidget()
        layout = QVBoxLayout()
        
        # Auto refresh
        self.auto_refresh_checkbox = QCheckBox("Actualización automática")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.toggled.connect(self.toggle_auto_refresh)
        layout.addWidget(self.auto_refresh_checkbox)
        
        # Interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervalo (seg):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(5, 60)
        self.interval_spinbox.setValue(10)
        self.interval_spinbox.valueChanged.connect(self.update_refresh_interval)
        interval_layout.addWidget(self.interval_spinbox)
        layout.addLayout(interval_layout)
        
        content.setLayout(layout)
        return ModernCard("⚙️ Configuraciones", content)
    
    def create_monitoring_panel(self):
        """Crear panel de monitoreo derecho"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("📊 Network Monitoring")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #007acc; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Tabs para diferentes vistas
        tabs = QTabWidget()
        
        # Tab 1: Dispositivos
        devices_tab = self.create_devices_tab()
        tabs.addTab(devices_tab, "🖥️ Dispositivos")
        
        # Tab 2: Información de red
        network_tab = self.create_network_info_tab()
        tabs.addTab(network_tab, "🌐 Info de Red")
        
        # Tab 3: Logs
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "📋 Logs")
        
        layout.addWidget(tabs)
        panel.setLayout(layout)
        return panel
    
    def create_devices_tab(self):
        """Crear tab de dispositivos"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Información de la red actual
        self.network_info_label = QLabel("Red: No conectado")
        self.network_info_label.setStyleSheet("""
            QLabel {
                background-color: #323237;
                padding: 12px;
                border-radius: 8px;
                font-size: 12px;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self.network_info_label)
        
        # Tabla de dispositivos
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(5)
        self.devices_table.setHorizontalHeaderLabels(["IP", "Tipo", "MAC", "Estado", "Última Conexión"])
        
        # Configurar tabla de dispositivos
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.devices_table)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        self.devices_count_label = QLabel("Dispositivos: 0")
        self.last_update_label = QLabel("Última actualización: --")
        
        stats_layout.addWidget(self.devices_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.last_update_label)
        
        layout.addLayout(stats_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_network_info_tab(self):
        """Crear tab de información de red"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Información detallada de la red
        self.detailed_network_info = QTextEdit()
        self.detailed_network_info.setReadOnly(True)
        self.detailed_network_info.setMaximumHeight(200)
        layout.addWidget(self.detailed_network_info)
        
        # Gráfico de red (simulado con tabla)
        network_card = ModernCard("🗺️ Mapa de Red")
        layout.addWidget(network_card)
        
        tab.setLayout(layout)
        return tab
    
    def create_logs_tab(self):
        """Crear tab de logs"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Área de logs
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)
        
        # Controles de logs
        logs_controls = QHBoxLayout()
        
        clear_logs_btn = QPushButton("🗑️ Limpiar Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        logs_controls.addWidget(clear_logs_btn)
        
        logs_controls.addStretch()
        
        export_logs_btn = QPushButton("💾 Exportar Logs")
        export_logs_btn.clicked.connect(self.export_logs)
        logs_controls.addWidget(export_logs_btn)
        
        layout.addLayout(logs_controls)
        
        tab.setLayout(layout)
        return tab
    
    def setup_status_bar(self):
        """Configurar barra de estado"""
        status_bar = QStatusBar()
        
        # Elementos de la barra de estado
        self.status_label = QLabel("Listo")
        self.connection_status_label = QLabel("Desconectado")
        self.device_count_status = QLabel("0 dispositivos")
        
        status_bar.addWidget(self.status_label)
        status_bar.addPermanentWidget(self.device_count_status)
        status_bar.addPermanentWidget(self.connection_status_label)
        
        self.setStatusBar(status_bar)
    
    def setup_timers(self):
        """Configurar timers para actualización automática"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_update)
        self.refresh_timer.start(self.refresh_interval * 1000)
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Cada 5 segundos
    
    def log_message(self, message, level="INFO"):
        """Agregar mensaje a los logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#ffffff",
            "SUCCESS": "#4caf50", 
            "WARNING": "#ff9800",
            "ERROR": "#f44336"
        }
        
        color = color_map.get(level, "#ffffff")
        formatted_message = f'<span style="color: #888888">[{timestamp}]</span> <span style="color: {color}">[{level}]</span> {message}'
        
        self.logs_text.append(formatted_message)
        
        # Mantener solo las últimas 100 líneas
        document = self.logs_text.document()
        if document.blockCount() > 100:
            cursor = self.logs_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def update_esp32_ip(self):
        """Actualizar IP del ESP32"""
        new_ip = self.ip_entry.text().strip()
        if new_ip:
            self.esp32_ip = new_ip
            self.log_message(f"IP del ESP32 actualizada a: {new_ip}")
            self.update_status()
    
    def scan_wifi_networks(self):
        """Escanear redes WiFi"""
        self.log_message("Iniciando escaneo de redes WiFi...")
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.scan_thread = NetworkScannerThread(self.esp32_ip, "scan_wifi")
        self.scan_thread.data_updated.connect(self.on_wifi_scan_complete)
        self.scan_thread.error_occurred.connect(self.on_network_error)
        self.scan_thread.start()
    
    def on_wifi_scan_complete(self, data):
        """Callback cuando se completa el escaneo WiFi"""
        self.progress_bar.hide()
        networks = data.get('networks', [])
        
        self.wifi_table.setRowCount(len(networks))
        
        for i, network in enumerate(networks):
            ssid = network.get('ssid', '')
            rssi = network.get('rssi', 0)
            encryption = network.get('encryption', '')
            channel = network.get('channel', '')
            
            # Determinar calidad de señal
            if rssi > -50:
                signal_text = f"{rssi} dBm (Excelente)"
                signal_color = "#4caf50"
            elif rssi > -60:
                signal_text = f"{rssi} dBm (Buena)"
                signal_color = "#8bc34a"
            elif rssi > -70:
                signal_text = f"{rssi} dBm (Regular)"
                signal_color = "#ff9800"
            else:
                signal_text = f"{rssi} dBm (Débil)"
                signal_color = "#f44336"
            
            # Crear items de tabla con colores
            ssid_item = QTableWidgetItem(ssid)
            signal_item = QTableWidgetItem(signal_text)
            signal_item.setForeground(QColor(signal_color))
            encryption_item = QTableWidgetItem(encryption)
            channel_item = QTableWidgetItem(str(channel))
            
            self.wifi_table.setItem(i, 0, ssid_item)
            self.wifi_table.setItem(i, 1, signal_item)
            self.wifi_table.setItem(i, 2, encryption_item)
            self.wifi_table.setItem(i, 3, channel_item)
        
        self.log_message(f"Escaneo completado: {len(networks)} redes encontradas", "SUCCESS")
    
    def on_wifi_double_click(self, row, column):
        """Manejar doble clic en red WiFi"""
        ssid_item = self.wifi_table.item(row, 0)
        if ssid_item:
            ssid = ssid_item.text()
            self.log_message(f"Red seleccionada: {ssid}")
    
    def connect_to_wifi(self):
        """Conectar a red WiFi seleccionada"""
        current_row = self.wifi_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione una red WiFi")
            return
        
        ssid_item = self.wifi_table.item(current_row, 0)
        encryption_item = self.wifi_table.item(current_row, 2)
        
        if not ssid_item:
            return
        
        ssid = ssid_item.text()
        password = self.password_entry.text()
        encryption = encryption_item.text() if encryption_item else ""
        
        if "Secured" in encryption and not password:
            QMessageBox.warning(self, "Advertencia", "Ingrese la contraseña para la red")
            return
        
        self.log_message(f"Conectando a red: {ssid}")
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        self.status_indicator.set_status("connecting")
        
        data = {'ssid': ssid, 'password': password}
        self.connect_thread = NetworkScannerThread(self.esp32_ip, "connect", data)
        self.connect_thread.data_updated.connect(self.on_wifi_connect_complete)
        self.connect_thread.error_occurred.connect(self.on_network_error)
        self.connect_thread.start()
    
    def on_wifi_connect_complete(self, data):
        """Callback cuando se completa la conexión WiFi"""
        self.progress_bar.hide()
        
        if data.get('success', False):
            ssid = data.get('ssid', 'Unknown')
            ip = data.get('ip', 'Unknown')
            
            self.connected = True
            self.status_indicator.set_status("connected")
            self.connection_label.setText(f"Estado: Conectado a {ssid} ({ip})")
            self.connection_label.setStyleSheet("""
                QLabel {
                    background-color: #4caf5020;
                    border: 1px solid #4caf50;
                    color: #4caf50;
                    padding: 8px;
                    border-radius: 6px;
                    font-weight: bold;
                }
            """)
            
            self.password_entry.clear()
            self.log_message(f"Conectado exitosamente a {ssid} ({ip})", "SUCCESS")
            
            # Actualizar información de estado
            self.connection_status_label.setText(f"Conectado a {ssid}")
            self.status_label.setText("Conectado")
            
            # Iniciar monitoreo de dispositivos
            self.refresh_devices()
            
            QMessageBox.information(self, "Éxito", f"Conectado exitosamente a {ssid}\nIP: {ip}")
        else:
            self.status_indicator.set_status("error")
            self.connection_label.setText("Estado: Error de conexión")
            self.connection_label.setStyleSheet("""
                QLabel {
                    background-color: #f4433620;
                    border: 1px solid #f44336;
                    color: #f44336;
                    padding: 8px;
                    border-radius: 6px;
                    font-weight: bold;
                }
            """)
            self.log_message("Error al conectar a la red WiFi", "ERROR")
            QMessageBox.critical(self, "Error", "No se pudo conectar a la red")
    
    def disconnect_wifi(self):
        """Desconectar de WiFi"""
        self.log_message("Desconectando de WiFi...")
        
        self.disconnect_thread = NetworkScannerThread(self.esp32_ip, "disconnect")
        self.disconnect_thread.data_updated.connect(self.on_wifi_disconnect_complete)
        self.disconnect_thread.error_occurred.connect(self.on_network_error)
        self.disconnect_thread.start()
    
    def on_wifi_disconnect_complete(self, data):
        """Callback cuando se completa la desconexión"""
        if data.get('success', False):
            self.connected = False
            self.status_indicator.set_status("disconnected")
            self.connection_label.setText("Estado: Desconectado")
            self.connection_label.setStyleSheet("""
                QLabel {
                    background-color: #323237;
                    padding: 8px;
                    border-radius: 6px;
                    color: #ffffff;
                }
            """)
            
            # Limpiar información
            self.devices_table.setRowCount(0)
            self.network_info_label.setText("Red: No conectado")
            self.detailed_network_info.clear()
            self.device_count_status.setText("0 dispositivos")
            self.connection_status_label.setText("Desconectado")
            self.status_label.setText("Desconectado")
            
            self.log_message("Desconectado exitosamente", "SUCCESS")
            QMessageBox.information(self, "Info", "Desconectado de la red WiFi")
    
    def update_status(self):
        """Actualizar estado de conexión"""
        self.status_thread = NetworkScannerThread(self.esp32_ip, "status")
        self.status_thread.data_updated.connect(self.on_status_update)
        self.status_thread.error_occurred.connect(self.on_status_error)
        self.status_thread.start()
    
    def on_status_update(self, data):
        """Callback para actualización de estado"""
        if data.get('connected', False):
            if not self.connected:
                # Cambio de estado a conectado
                self.connected = True
                self.status_indicator.set_status("connected")
                
                ssid = data.get('ssid', 'Unknown')
                ip = data.get('ip', 'Unknown')
                rssi = data.get('rssi', 0)
                
                signal_quality = "Excelente" if rssi > -50 else \
                                "Buena" if rssi > -60 else \
                                "Regular" if rssi > -70 else "Débil"
                
                self.connection_label.setText(f"Estado: Conectado a {ssid} ({ip}) - {signal_quality}")
                self.connection_label.setStyleSheet("""
                    QLabel {
                        background-color: #4caf5020;
                        border: 1px solid #4caf50;
                        color: #4caf50;
                        padding: 8px;
                        border-radius: 6px;
                        font-weight: bold;
                    }
                """)
                
                self.connection_status_label.setText(f"Conectado a {ssid}")
                self.status_label.setText("Conectado")
                
                # Actualizar información detallada de red
                network_info = f"""
Información de Conexión WiFi:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 SSID: {ssid}
📶 IP Local: {ip}
📊 Señal RSSI: {rssi} dBm ({signal_quality})
🔗 Gateway: {data.get('gateway', 'N/A')}
🔍 DNS: {data.get('dns', 'N/A')}
⏰ Estado: Conectado y activo

Última actualización: {datetime.now().strftime('%H:%M:%S')}
                """
                self.detailed_network_info.setText(network_info)
        else:
            if self.connected:
                # Cambio de estado a desconectado
                self.connected = False
                self.status_indicator.set_status("disconnected")
                self.connection_label.setText("Estado: Desconectado")
                self.connection_label.setStyleSheet("""
                    QLabel {
                        background-color: #323237;
                        padding: 8px;
                        border-radius: 6px;
                        color: #ffffff;
                    }
                """)
                self.connection_status_label.setText("Desconectado")
                self.status_label.setText("Desconectado")
                self.detailed_network_info.clear()
    
    def on_status_error(self, error):
        """Callback para errores de estado"""
        self.status_indicator.set_status("error")
        self.connection_label.setText("Estado: ESP32 no accesible")
        self.connection_label.setStyleSheet("""
            QLabel {
                background-color: #f4433620;
                border: 1px solid #f44336;
                color: #f44336;
                padding: 8px;
                border-radius: 6px;
            }
        """)
        self.connection_status_label.setText("Error de comunicación")
        self.status_label.setText("Error")
    
    def refresh_devices(self):
        """Actualizar lista de dispositivos"""
        if self.connected:
            self.devices_thread = NetworkScannerThread(self.esp32_ip, "devices")
            self.devices_thread.data_updated.connect(self.on_devices_update)
            self.devices_thread.error_occurred.connect(self.on_network_error)
            self.devices_thread.start()
    
    def on_devices_update(self, data):
        """Callback para actualización de dispositivos"""
        devices = data.get('devices', [])
        network_info = data.get('networkInfo', {})
        
        # Actualizar tabla de dispositivos
        self.devices_table.setRowCount(len(devices))
        
        for i, device in enumerate(devices):
            ip = device.get('ip', 'N/A')
            device_type = device.get('type', 'Unknown')
            mac = device.get('mac', 'Unknown')
            active = device.get('active', False)
            last_seen = device.get('lastSeen')
            
            # Estado visual
            if active:
                status_text = "🟢 Activo"
                status_color = "#4caf50"
            else:
                status_text = "🔴 Inactivo"
                status_color = "#f44336"
            
            # Formatear última conexión
            if last_seen:
                last_seen_str = datetime.fromtimestamp(last_seen/1000).strftime('%H:%M:%S')
            else:
                last_seen_str = "N/A"
            
            # Crear items con colores
            ip_item = QTableWidgetItem(ip)
            type_item = QTableWidgetItem(device_type)
            mac_item = QTableWidgetItem(mac)
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(status_color))
            time_item = QTableWidgetItem(last_seen_str)
            
            # Destacar el propio dispositivo
            if "Self" in device_type:
                for item in [ip_item, type_item, mac_item, status_item, time_item]:
                    item.setBackground(QColor("#007acc20"))
            
            self.devices_table.setItem(i, 0, ip_item)
            self.devices_table.setItem(i, 1, type_item)
            self.devices_table.setItem(i, 2, mac_item)
            self.devices_table.setItem(i, 3, status_item)
            self.devices_table.setItem(i, 4, time_item)
        
        # Actualizar información de red
        if network_info:
            subnet = network_info.get('subnet', 'N/A')
            network = network_info.get('network', 'N/A')
            broadcast = network_info.get('broadcast', 'N/A')
            gateway = network_info.get('gateway', 'N/A')
            total_devices = network_info.get('totalDevices', 0)
            
            network_text = f"Red: {network}/{subnet} | Gateway: {gateway} | Dispositivos: {total_devices}"
            self.network_info_label.setText(network_text)
        
        # Actualizar estadísticas
        active_devices = len([d for d in devices if d.get('active', False)])
        self.devices_count_label.setText(f"Dispositivos activos: {active_devices}/{len(devices)}")
        self.device_count_status.setText(f"{active_devices} dispositivos activos")
        
        # Actualizar timestamp
        now = datetime.now().strftime('%H:%M:%S')
        self.last_update_label.setText(f"Última actualización: {now}")
        
        self.log_message(f"Dispositivos actualizados: {active_devices} activos de {len(devices)} total")
    
    def on_network_error(self, error):
        """Callback para errores de red"""
        self.progress_bar.hide()
        self.log_message(f"Error de red: {error}", "ERROR")
        
        # Solo mostrar error crítico si no es un error de rutina
        if "timeout" not in error.lower() and "connection" not in error.lower():
            QMessageBox.critical(self, "Error de Red", f"Error de comunicación:\n{error}")
    
    def auto_update(self):
        """Actualización automática"""
        if self.auto_refresh and self.connected:
            self.refresh_devices()
    
    def toggle_auto_refresh(self, checked):
        """Activar/desactivar actualización automática"""
        self.auto_refresh = checked
        if checked:
            self.log_message("Actualización automática activada")
        else:
            self.log_message("Actualización automática desactivada")
    
    def update_refresh_interval(self, value):
        """Actualizar intervalo de actualización"""
        self.refresh_interval = value
        self.refresh_timer.stop()
        self.refresh_timer.start(value * 1000)
        self.log_message(f"Intervalo de actualización cambiado a {value} segundos")
    
    def clear_logs(self):
        """Limpiar logs"""
        self.logs_text.clear()
        self.log_message("Logs limpiados")
    
    def export_logs(self):
        """Exportar logs a archivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wifi_manager_logs_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"WiFi Manager Logs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                
                # Obtener texto plano sin HTML
                plain_text = self.logs_text.toPlainText()
                f.write(plain_text)
            
            self.log_message(f"Logs exportados a: {filename}", "SUCCESS")
            QMessageBox.information(self, "Éxito", f"Logs exportados exitosamente a:\n{filename}")
            
        except Exception as e:
            self.log_message(f"Error al exportar logs: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Error al exportar logs:\n{str(e)}")
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        self.auto_refresh = False
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Detener threads activos
        for thread_name in ['scan_thread', 'connect_thread', 'disconnect_thread', 'status_thread', 'devices_thread']:
            if hasattr(self, thread_name):
                thread = getattr(self, thread_name)
                if thread.isRunning():
                    thread.quit()
                    thread.wait()
        
        self.log_message("Aplicación cerrada")
        event.accept()

class SplashScreen(QWidget):
    """Pantalla de inicio con loading"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Centrar en pantalla
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Contenedor con fondo
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 2px solid #007acc;
                border-radius: 20px;
            }
        """)
        
        container_layout = QVBoxLayout()
        
        # Logo/Título
        title = QLabel("🛡️ WiFi Manager Pro")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 24px;
                font-weight: bold;
                margin: 20px;
            }
        """)
        container_layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("ESP32-S3 Network Scanner")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                margin-bottom: 30px;
            }
        """)
        container_layout.addWidget(subtitle)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3f3f46;
                border-radius: 8px;
                background-color: #2d2d30;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 6px;
            }
        """)
        container_layout.addWidget(self.progress)
        
        # Status label
        self.status_label = QLabel("Iniciando...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                margin: 10px;
            }
        """)
        container_layout.addWidget(self.status_label)
        
        container.setLayout(container_layout)
        layout.addWidget(container)
        self.setLayout(layout)
        
        # Timer para simular carga
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.current_progress = 0
        self.timer.start(50)
    
    def update_progress(self):
        self.current_progress += 2
        self.progress.setValue(self.current_progress)
        
        # Actualizar estado
        if self.current_progress < 30:
            self.status_label.setText("Cargando componentes...")
        elif self.current_progress < 60:
            self.status_label.setText("Inicializando interfaz...")
        elif self.current_progress < 90:
            self.status_label.setText("Configurando tema...")
        else:
            self.status_label.setText("¡Listo!")
        
        if self.current_progress >= 100:
            self.timer.stop()
            QTimer.singleShot(500, self.close)

def main():
    """Función principal de la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("WiFi Manager Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("ESP32 Tools")
    
    # Configurar fuente
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Mostrar splash screen
    splash = SplashScreen()
    splash.show()
    
    # Procesar eventos para mostrar splash
    app.processEvents()
    
    # Crear ventana principal
    main_window = WiFiManagerGUI()
    
    # Configurar cierre de splash cuando se muestre la ventana principal
    def show_main_window():
        if splash.isVisible():
            splash.close()
        main_window.show()
        main_window.log_message("Aplicación iniciada correctamente", "SUCCESS")
        main_window.log_message(f"ESP32 IP configurada: {main_window.esp32_ip}")
        main_window.log_message("Para comenzar, conecta tu PC a la red 'ESP32-WiFiConfig'", "INFO")
    
    # Mostrar ventana principal después del splash
    QTimer.singleShot(3000, show_main_window)
    
    # Manejar cierre limpio
    def cleanup():
        main_window.close()
    
    app.aboutToQuit.connect(cleanup)
    
    # Ejecutar aplicación
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()