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
        
        # Arduino Port
        self.port_input = QComboBox()
        self.port_input.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", 
                                  "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"])
        self.port_input.setEditable(True)
        if settings and "port" in settings:
            self.port_input.setCurrentText(settings["port"])
        layout.addRow("Arduino Port:", self.port_input)
        
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
        
        # Arduino Port for LedTeacher
        self.ledteacher_port = QComboBox()
        self.ledteacher_port.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8",
                                       "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"])
        self.ledteacher_port.setEditable(True)
        if settings and "ledteacher_port" in settings:
            self.ledteacher_port.setCurrentText(settings["ledteacher_port"])
        else:
            self.ledteacher_port.setCurrentText("COM4")
        comm_layout.addRow("Arduino Port:", self.ledteacher_port)
        
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
        
        return widget
        
    def _choose_played_note_color(self):
        """Open color picker for played note color"""
        color = QColorDialog.getColor(self.played_note_color, self, "Choose Played Note Color")
        if color.isValid():
            self.played_note_color = color
            self.played_note_color_btn.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});")
    
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
            "port": self.port_input.currentText(),
            "baud_rate": int(self.baud_combo.currentText()),
            "auto_reconnect": self.auto_reconnect.isChecked(),
            
            # LedTeacher
            "ledteacher_enabled": self.ledteacher_enabled.isChecked(),
            "leds_per_key": self.leds_per_key.value(),
            "led_brightness": self.led_brightness.value(),
            "led_color_mode": self.led_color_mode.currentText(),
            "ledteacher_port": self.ledteacher_port.currentText(),
            "ledteacher_baud": int(self.ledteacher_baud.currentText())
        }
