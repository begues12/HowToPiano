"""
Herramienta de diagnóstico y prueba de conexión Arduino.
Permite probar la comunicación serial y enviar/recibir comandos de prueba.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QComboBox, QSpinBox, QTextEdit, QGroupBox,
                              QCheckBox, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
import serial
import serial.tools.list_ports
import time
import json


class ArduinoTester(QWidget):
    """Widget para probar la conexión y comunicación con Arduino"""
    
    def __init__(self):
        super().__init__()
        self.serial = None
        self.init_ui()
        self.load_settings()
        self.refresh_ports()
        
    def init_ui(self):
        self.setWindowTitle("Arduino Connection Tester")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout()
        
        # === SECTION 1: Connection Settings ===
        conn_group = QGroupBox("🔌 Connection Settings")
        conn_layout = QVBoxLayout()
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        port_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        port_layout.addStretch()
        conn_layout.addLayout(port_layout)
        
        # Baud rate
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baud Rate:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        baud_layout.addWidget(self.baud_combo)
        baud_layout.addStretch()
        conn_layout.addLayout(baud_layout)
        
        # Connect/Disconnect buttons
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("✅ Connect")
        self.connect_btn.clicked.connect(self.connect_arduino)
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("❌ Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_arduino)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-weight: bold;")
        btn_layout.addWidget(self.disconnect_btn)
        conn_layout.addLayout(btn_layout)
        
        # Status label
        self.status_label = QLabel("❌ Not Connected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
        conn_layout.addWidget(self.status_label)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # === SECTION 2: Quick Tests ===
        test_group = QGroupBox("🧪 Quick Tests")
        test_layout = QVBoxLayout()
        
        quick_btn_layout = QHBoxLayout()
        
        test_note_btn = QPushButton("🎹 Test Note C4 (60)")
        test_note_btn.clicked.connect(lambda: self.send_test_note(60))
        quick_btn_layout.addWidget(test_note_btn)
        
        test_scale_btn = QPushButton("🎵 Test C Scale")
        test_scale_btn.clicked.connect(self.test_c_scale)
        quick_btn_layout.addWidget(test_scale_btn)
        
        test_chord_btn = QPushButton("🎼 Test C Chord")
        test_chord_btn.clicked.connect(self.test_c_chord)
        quick_btn_layout.addWidget(test_chord_btn)
        
        test_layout.addLayout(quick_btn_layout)
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # === SECTION 3: Manual Command ===
        manual_group = QGroupBox("✍️ Manual Command")
        manual_layout = QVBoxLayout()
        
        manual_info = QLabel("Protocol: ON:note:velocity or OFF:note\nExample: ON:60:100 or OFF:60")
        manual_info.setStyleSheet("color: gray; font-style: italic;")
        manual_layout.addWidget(manual_info)
        
        cmd_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command (e.g., ON:60:100)")
        self.command_input.returnPressed.connect(self.send_manual_command)
        cmd_layout.addWidget(self.command_input)
        
        send_btn = QPushButton("📤 Send")
        send_btn.clicked.connect(self.send_manual_command)
        cmd_layout.addWidget(send_btn)
        manual_layout.addLayout(cmd_layout)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        # === SECTION 4: Custom Note Test ===
        custom_group = QGroupBox("🎹 Custom Note Test")
        custom_layout = QHBoxLayout()
        
        custom_layout.addWidget(QLabel("Note:"))
        self.note_spin = QSpinBox()
        self.note_spin.setRange(21, 108)
        self.note_spin.setValue(60)
        custom_layout.addWidget(self.note_spin)
        
        custom_layout.addWidget(QLabel("Velocity:"))
        self.velocity_spin = QSpinBox()
        self.velocity_spin.setRange(0, 127)
        self.velocity_spin.setValue(100)
        custom_layout.addWidget(self.velocity_spin)
        
        send_custom_btn = QPushButton("▶️ Send Note")
        send_custom_btn.clicked.connect(self.send_custom_note)
        custom_layout.addWidget(send_custom_btn)
        
        custom_layout.addStretch()
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        # === SECTION 5: Console Log ===
        log_group = QGroupBox("📋 Console Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 9))
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
    def load_settings(self):
        """Load settings from settings.json"""
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.default_port = settings.get("port", "COM3")
                self.default_baud = settings.get("baud_rate", 9600)
                self.baud_combo.setCurrentText(str(self.default_baud))
                self.log(f"📂 Loaded settings: Port={self.default_port}, Baud={self.default_baud}")
        except Exception as e:
            self.log(f"⚠️ Could not load settings: {e}")
            self.default_port = "COM3"
            self.default_baud = 9600
    
    def refresh_ports(self):
        """Refresh available COM ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.log("⚠️ No COM ports found!")
            self.port_combo.addItem("No ports available")
            return
        
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")
            self.log(f"🔍 Found: {port.device} - {port.description}")
        
        # Try to select default port
        for i in range(self.port_combo.count()):
            if self.default_port in self.port_combo.itemText(i):
                self.port_combo.setCurrentIndex(i)
                break
    
    def connect_arduino(self):
        """Connect to Arduino"""
        port_text = self.port_combo.currentText()
        if not port_text or "No ports" in port_text:
            self.log("❌ No valid port selected!")
            return
        
        port = port_text.split(" - ")[0]
        baud = int(self.baud_combo.currentText())
        
        try:
            self.serial = serial.Serial(port, baud, timeout=0.1)
            time.sleep(2)  # Wait for Arduino to reset
            self.log(f"✅ Connected to {port} at {baud} baud")
            self.status_label.setText(f"✅ Connected to {port}")
            self.status_label.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 14px; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
        except Exception as e:
            self.log(f"❌ Connection failed: {e}")
            self.status_label.setText("❌ Connection Failed")
            self.status_label.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-size: 14px; font-weight: bold;")
    
    def disconnect_arduino(self):
        """Disconnect from Arduino"""
        if self.serial:
            self.serial.close()
            self.serial = None
            self.log("🔌 Disconnected")
            self.status_label.setText("❌ Not Connected")
            self.status_label.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
    
    def send_command(self, command: str):
        """Send command to Arduino"""
        if not self.serial or not self.serial.is_open:
            self.log("❌ Not connected! Connect first.")
            return False
        
        try:
            self.serial.write(f"{command}\n".encode())
            self.log(f"📤 Sent: {command}")
            return True
        except Exception as e:
            self.log(f"❌ Send error: {e}")
            return False
    
    def send_manual_command(self):
        """Send manual command from input"""
        command = self.command_input.text().strip()
        if command:
            self.send_command(command)
            self.command_input.clear()
    
    def send_test_note(self, note: int, velocity: int = 100):
        """Send a test note"""
        self.send_command(f"ON:{note}:{velocity}")
        time.sleep(0.5)
        self.send_command(f"OFF:{note}")
    
    def send_custom_note(self):
        """Send custom note from spinboxes"""
        note = self.note_spin.value()
        velocity = self.velocity_spin.value()
        self.send_test_note(note, velocity)
    
    def test_c_scale(self):
        """Test C major scale"""
        scale = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
        self.log("🎵 Playing C major scale...")
        
        for note in scale:
            self.send_command(f"ON:{note}:100")
            time.sleep(0.3)
            self.send_command(f"OFF:{note}")
            time.sleep(0.1)
    
    def test_c_chord(self):
        """Test C major chord"""
        chord = [60, 64, 67]  # C E G
        self.log("🎼 Playing C major chord...")
        
        # Note on
        for note in chord:
            self.send_command(f"ON:{note}:100")
        
        time.sleep(1.0)
        
        # Note off
        for note in chord:
            self.send_command(f"OFF:{note}")
    
    def log(self, message: str):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    tester = ArduinoTester()
    tester.show()
    sys.exit(app.exec())
