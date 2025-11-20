from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QDialogButtonBox, QSpinBox, QTabWidget, QWidget, QSlider,
                             QCheckBox, QGroupBox, QFormLayout, QPushButton, QColorDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class SettingsDialog(QDialog):
    def __init__(self, current_settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(500, 400)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Tab 1: Piano Configuration
        piano_tab = self._create_piano_tab(current_settings)
        tabs.addTab(piano_tab, "Piano")
        
        # Tab 2: Sound & Audio
        audio_tab = self._create_audio_tab(current_settings)
        tabs.addTab(audio_tab, "Audio")
        
        # Tab 3: Practice Mode
        practice_tab = self._create_practice_tab(current_settings)
        tabs.addTab(practice_tab, "Practice Mode")
        
        # Tab 4: Connection
        connection_tab = self._create_connection_tab(current_settings)
        tabs.addTab(connection_tab, "Connection")
        
        # Tab 5: LedTeacher (Arduino)
        ledteacher_tab = self._create_ledteacher_tab(current_settings)
        tabs.addTab(ledteacher_tab, "LedTeacher")
        
        main_layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #34495e;
                background-color: #34495e;
            }
            QTabBar::tab {
                background-color: #34495e;
                color: white;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
            }
            QLabel {
                color: white;
            }
            QComboBox, QSpinBox {
                background-color: #34495e;
                color: white;
                border: 1px solid #7f8c8d;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QSlider::groove:horizontal {
                background: #34495e;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QCheckBox {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
    
    def _create_piano_tab(self, settings):
        """Piano configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Number of keys
        self.keys_combo = QComboBox()
        self.keys_combo.addItems(["88", "76", "61", "49", "37", "25"])
        if settings and "keys" in settings:
            index = self.keys_combo.findText(str(settings["keys"]))
            if index >= 0:
                self.keys_combo.setCurrentIndex(index)
        layout.addRow("Number of Keys:", self.keys_combo)
        
        # Starting key
        self.start_key_combo = QComboBox()
        self.start_key_combo.addItems(["A0 (21)", "C1 (24)", "C2 (36)", "C3 (48)", "C4 (60)"])
        if settings and "start_key" in settings:
            self.start_key_combo.setCurrentText(settings["start_key"])
        else:
            self.start_key_combo.setCurrentIndex(0)  # A0 default for 88 keys
        layout.addRow("Starting Key:", self.start_key_combo)
        
        # Visual options group
        visual_group = QGroupBox("Visual Options")
        visual_layout = QVBoxLayout()
        
        self.show_key_labels = QCheckBox("Show note names on keys (C, D, E...)")
        self.show_key_labels.setChecked(settings.get("show_key_labels", True) if settings else True)
        visual_layout.addWidget(self.show_key_labels)
        
        self.show_finger_colors = QCheckBox("Show finger colors on keys")
        self.show_finger_colors.setChecked(settings.get("show_finger_colors", True) if settings else True)
        visual_layout.addWidget(self.show_finger_colors)
        
        self.show_finger_numbers = QCheckBox("Show finger numbers (1-5)")
        self.show_finger_numbers.setChecked(settings.get("show_finger_numbers", True) if settings else True)
        visual_layout.addWidget(self.show_finger_numbers)
        
        self.show_active_note_colors = QCheckBox("Show colors when notes are played")
        self.show_active_note_colors.setChecked(settings.get("show_active_note_colors", True) if settings else True)
        visual_layout.addWidget(self.show_active_note_colors)
        
        self.show_staff_note_colors = QCheckBox("Show colors on staff notes")
        self.show_staff_note_colors.setChecked(settings.get("show_staff_note_colors", True) if settings else True)
        visual_layout.addWidget(self.show_staff_note_colors)
        
        # Played note color picker
        color_layout = QHBoxLayout()
        color_label = QLabel("Color for played notes:")
        self.played_note_color_btn = QPushButton("")
        self.played_note_color_btn.setFixedSize(50, 25)
        
        # Get color from settings or use default electric blue
        if settings and "played_note_color" in settings:
            color_data = settings["played_note_color"]
            self.played_note_color = QColor(color_data[0], color_data[1], color_data[2])
        else:
            self.played_note_color = QColor(0, 120, 255)  # Electric blue default
        
        self.played_note_color_btn.setStyleSheet(f"background-color: rgb({self.played_note_color.red()}, {self.played_note_color.green()}, {self.played_note_color.blue()});")
        self.played_note_color_btn.clicked.connect(self._choose_played_note_color)
        
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.played_note_color_btn)
        color_layout.addStretch()
        visual_layout.addLayout(color_layout)
        
        visual_group.setLayout(visual_layout)
        layout.addRow(visual_group)
        
        layout.addRow(QLabel(""))  # Spacer
        
        return widget
    
    def _create_audio_tab(self, settings):
        """Audio configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Sound selection
        self.sound_combo = QComboBox()
        self.sound_combo.addItems(["Classic Piano", "Electric Piano", "Organ", "Harpsichord"])
        if settings and "sound" in settings:
            self.sound_combo.setCurrentText(settings["sound"])
        else:
            self.sound_combo.setCurrentIndex(0)
        layout.addRow("Piano Sound:", self.sound_combo)
        
        # Volume control
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(settings.get("volume", 80) if settings else 80)
        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        layout.addRow("Volume:", volume_layout)
        
        # Metronome volume
        metronome_layout = QHBoxLayout()
        self.metronome_slider = QSlider(Qt.Orientation.Horizontal)
        self.metronome_slider.setRange(0, 100)
        self.metronome_slider.setValue(settings.get("metronome_volume", 50) if settings else 50)
        self.metronome_label = QLabel(f"{self.metronome_slider.value()}%")
        self.metronome_slider.valueChanged.connect(lambda v: self.metronome_label.setText(f"{v}%"))
        metronome_layout.addWidget(self.metronome_slider)
        metronome_layout.addWidget(self.metronome_label)
        layout.addRow("Metronome Volume:", metronome_layout)
        
        # Audio latency
        self.latency_spin = QSpinBox()
        self.latency_spin.setRange(0, 500)
        self.latency_spin.setValue(settings.get("audio_latency", 50) if settings else 50)
        self.latency_spin.setSuffix(" ms")
        layout.addRow("Audio Latency:", self.latency_spin)
        
        layout.addRow(QLabel(""))  # Spacer
        
        return widget
    
    def _create_practice_tab(self, settings):
        """Practice mode configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Waiting time group
        wait_group = QGroupBox("Timing Settings")
        wait_layout = QFormLayout(wait_group)
        
        self.preparation_time_spin = QSpinBox()
        self.preparation_time_spin.setRange(0, 10)
        self.preparation_time_spin.setValue(settings.get("preparation_time", 3) if settings else 3)
        self.preparation_time_spin.setSuffix(" seconds")
        wait_layout.addRow("Preparation Time:", self.preparation_time_spin)
        
        self.wait_time_spin = QSpinBox()
        self.wait_time_spin.setRange(0, 60)
        self.wait_time_spin.setValue(settings.get("wait_time", 10) if settings else 10)
        self.wait_time_spin.setSuffix(" seconds")
        wait_layout.addRow("Max Wait Time:", self.wait_time_spin)
        
        layout.addWidget(wait_group)
        
        # Practice mode options
        options_group = QGroupBox("Practice Options")
        options_layout = QVBoxLayout(options_group)
        
        self.show_hints = QCheckBox("Show note hints")
        self.show_hints.setChecked(settings.get("show_hints", True) if settings else True)
        options_layout.addWidget(self.show_hints)
        
        self.auto_pause = QCheckBox("Auto-pause on wrong note")
        self.auto_pause.setChecked(settings.get("auto_pause", False) if settings else False)
        options_layout.addWidget(self.auto_pause)
        
        self.show_mistakes = QCheckBox("Highlight mistakes in red")
        self.show_mistakes.setChecked(settings.get("show_mistakes", True) if settings else True)
        options_layout.addWidget(self.show_mistakes)
        
        self.repeat_section = QCheckBox("Auto-repeat difficult sections")
        self.repeat_section.setChecked(settings.get("repeat_section", False) if settings else False)
        options_layout.addWidget(self.repeat_section)
        
        layout.addWidget(options_group)
        
        # Difficulty
        difficulty_group = QGroupBox("Difficulty Settings")
        difficulty_layout = QFormLayout(difficulty_group)
        
        self.tempo_slider = QSlider(Qt.Orientation.Horizontal)
        self.tempo_slider.setRange(25, 150)
        self.tempo_slider.setValue(settings.get("practice_tempo", 75) if settings else 75)
        tempo_label_layout = QHBoxLayout()
        self.tempo_percentage = QLabel(f"{self.tempo_slider.value()}%")
        self.tempo_slider.valueChanged.connect(lambda v: self.tempo_percentage.setText(f"{v}%"))
        tempo_label_layout.addWidget(self.tempo_slider)
        tempo_label_layout.addWidget(self.tempo_percentage)
        difficulty_layout.addRow("Practice Tempo:", tempo_label_layout)
        
        layout.addWidget(difficulty_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_connection_tab(self, settings):
        """Connection configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Arduino Port with auto-detection
        port_layout_conn = QHBoxLayout()
        self.port_input = QComboBox()
        self.port_input.setMinimumWidth(300)
        self._refresh_connection_ports(settings)
        port_layout_conn.addWidget(self.port_input)
        
        refresh_conn_btn = QPushButton("🔄")
        refresh_conn_btn.setMaximumWidth(40)
        refresh_conn_btn.setToolTip("Refresh available ports")
        refresh_conn_btn.clicked.connect(lambda: self._refresh_connection_ports(settings))
        port_layout_conn.addWidget(refresh_conn_btn)
        
        layout.addRow("Arduino Port:", port_layout_conn)
        
        # Baud rate
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        if settings and "baud_rate" in settings:
            self.baud_combo.setCurrentText(str(settings["baud_rate"]))
        else:
            self.baud_combo.setCurrentIndex(0)  # 9600 default
        layout.addRow("Baud Rate:", self.baud_combo)
        
        # Auto-reconnect
        self.auto_reconnect = QCheckBox("Auto-reconnect on disconnect")
        self.auto_reconnect.setChecked(settings.get("auto_reconnect", True) if settings else True)
        layout.addRow("", self.auto_reconnect)
        
        layout.addRow(QLabel(""))  # Spacer
        
        return widget
    
    def _create_ledteacher_tab(self, settings):
        """LedTeacher (Arduino) configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Enable LedTeacher
        self.ledteacher_enabled = QCheckBox("Enable LedTeacher Arduino")
        self.ledteacher_enabled.setChecked(settings.get("ledteacher_enabled", False) if settings else False)
        layout.addRow("", self.ledteacher_enabled)
        
        layout.addRow(QLabel(""))  # Spacer
        
        # LED Configuration Group
        led_group = QGroupBox("LED Configuration")
        led_layout = QFormLayout()
        
        # Number of LEDs per key
        self.leds_per_key = QSpinBox()
        self.leds_per_key.setRange(1, 10)
        self.leds_per_key.setValue(settings.get("leds_per_key", 1) if settings else 1)
        led_layout.addRow("LEDs per key:", self.leds_per_key)
        
        # LED brightness
        brightness_layout = QHBoxLayout()
        self.led_brightness = QSlider(Qt.Orientation.Horizontal)
        self.led_brightness.setRange(0, 255)
        self.led_brightness.setValue(settings.get("led_brightness", 128) if settings else 128)
        self.brightness_label = QLabel(str(self.led_brightness.value()))
        self.led_brightness.valueChanged.connect(lambda v: self.brightness_label.setText(str(v)))
        brightness_layout.addWidget(self.led_brightness)
        brightness_layout.addWidget(self.brightness_label)
        led_layout.addRow("LED Brightness:", brightness_layout)
        
        # LED color mode
        self.led_color_mode = QComboBox()
        self.led_color_mode.addItems(["Finger Colors", "Single Color", "Rainbow", "Note Pitch"])
        if settings and "led_color_mode" in settings:
            self.led_color_mode.setCurrentText(settings["led_color_mode"])
        else:
            self.led_color_mode.setCurrentIndex(0)
        led_layout.addRow("Color Mode:", self.led_color_mode)
        
        led_group.setLayout(led_layout)
        layout.addRow(led_group)
        
        layout.addRow(QLabel(""))  # Spacer
        
        # Communication Group
        comm_group = QGroupBox("Communication")
        comm_layout = QFormLayout()
        
        # Arduino Port for LedTeacher with auto-detection
        port_layout_led = QHBoxLayout()
        self.ledteacher_port = QComboBox()
        self.ledteacher_port.setMinimumWidth(300)
        self._refresh_ledteacher_ports(settings)
        port_layout_led.addWidget(self.ledteacher_port)
        
        refresh_led_btn = QPushButton("🔄")
        refresh_led_btn.setMaximumWidth(40)
        refresh_led_btn.setToolTip("Refresh available ports")
        refresh_led_btn.clicked.connect(lambda: self._refresh_ledteacher_ports(settings))
        port_layout_led.addWidget(refresh_led_btn)
        
        comm_layout.addRow("Arduino Port:", port_layout_led)
        
        # Baud rate for LedTeacher
        self.ledteacher_baud = QComboBox()
        self.ledteacher_baud.addItems(["9600", "19200", "38400", "57600", "115200"])
        if settings and "ledteacher_baud" in settings:
            self.ledteacher_baud.setCurrentText(str(settings["ledteacher_baud"]))
        else:
            self.ledteacher_baud.setCurrentText("115200")
        comm_layout.addRow("Baud Rate:", self.ledteacher_baud)
        
        comm_group.setLayout(comm_layout)
        layout.addRow(comm_group)
        
        layout.addRow(QLabel(""))  # Spacer
        
        # Test Connection Group
        test_group = QGroupBox("🧪 Test Connection")
        test_layout = QVBoxLayout()
        
        test_info = QLabel("Test the Arduino connection by lighting LEDs and playing sounds.")
        test_info.setWordWrap(True)
        test_info.setStyleSheet("color: #bdc3c7; font-style: italic; padding: 5px;")
        test_layout.addWidget(test_info)
        
        test_btn = QPushButton("🎹 Test Connection (LEDs + Sound)")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        test_btn.clicked.connect(self._test_arduino_connection)
        test_layout.addWidget(test_btn)
        
        self.test_status_label = QLabel("")
        self.test_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.test_status_label.setStyleSheet("padding: 5px; font-size: 12px;")
        test_layout.addWidget(self.test_status_label)
        
        # Arduino Response Console
        console_label = QLabel("Arduino Responses:")
        console_label.setStyleSheet("color: #bdc3c7; font-weight: bold; margin-top: 10px;")
        test_layout.addWidget(console_label)
        
        self.arduino_console = QTextEdit()
        self.arduino_console.setReadOnly(True)
        self.arduino_console.setMaximumHeight(150)
        self.arduino_console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)
        self.arduino_console.setPlaceholderText("Arduino responses will appear here...")
        test_layout.addWidget(self.arduino_console)
        
        clear_console_btn = QPushButton("🗑️ Clear Console")
        clear_console_btn.clicked.connect(self.arduino_console.clear)
        clear_console_btn.setMaximumWidth(150)
        test_layout.addWidget(clear_console_btn)
        
        test_group.setLayout(test_layout)
        layout.addRow(test_group)
        
        return widget
        
    def _choose_played_note_color(self):
        """Open color picker for played note color"""
        color = QColorDialog.getColor(self.played_note_color, self, "Choose Played Note Color")
        if color.isValid():
            self.played_note_color = color
            self.played_note_color_btn.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});")
    
    def _refresh_connection_ports(self, settings=None):
        """Refresh and populate Connection port selector with available ports"""
        import serial.tools.list_ports
        
        self.port_input.clear()
        ports = serial.tools.list_ports.comports()
        
        # Store the mapping of display text to actual port
        self.connection_port_map = {}
        
        if not ports:
            self.port_input.addItem("❌ No ports found")
            return
        
        # Get saved port from settings
        saved_port = settings.get("port", "COM3") if settings else "COM3"
        
        # Add each port with its description
        for i, port in enumerate(ports):
            # Create readable display name
            display_name = f"{port.device} - {port.description}"
            if port.manufacturer:
                display_name += f" ({port.manufacturer})"
            
            self.port_input.addItem(display_name)
            self.connection_port_map[display_name] = port.device
            
            # Select the saved port
            if port.device == saved_port:
                self.port_input.setCurrentIndex(i)
        
        # If saved port not found, try to select Arduino/CH340/CP210x
        if self.port_input.currentIndex() == -1:
            for i in range(self.port_input.count()):
                text = self.port_input.itemText(i).lower()
                if any(keyword in text for keyword in ["arduino", "ch340", "cp210", "usb-serial", "ftdi"]):
                    self.port_input.setCurrentIndex(i)
                    break
    
    def _get_actual_connection_port(self):
        """Get the actual COM port from the selected display text"""
        display_text = self.port_input.currentText()
        return self.connection_port_map.get(display_text, display_text.split(" - ")[0] if " - " in display_text else display_text)
    
    def _refresh_ledteacher_ports(self, settings=None):
        """Refresh and populate LedTeacher port selector with available ports"""
        import serial.tools.list_ports
        
        self.ledteacher_port.clear()
        ports = serial.tools.list_ports.comports()
        
        # Store the mapping of display text to actual port
        self.ledteacher_port_map = {}
        
        if not ports:
            self.ledteacher_port.addItem("❌ No ports found")
            return
        
        # Get saved port from settings
        saved_port = settings.get("ledteacher_port", "COM4") if settings else "COM4"
        
        # Add each port with its description
        for i, port in enumerate(ports):
            # Create readable display name
            display_name = f"{port.device} - {port.description}"
            if port.manufacturer:
                display_name += f" ({port.manufacturer})"
            
            self.ledteacher_port.addItem(display_name)
            self.ledteacher_port_map[display_name] = port.device
            
            # Select the saved port
            if port.device == saved_port:
                self.ledteacher_port.setCurrentIndex(i)
        
        # If saved port not found, try to select Arduino/CH340/CP210x
        if self.ledteacher_port.currentIndex() == -1:
            for i in range(self.ledteacher_port.count()):
                text = self.ledteacher_port.itemText(i).lower()
                if any(keyword in text for keyword in ["arduino", "ch340", "cp210", "usb-serial", "ftdi"]):
                    self.ledteacher_port.setCurrentIndex(i)
                    break
    
    def _get_actual_ledteacher_port(self):
        """Get the actual COM port from the selected display text"""
        display_text = self.ledteacher_port.currentText()
        return self.ledteacher_port_map.get(display_text, display_text.split(" - ")[0] if " - " in display_text else display_text)
    
    def _find_process_using_port(self, port):
        """Try to find which process is using the serial port (Windows only)"""
        try:
            import subprocess
            import re
            
            print(f"\n🔍 Searching for process using {port}...")
            
            # Check for common programs that use serial ports
            common_culprits = {
                'arduino': 'Arduino IDE',
                'arduino_debug': 'Arduino IDE (Debug)',
                'platformio-ide': 'PlatformIO IDE',
                'python': 'Python (maybe this program!)',
                'putty': 'PuTTY',
                'teraterm': 'TeraTerm',
                'realterm': 'RealTerm',
                'com0com': 'COM0COM',
                'vscodium': 'VSCodium/VSCode'
            }
            
            # Get list of running processes
            result = subprocess.run(
                ['tasklist', '/FO', 'CSV', '/NH'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                print(f"  📋 Scanning {len(output.splitlines())} running processes...")
                
                for proc_key, proc_name in common_culprits.items():
                    if proc_key in output:
                        print(f"  ✓ Found: {proc_name}")
                        return proc_name
                
                print("  ℹ️ No common serial programs found running")
            
            return None
            
        except Exception as e:
            print(f"  ⚠️ Could not detect process: {e}")
            return None
    
    def _test_arduino_connection(self):
        """Test Arduino connection with LEDs and sound"""
        import serial
        import time
        import pygame
        from PyQt6.QtCore import QTimer
        
        print("\n" + "="*60)
        print("🧪 ARDUINO CONNECTION TEST - DEBUG MODE")
        print("="*60)
        
        # Validate port selection
        port = self._get_actual_ledteacher_port()
        baud = int(self.ledteacher_baud.currentText())
        
        print(f"Selected display text: {self.ledteacher_port.currentText()}")
        print(f"Mapped port: {port}")
        print(f"Baud rate: {baud}")
        
        if not port or "No ports" in port or port.startswith("❌"):
            print("❌ ERROR: No valid port selected")
            self.test_status_label.setText("❌ No port selected! Click 🔄 to refresh.")
            self.test_status_label.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px; font-size: 12px; border-radius: 3px;")
            QTimer.singleShot(5000, lambda: self.test_status_label.setText(""))
            return
        
        print(f"✓ Attempting connection to {port} at {baud} baud...")
        self.test_status_label.setText(f"⏳ Connecting to {port}...")
        self.test_status_label.setStyleSheet("background-color: #f39c12; color: white; padding: 5px; font-size: 12px; border-radius: 3px;")
        
        try:
            # Initialize pygame mixer for sound
            print("🔊 Initializing pygame mixer...")
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                print("✓ Pygame mixer initialized")
            else:
                print("✓ Pygame mixer already initialized")
            
            # Connect to Arduino
            print(f"🔌 Opening serial port {port}...")
            ser = serial.Serial(port, baud, timeout=0.1)
            print(f"✓ Serial port opened successfully")
            print(f"⏳ Waiting 2 seconds for Arduino reset...")
            time.sleep(2)  # Wait for Arduino reset
            print("✓ Arduino should be ready")
            
            self.test_status_label.setText("✅ Connected! Testing...")
            self.test_status_label.setStyleSheet("background-color: #27ae60; color: white; padding: 5px; font-size: 12px; border-radius: 3px;")
            
            # Test sequence: C major scale (C4 to C5)
            test_notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
            note_names = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
            
            print(f"\n🎹 Starting test sequence: {len(test_notes)} notes")
            print("-" * 60)
            
            for i, (note, name) in enumerate(zip(test_notes, note_names)):
                print(f"\n[{i+1}/{len(test_notes)}] Note: {name} (MIDI {note})")
                
                # Update status
                self.test_status_label.setText(f"🎵 Playing: {name} ({i+1}/{len(test_notes)})")
                
                # Send LED command to Arduino
                command = f"ON:{note}:100\n"
                print(f"  📡 Sending to Arduino: {command.strip()}")
                self.arduino_console.append(f">>> {command.strip()}")
                ser.write(command.encode())
                print(f"  ✓ Command sent successfully")
                
                # Read Arduino response (with timeout)
                response_start = time.time()
                while time.time() - response_start < 0.1:  # 100ms timeout
                    if ser.in_waiting > 0:
                        response = ser.readline().decode('utf-8', errors='ignore').strip()
                        if response:
                            print(f"  ← Arduino: {response}")
                            self.arduino_console.append(f"<<< {response}")
                            self.arduino_console.verticalScrollBar().setValue(
                                self.arduino_console.verticalScrollBar().maximum()
                            )
                    time.sleep(0.01)
                
                # Play sound
                try:
                    # Generate a simple sine wave tone
                    frequency = 440 * (2 ** ((note - 69) / 12))  # A4 = 440Hz
                    sample_rate = 44100
                    duration = 0.3
                    
                    print(f"  🔊 Generating tone: {frequency:.1f} Hz")
                    
                    import numpy as np
                    t = np.linspace(0, duration, int(sample_rate * duration))
                    wave = np.sin(2 * np.pi * frequency * t)
                    
                    # Apply envelope
                    envelope = np.ones_like(wave)
                    fade_samples = int(0.05 * sample_rate)
                    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
                    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
                    wave = wave * envelope * 0.3
                    
                    # Convert to 16-bit
                    wave = np.int16(wave * 32767)
                    stereo_wave = np.column_stack((wave, wave))
                    
                    sound = pygame.sndarray.make_sound(stereo_wave)
                    sound.play()
                    print(f"  ✓ Sound playing")
                    
                except Exception as e:
                    print(f"  ❌ Sound error: {e}")
                
                # Wait
                print(f"  ⏳ Waiting 400ms...")
                time.sleep(0.4)
                
                # Turn off LED
                off_command = f"OFF:{note}\n"
                print(f"  📡 Sending OFF: {off_command.strip()}")
                self.arduino_console.append(f">>> {off_command.strip()}")
                ser.write(off_command.encode())
                
                # Read Arduino response for OFF command
                response_start = time.time()
                while time.time() - response_start < 0.1:  # 100ms timeout
                    if ser.in_waiting > 0:
                        response = ser.readline().decode('utf-8', errors='ignore').strip()
                        if response:
                            print(f"  ← Arduino: {response}")
                            self.arduino_console.append(f"<<< {response}")
                            self.arduino_console.verticalScrollBar().setValue(
                                self.arduino_console.verticalScrollBar().maximum()
                            )
                    time.sleep(0.01)
                
                print(f"  ⏳ Waiting 100ms...")
                time.sleep(0.1)
            
            # Close connection
            print("\n" + "-" * 60)
            print("🔌 Closing serial connection...")
            ser.close()
            print("✓ Serial connection closed")
            
            self.test_status_label.setText("✅ Test completed successfully!")
            self.test_status_label.setStyleSheet("background-color: #27ae60; color: white; padding: 5px; font-size: 12px; border-radius: 3px;")
            
            print("\n✅ TEST COMPLETED SUCCESSFULLY")
            print("="*60 + "\n")
            
            # Clear status after 3 seconds
            QTimer.singleShot(3000, lambda: self.test_status_label.setText(""))
            
        except serial.SerialException as e:
            error_msg = str(e)
            
            print("\n" + "="*60)
            print("❌ SERIAL EXCEPTION CAUGHT")
            print("="*60)
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {error_msg}")
            print(f"Port attempted: {port}")
            print(f"Baud rate: {baud}")
            
            # Try to find which process is using the port
            port_in_use_by = self._find_process_using_port(port)
            if port_in_use_by:
                print(f"🔍 Port in use by: {port_in_use_by}")
            
            # Provide specific error messages
            if "PermissionError" in error_msg or "Access is denied" in error_msg:
                if port_in_use_by:
                    msg = f"❌ Port {port} in use by {port_in_use_by}! Close it first."
                else:
                    msg = f"❌ Port {port} in use! Close Arduino IDE, Serial Monitor, or other programs."
                print("Diagnosis: Port is being used by another program")
            elif "FileNotFoundError" in error_msg or "could not open port" in error_msg:
                msg = f"❌ Port {port} not found! Check cable and click 🔄"
                print("Diagnosis: Port does not exist or device disconnected")
            elif "com" in port.lower() and int(port.replace("COM", "")) > 10:
                msg = f"❌ Port {port} unavailable. Try unplugging/replugging Arduino."
                print("Diagnosis: High COM number may indicate driver issues")
            else:
                # Show full error message without truncation
                msg = f"❌ {error_msg}"
                if len(msg) > 80:
                    msg = f"❌ {error_msg[:77]}..."
                print("Diagnosis: Unknown serial error")
            
            print(f"User message: {msg}")
            print("\n💡 SOLUTIONS:")
            print("  1. Close Arduino IDE (especially Serial Monitor)")
            print("  2. Close any other serial terminal programs (PuTTY, etc.)")
            print("  3. Close other instances of this program")
            print("  4. Unplug and replug the Arduino USB cable")
            print("  5. Try selecting a different port from the dropdown")
            print("="*60 + "\n")
            
            self.test_status_label.setText(msg)
            self.test_status_label.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px; font-size: 11px; border-radius: 3px;")
            self.test_status_label.setWordWrap(True)
            QTimer.singleShot(10000, lambda: self.test_status_label.setText(""))
            
        except Exception as e:
            error_msg = str(e)
            
            print("\n" + "="*60)
            print("❌ UNEXPECTED EXCEPTION CAUGHT")
            print("="*60)
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {error_msg}")
            
            # Print full traceback for debugging
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
            print("="*60 + "\n")
            
            msg = f"❌ Unexpected error: {error_msg[:60]}..."
            self.test_status_label.setText(msg)
            self.test_status_label.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px; font-size: 11px; border-radius: 3px;")
            self.test_status_label.setWordWrap(True)
            QTimer.singleShot(8000, lambda: self.test_status_label.setText(""))
    
    def get_settings(self):
        """Return all settings as dictionary"""
        return {
            # Piano
            "keys": int(self.keys_combo.currentText()),
            "start_key": self.start_key_combo.currentText(),
            "show_key_labels": self.show_key_labels.isChecked(),
            "show_finger_colors": self.show_finger_colors.isChecked(),
            "show_finger_numbers": self.show_finger_numbers.isChecked(),
            "show_active_note_colors": self.show_active_note_colors.isChecked(),
            "show_staff_note_colors": self.show_staff_note_colors.isChecked(),
            "played_note_color": [self.played_note_color.red(), self.played_note_color.green(), self.played_note_color.blue()],
            
            # Audio
            "sound": self.sound_combo.currentText(),
            "volume": self.volume_slider.value(),
            "metronome_volume": self.metronome_slider.value(),
            "audio_latency": self.latency_spin.value(),
            
            # Practice
            "preparation_time": self.preparation_time_spin.value(),
            "wait_time": self.wait_time_spin.value(),
            "show_hints": self.show_hints.isChecked(),
            "auto_pause": self.auto_pause.isChecked(),
            "show_mistakes": self.show_mistakes.isChecked(),
            "repeat_section": self.repeat_section.isChecked(),
            "practice_tempo": self.tempo_slider.value(),
            
            # Connection
            "port": self._get_actual_connection_port(),  # Save actual COM port, not display text
            "baud_rate": int(self.baud_combo.currentText()),
            "auto_reconnect": self.auto_reconnect.isChecked(),
            
            # LedTeacher
            "ledteacher_enabled": self.ledteacher_enabled.isChecked(),
            "leds_per_key": self.leds_per_key.value(),
            "led_brightness": self.led_brightness.value(),
            "led_color_mode": self.led_color_mode.currentText(),
            "ledteacher_port": self._get_actual_ledteacher_port(),  # Save actual COM port, not display text
            "ledteacher_baud": int(self.ledteacher_baud.currentText())
        }
