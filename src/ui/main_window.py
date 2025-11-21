import sys
import os
import json
import threading
import time
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox, 
                             QSpinBox, QDialog, QTextEdit)
from PyQt6.QtCore import Qt, QThread, QSize, pyqtSignal, QObject, QTimer

from src.core.arduino_conn import ArduinoWorker
from src.core.synth import PianoSynth
from src.core.midi_engine import MidiEngine
from src.ui.score_view import SongLibrary
from src.ui.staff_widget import StaffWidget
from src.ui.settings_dialog import SettingsDialog
from src.ui.piano_widget import PianoWidget
from src.ui.song_list_widget import SongListWidget
from src.ui.progress_bar import ProgressBar
from PyQt6.QtGui import QColor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("How To Piano")
        self.resize(1200, 900)
        
        # Settings file path
        self.settings_file = os.path.join(os.getcwd(), "settings.json")
        
        # Load settings or use defaults
        self.settings = self.load_settings()

        # Initialize Core Components
        # Try to find a soundfont in assets
        sf_path = os.path.join(os.getcwd(), "assets", "soundfonts", "default.sf2")
        if not os.path.exists(sf_path):
            # Fallback or ask user? For now just warn
            print("No default soundfont found.")
        
        self.synth = PianoSynth(sf_path)
        self.midi_engine = MidiEngine(self.synth)
        self.midi_engine.preparation_time = self.settings.get("preparation_time", 3)
        
        # Initialize Song Library
        self.song_library = SongLibrary()
        
        # Training mode manager (will be initialized after widgets are created)
        self.training_manager = None
        
        # UI Setup - Create widgets first
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout (top section + piano at bottom)
        main_v_layout = QVBoxLayout(central_widget)
        main_v_layout.setSpacing(0)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top horizontal section (song list + score/controls)
        top_widget = QWidget()
        main_layout = QHBoxLayout(top_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.addWidget(top_widget)
        
        # Left side: Song list (Canciones)
        self.song_list = SongListWidget(self.song_library)
        self.song_list.setMaximumWidth(200)
        self.song_list.setMinimumWidth(150)
        self.song_list.song_selected.connect(self.load_song_from_library)
        main_layout.addWidget(self.song_list)
        
        # Right side: Vertical layout for Controls and Score
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(right_widget)

        # Controls Area (Acciones - TOP section above staff)
        controls_widget = QWidget()
        controls_widget.setMaximumHeight(42)
        controls_widget.setStyleSheet("background-color: #2c3e50; border-bottom: 2px solid #34495e;")
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(8, 5, 8, 5)
        controls_layout.setSpacing(4)
        right_layout.addWidget(controls_widget)
        
        # Staff Widget (Interactive pentagram - takes most space)
        self.score_view = StaffWidget()
        self.score_view.setMinimumHeight(400)
        right_layout.addWidget(self.score_view, stretch=10)
        
        # Progress Bar (above piano)
        self.progress_bar = ProgressBar()
        self.progress_bar.seek_requested.connect(self.seek_to_time)
        main_v_layout.addWidget(self.progress_bar)
        
        # Piano Widget (Piano - bottom, full width at bottom of entire window)
        self.piano_widget = PianoWidget(num_keys=self.settings["keys"])
        self.piano_widget.setMinimumHeight(100)
        self.piano_widget.setMaximumHeight(150)
        
        # Apply saved visual settings to piano
        self.piano_widget.show_note_names = self.settings.get("show_key_labels", True)
        self.piano_widget.show_finger_colors = self.settings.get("show_finger_colors", True)
        
        # Apply played note color to staff
        self.score_view.played_note_color = self.get_played_note_color()
        self.piano_widget.show_finger_numbers = self.settings.get("show_finger_numbers", True)
        self.piano_widget.show_active_note_colors = self.settings.get("show_active_note_colors", True)
        
        # Apply visual zoom to staff widget
        visual_zoom = self.settings.get("visual_zoom", 100)
        zoom_scale = visual_zoom / 100.0
        self.score_view.visual_zoom_scale = zoom_scale
        self.score_view.staff_spacing = self.score_view.base_staff_spacing * zoom_scale
        self.score_view.left_margin = int(self.score_view.base_left_margin * zoom_scale)
        
        # Apply saved visual settings to staff
        self.score_view.show_note_colors = self.settings.get("show_staff_note_colors", True)
        
        # Apply preparation time from settings
        self.score_view.preparation_time = self.settings.get("preparation_time", 3)
        
        # Disable proportional spacing (using pure time-based triggering)
        self.score_view.use_proportional_spacing = False
        
        main_v_layout.addWidget(self.piano_widget)

        # Arduino (Mock by default for safety, user can configure)
        self.arduino = ArduinoWorker(port="COM3", mock=True)
        self.arduino_thread = QThread()
        self.arduino.moveToThread(self.arduino_thread)
        self.arduino_thread.started.connect(self.arduino.run)
        
        # Connect Arduino -> MidiEngine
        self.arduino.note_on.connect(self.midi_engine.on_user_note_on)
        self.arduino.note_off.connect(self.midi_engine.on_user_note_off)
        
        # Connect Arduino -> PianoWidget (Visual Feedback with bright orange for user input)
        self.arduino.note_on.connect(self.on_arduino_note_on)
        self.arduino.note_off.connect(self.on_arduino_note_off)
        
        # Connect PianoWidget Mouse -> MidiEngine (Interactive Piano)
        self.piano_widget.note_pressed.connect(self.midi_engine.on_user_note_on)
        self.piano_widget.note_released.connect(self.midi_engine.on_user_note_off)
        
        # Connect PianoWidget Mouse -> Visual feedback (registered)
        self.piano_widget.note_pressed.connect(self.on_user_note_pressed)
        self.piano_widget.note_released.connect(self.on_user_note_released)
        
        # Connect PianoWidget -> Arduino LED control
        self.piano_widget.note_pressed.connect(self.send_arduino_led_on)
        self.piano_widget.note_released.connect(self.send_arduino_led_off)
        
        self.arduino_thread.start()

        # Control Buttons - SVG Icons
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtGui import QIcon, QPixmap, QPainter as QP
        
        def create_svg_icon(svg_data, color="#ffffff"):
            """Create QIcon from SVG data"""
            svg_bytes = svg_data.replace("currentColor", color).encode()
            renderer = QSvgRenderer(svg_bytes)
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QP(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
        
        # SVG icon definitions
        svg_folder = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>'
        svg_play = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>'
        svg_pause = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>'
        svg_stop = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h12v12H6z"/></svg>'
        svg_music_note = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>'
        svg_settings = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>'
        
        btn_style = """
            QPushButton {
                background-color: #34495e;
                border: none;
                border-radius: 3px;
                padding: 6px;
                min-width: 27px;
                min-height: 27px;
            }
            QPushButton:hover {
                background-color: #4a5f7f;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """
        
        # File control
        self.btn_open = QPushButton()
        self.btn_open.setIcon(create_svg_icon(svg_folder))
        self.btn_open.setIconSize(QSize(18, 18))
        self.btn_open.clicked.connect(self.open_midi)
        self.btn_open.setStyleSheet(btn_style)
        self.btn_open.setToolTip("Open MIDI file")
        controls_layout.addWidget(self.btn_open)
        
        controls_layout.addSpacing(5)
        
        # Playback controls
        self.btn_play = QPushButton()
        self.btn_play.setIcon(create_svg_icon(svg_play))
        self.btn_play.setIconSize(QSize(18, 18))
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet(btn_style.replace("#34495e", "#27ae60"))
        self.btn_play.setToolTip("Play")
        controls_layout.addWidget(self.btn_play)
        
        self.btn_pause = QPushButton()
        self.btn_pause.setIcon(create_svg_icon(svg_pause))
        self.btn_pause.setIconSize(QSize(18, 18))
        self.btn_pause.clicked.connect(self.pause_playback)
        self.btn_pause.setStyleSheet(btn_style.replace("#34495e", "#f39c12"))
        self.btn_pause.setEnabled(False)
        self.btn_pause.setToolTip("Pause")
        controls_layout.addWidget(self.btn_pause)

        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(create_svg_icon(svg_stop))
        self.btn_stop.setIconSize(QSize(18, 18))
        self.btn_stop.clicked.connect(self.stop_playback)
        self.btn_stop.setStyleSheet(btn_style.replace("#34495e", "#c0392b"))
        self.btn_stop.setToolTip("Stop")
        controls_layout.addWidget(self.btn_stop)
        
        controls_layout.addSpacing(8)
        
        # Train button
        self.btn_train = QPushButton()
        self.btn_train.setIcon(create_svg_icon(svg_music_note))
        self.btn_train.setIconSize(QSize(18, 18))
        self.btn_train.clicked.connect(self.open_train_dialog)
        self.btn_train.setStyleSheet(btn_style.replace("#34495e", "#2980b9"))
        self.btn_train.setToolTip("Training modes")
        controls_layout.addWidget(self.btn_train)
        
        controls_layout.addSpacing(8)
        
        # Clef selector
        self.clef_selector = QComboBox()
        self.clef_selector.addItems([
            "Grand Staff (Sol+Fa)",
            "Treble Clef (Sol)",
            "Bass Clef (Fa)",
            "Alto Clef (Do)",
            "Tenor Clef (Do)",
            "Soprano Clef (Do)",
            "Mezzosoprano Clef (Do)",
            "Baritone Clef (Fa)"
        ])
        self.clef_selector.setCurrentIndex(0)  # Default to Grand Staff
        self.clef_selector.currentIndexChanged.connect(self.change_clef)
        self.clef_selector.setStyleSheet("""
            QComboBox {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 160px;
            }
            QComboBox:hover {
                background-color: #4a5f7f;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2c3e50;
                color: white;
                selection-background-color: #3498db;
            }
        """)
        controls_layout.addWidget(self.clef_selector)
        
        controls_layout.addSpacing(8)
        
        # Sound selector (compact)
        
        controls_layout.addSpacing(8)
        
        # Zoom control (visual speed)
        from PyQt6.QtWidgets import QSlider
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("color: #ecf0f1; font-size: 10px;")
        controls_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(25)  # 25% zoom
        self.zoom_slider.setMaximum(200)  # 200% zoom
        self.zoom_slider.setValue(self.settings.get("visual_zoom", 100))
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.setMaximumWidth(80)
        self.zoom_slider.valueChanged.connect(self.change_zoom)
        self.zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 4px;
                background: #34495e;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #5dade2;
            }
        """)
        controls_layout.addWidget(self.zoom_slider)
        
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setMinimum(25)
        self.zoom_spinbox.setMaximum(200)
        self.zoom_spinbox.setValue(self.settings.get('visual_zoom', 100))
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.setMaximumWidth(60)
        self.zoom_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2980b9;
                border-radius: 3px;
                padding: 2px;
                font-size: 10px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #2980b9;
                border: none;
                width: 12px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #3498db;
            }
        """)
        self.zoom_spinbox.valueChanged.connect(self.on_zoom_spinbox_changed)
        controls_layout.addWidget(self.zoom_spinbox)
        
        controls_layout.addSpacing(8)
        
        # Tempo control (playback speed)
        tempo_label = QLabel("Tempo:")
        tempo_label.setStyleSheet("color: #ecf0f1; font-size: 10px;")
        controls_layout.addWidget(tempo_label)
        
        self.tempo_slider = QSlider(Qt.Orientation.Horizontal)
        self.tempo_slider.setMinimum(25)  # 25% tempo
        self.tempo_slider.setMaximum(200)  # 200% tempo
        self.tempo_slider.setValue(self.settings.get("playback_tempo", 100))
        self.tempo_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.tempo_slider.setTickInterval(25)
        self.tempo_slider.setMaximumWidth(80)
        self.tempo_slider.valueChanged.connect(self.change_tempo)
        self.tempo_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 4px;
                background: #34495e;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #e67e22;
                border: 1px solid #d35400;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #f39c12;
            }
        """)
        controls_layout.addWidget(self.tempo_slider)
        
        self.tempo_spinbox = QSpinBox()
        self.tempo_spinbox.setMinimum(25)
        self.tempo_spinbox.setMaximum(200)
        self.tempo_spinbox.setValue(self.settings.get('playback_tempo', 100))
        self.tempo_spinbox.setSuffix("%")
        self.tempo_spinbox.setMaximumWidth(60)
        self.tempo_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #d35400;
                border-radius: 3px;
                padding: 2px;
                font-size: 10px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #d35400;
                border: none;
                width: 12px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e67e22;
            }
        """)
        self.tempo_spinbox.valueChanged.connect(self.on_tempo_spinbox_changed)
        controls_layout.addWidget(self.tempo_spinbox)
        
        controls_layout.addStretch()
        
        # Current mode indicator (compact)
        self.mode_label = QLabel("▶️ Play")
        self.mode_label.setStyleSheet("color: #ecf0f1; font-size: 11px; font-weight: bold;")
        controls_layout.addWidget(self.mode_label)
        
        controls_layout.addSpacing(10)
        
        # Settings button
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(create_svg_icon(svg_settings))
        self.btn_settings.setIconSize(QSize(18, 18))
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_settings.setStyleSheet(btn_style)
        self.btn_settings.setToolTip("Settings")
        controls_layout.addWidget(self.btn_settings)
        
        controls_layout.addSpacing(8)
        
        # MIDI connection indicator
        self.btn_midi = QPushButton("🎹")
        self.btn_midi.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                border: 2px solid #9b59b6;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 16px;
                min-width: 35px;
                min-height: 27px;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
        """)
        self.btn_midi.setToolTip("MIDI: Mock Mode - Click to select device")
        self.btn_midi.clicked.connect(self.open_midi_selector)
        controls_layout.addWidget(self.btn_midi)
        
        controls_layout.addSpacing(5)
        
        # Arduino connection indicator
        self.btn_arduino = QPushButton("🔌")
        self.btn_arduino.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                border: 2px solid #e74c3c;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 16px;
                min-width: 35px;
                min-height: 27px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        self.btn_arduino.setToolTip("Arduino: Disconnected")
        self.btn_arduino.clicked.connect(self.open_arduino_console)
        controls_layout.addWidget(self.btn_arduino)
        
        # Arduino connection state
        self.arduino_connected = False
        self.arduino_serial = None
        self.arduino_console_dialog = None
        
        # MIDI connection state
        self.midi_connected = False
        self.midi_port = None
        self.midi_device_name = "Mock Mode"
        
        # Add stretch to push controls to the left
        controls_layout.addStretch()
        
        # Status Bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        
        # Start Arduino detection
        QTimer.singleShot(1000, self.detect_arduino_connection)
        
        # Connect Engine Signals
        self.midi_engine.playback_update.connect(self.update_playback_time)
        self.midi_engine.note_on_signal.connect(self.on_playback_note_on)
        self.midi_engine.note_off_signal.connect(self.on_playback_note_off)
        self.midi_engine.practice_finished.connect(self.show_practice_results)
        
        # Connect Staff (Pentagrama) signals - Staff controls playback visuals and sound
        self.score_view.note_triggered.connect(self.on_staff_note_triggered)
        self.score_view.note_ended.connect(self.on_staff_note_ended)
        
        # Initialize Training Mode Manager
        from src.core.training_mode_manager import TrainingModeManager
        self.training_manager = TrainingModeManager(self.midi_engine, self.score_view, self.piano_widget)
        
        # Link training manager to midi_engine
        self.midi_engine.training_manager = self.training_manager
        
        # Connect training manager signals
        self.training_manager.playback_update.connect(self.update_playback_time)
        self.training_manager.note_highlight.connect(self.on_mode_note_highlight)
        self.training_manager.note_unhighlight.connect(self.on_mode_note_unhighlight)
        self.training_manager.play_audio.connect(self.on_mode_play_audio)
        self.training_manager.stop_audio.connect(self.on_mode_stop_audio)
        self.training_manager.mode_message.connect(self.on_mode_message)
        self.training_manager.mode_changed.connect(self.on_mode_changed)
        self.training_manager.song_finished.connect(self.on_song_finished)
        
        # Connect user input (Arduino/Mouse) to training manager
        self.arduino.note_on.connect(self.training_manager.on_user_note_press)
        self.arduino.note_off.connect(self.training_manager.on_user_note_release)
        self.piano_widget.note_pressed.connect(self.training_manager.on_user_note_press)
        self.piano_widget.note_released.connect(self.training_manager.on_user_note_release)
        
        # Track which notes should be active (pressed by user or playing)
        self.expected_active_notes = set()  # Set of MIDI note numbers that should be lit
        
        # Keyboard cleanup timer - removes stuck keys every 100ms
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_orphaned_keys)
        self.cleanup_timer.start(100)  # Run every 100ms

    def open_midi(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open MIDI File", "", "MIDI Files (*.mid *.midi)")
        if file_name:
            self.status_label.setText(f"Loading {os.path.basename(file_name)}...")
            if self.midi_engine.load_midi(file_name):
                # Add to library
                self.song_library.add_song(file_name)
                # Load into staff widget
                self.score_view.load_midi_notes(file_name)
                
                # CRITICAL: Apply current zoom settings after loading MIDI
                visual_zoom = self.settings.get("visual_zoom", 100)
                zoom_scale = visual_zoom / 100.0
                
                # Update zoom slider to show current value (without triggering change event)
                self.zoom_slider.blockSignals(True)
                self.zoom_slider.setValue(int(visual_zoom))
                self.zoom_spinbox.blockSignals(True)
                self.zoom_spinbox.setValue(int(visual_zoom))
                self.zoom_slider.blockSignals(False)
                self.zoom_spinbox.blockSignals(False)
                
                self.score_view.visual_zoom_scale = zoom_scale
                self.score_view.staff_spacing = self.score_view.base_staff_spacing * zoom_scale
                self.score_view.left_margin = int(self.score_view.base_left_margin * zoom_scale)
                
                # Calculate pixels_per_second (for scroll speed only, not note positions)
                # Formula: base * (original_tempo/120) * (tempo_multiplier) * zoom_scale
                original_tempo_factor = self.score_view.tempo_bpm / 120.0
                tempo_multiplier = self.settings.get("playback_tempo", 100) / 100.0
                self.score_view.pixels_per_second = self.score_view.base_pixels_per_second * original_tempo_factor * tempo_multiplier * zoom_scale
                
                # Recalculate Y positions only (for staff display)
                for note in self.score_view.notes:
                    note['y'] = self.score_view.pitch_to_y(note['pitch'])
                
                print(f"StaffWidget: Applied zoom {visual_zoom}% after loading (pixels_per_second={self.score_view.pixels_per_second:.1f})")
                
                # Force repaint to show changes immediately
                self.score_view.update()
                
                # Reset staff triggers for new song
                self.score_view.reset_triggers()
                
                # Set progress bar duration
                if self.midi_engine.events:
                    total_time = max(evt['time'] for evt in self.midi_engine.events)
                    self.progress_bar.set_duration(total_time)
                
                # Check and adapt to piano range
                self.adapt_song_to_piano()
                
                # Sync finger assignments from staff to piano
                self.sync_finger_assignments()
                
                self.song_list.refresh()  # Refresh the library list
                self.status_label.setText(f"Loaded: {os.path.basename(file_name)}")
                self.btn_play.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Failed to load MIDI file.")

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            new_settings = dlg.get_settings()
            self.settings.update(new_settings)
            
            # Save settings to file
            self.save_settings()
            print(f"Settings saved: {self.settings}")
            
            # Update Piano Widget
            self.piano_widget.set_num_keys(self.settings["keys"])
            
            # Apply visual settings to piano
            self.piano_widget.show_note_names = self.settings.get("show_key_labels", True)
            self.piano_widget.show_finger_colors = self.settings.get("show_finger_colors", True)
            self.piano_widget.show_finger_numbers = self.settings.get("show_finger_numbers", True)
            self.piano_widget.show_active_note_colors = self.settings.get("show_active_note_colors", True)
            self.piano_widget.update()
            
            # Apply visual settings to staff
            self.score_view.show_note_colors = self.settings.get("show_staff_note_colors", True)
            
            # Apply played note color to staff
            self.score_view.played_note_color = self.get_played_note_color()
            
            self.score_view.update()
            
            # Apply preparation time to staff (note: requires reloading song to take effect)
            preparation_time = self.settings.get("preparation_time", 3)
            self.score_view.preparation_time = preparation_time
            self.midi_engine.preparation_time = preparation_time
            
            # TODO: Apply settings (e.g. reconnect Arduino if port changed)

    def toggle_play(self):
        """Toggle play/pause for current training mode"""
        if self.training_manager.current_mode and self.training_manager.current_mode.is_active:
            self.pause_playback()
        else:
            # If starting from beginning, ensure position is reset
            if self.midi_engine.paused_at == 0:
                self.score_view.go_to_start()
            
            # Check if Practice mode needs countdown
            mode_name = self.training_manager.get_current_mode_name()
            if mode_name == "Practice":
                # Start countdown for Practice mode, then start when countdown finishes
                self.score_view.start_countdown(lambda: self.start_practice_after_countdown())
                return
            
            # Start the current training mode
            self.training_manager.start()
                        
            # Start the timer for updates
            self.midi_engine.timer.start()
            
            self.btn_play.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.status_label.setText(f"▶ Playing ({mode_name} Mode)")
            self.setWindowTitle(f"How To Piano - ▶ Playing ({mode_name} Mode)")
            
            # Visual feedback - highlight play button
            self.btn_pause.setStyleSheet(self.btn_pause.styleSheet().replace("#f39c12", "#e67e22"))
    
    def pause_playback(self):
        """Pause current training mode"""
        self.training_manager.stop()
        self.midi_engine.timer.stop()
        
        # Clear all highlighted keys when pausing
        self._clear_all_active_notes()
        
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        mode_name = self.training_manager.get_current_mode_name()
        self.status_label.setText(f"⏸ Paused ({mode_name} Mode)")
        self.setWindowTitle(f"How To Piano - ⏸ Paused ({mode_name} Mode)")

    def stop_playback(self):
        """Stop current training mode and reset"""
        # Stop playback logging
        if hasattr(self.score_view, 'stop_playback_logging'):
            self.score_view.stop_playback_logging()
        
        self.training_manager.stop()
        self.midi_engine.timer.stop()
        
        # Reset midi_engine to start position (will be adjusted to negative time in play())
        self.midi_engine.paused_at = 0
        
        # Clear all highlighted keys and stop all sounds
        self._clear_all_active_notes()
        
        self.score_view.go_to_start()  # Reset to start position with preparation time (-prep_time)
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        mode_name = self.training_manager.get_current_mode_name()
        self.status_label.setText(f"⏹ Stopped ({mode_name} Mode)")
        self.setWindowTitle(f"How To Piano - {mode_name} Mode")
    
    def open_train_dialog(self):
        """Open training mode selection dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QButtonGroup
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Training Mode")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("Selecciona un Modo de Entrenamiento")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Mode buttons
        btn_play = QPushButton("Reproducir\nSimplemente reproduce la canción")
        btn_play.setMinimumHeight(60)
        btn_play.setStyleSheet("text-align: left; padding: 10px;")
        btn_play.clicked.connect(lambda: self.select_mode("Play", dialog))
        layout.addWidget(btn_play)
        
        btn_master = QPushButton("Maestro\nMuestra y toca automáticamente")
        btn_master.setMinimumHeight(60)
        btn_master.setStyleSheet("text-align: left; padding: 10px;")
        btn_master.clicked.connect(lambda: self.select_mode("Master", dialog))
        layout.addWidget(btn_master)
        
        btn_student = QPushButton("Estudiante\nPrograma toca 4 acordes, tú los repites")
        btn_student.setMinimumHeight(60)
        btn_student.setStyleSheet("text-align: left; padding: 10px;")
        btn_student.clicked.connect(lambda: self.select_mode("Student", dialog))
        layout.addWidget(btn_student)
        
        btn_practice = QPushButton("Práctica\nIlumina teclas, presiónalas para avanzar")
        btn_practice.setMinimumHeight(60)
        btn_practice.setStyleSheet("text-align: left; padding: 10px;")
        btn_practice.clicked.connect(lambda: self.select_mode("Practice", dialog))
        layout.addWidget(btn_practice)
        
        btn_corrector = QPushButton("Corrector\nCorrige errores anteriores")
        btn_corrector.setMinimumHeight(60)
        btn_corrector.setStyleSheet("text-align: left; padding: 10px;")
        btn_corrector.clicked.connect(lambda: self.select_mode("Corrector", dialog))
        layout.addWidget(btn_corrector)
        
        # Cancel button
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        layout.addWidget(btn_cancel)
        
        dialog.exec()
    
    def select_mode(self, mode, dialog):
        """Set training mode and close dialog"""
        # Switch to the selected mode
        self.training_manager.set_mode(mode)
        
        # Update mode label with icon
        mode_icons = {
            "Play": "▶️",
            "Master": "🎹",
            "Student": "🎓",
            "Practice": "📝",
            "Corrector": "✏️"
        }
        icon = mode_icons.get(mode, "🎵")
        self.mode_label.setText(f"{icon} {mode}")
        self.mode_label.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold; background-color: #34495e; padding: 5px 10px; border-radius: 3px;")
        
        dialog.accept()
        
        # Update status
        self.setWindowTitle(f"How To Piano - {mode} Mode")
        self.status_label.setText(f"Ready - {mode} Mode")
        
        # Note: User must press PLAY button to start - no automatic countdown
    
    def start_practice_after_countdown(self):
        """Called after countdown finishes for Practice mode"""
        # Start Practice mode
        self.training_manager.start()
        
        # Start the timer for updates
        self.midi_engine.timer.start()
        
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.status_label.setText("▶ Playing (Practice Mode)")
        self.setWindowTitle("How To Piano - ▶ Playing (Practice Mode)")
    
    def start_practice_mode(self):
        """Called after countdown finishes (kept for backward compatibility)"""
        self.start_training_mode("Practice")
    
    def start_training_mode(self, mode):
        """Called after countdown finishes for any training mode"""
        self.midi_engine.play()
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.status_label.setText(f"▶ Active - {mode} Mode")
        self.setWindowTitle(f"How To Piano - ▶ {mode} Mode Active")

    def open_midi_selector(self):
        """Open MIDI device selector dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget
        import mido
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select MIDI Input Device")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("Select MIDI Input Device")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Device list
        device_list = QListWidget()
        device_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
            }
        """)
        
        # Add Mock Mode option
        device_list.addItem("🎭 Mock Mode (Demo)")
        
        # Detect MIDI devices
        try:
            input_names = mido.get_input_names()
            if input_names:
                for port_name in input_names:
                    device_list.addItem(f"🎹 {port_name}")
            else:
                info_label = QLabel("No MIDI devices detected")
                info_label.setStyleSheet("color: #95a5a6; font-style: italic;")
                layout.addWidget(info_label)
        except Exception as e:
            error_label = QLabel(f"Error detecting MIDI devices: {e}")
            error_label.setStyleSheet("color: #e74c3c;")
            layout.addWidget(error_label)
        
        layout.addWidget(device_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_select = QPushButton("Select")
        btn_select.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        btn_select.clicked.connect(lambda: self.select_midi_device(device_list.currentItem(), dialog))
        btn_layout.addWidget(btn_select)
        
        layout.addLayout(btn_layout)
        
        # Select current device
        if self.midi_device_name == "Mock Mode":
            device_list.setCurrentRow(0)
        
        dialog.exec()
    
    def select_midi_device(self, item, dialog):
        """Select MIDI device from list"""
        if not item:
            return
        
        device_text = item.text()
        
        if "Mock Mode" in device_text:
            # Switch to mock mode
            self.midi_connected = False
            self.midi_device_name = "Mock Mode"
            self.midi_port = None
            print("✅ Switched to Mock Mode")
            self.update_midi_indicator()
        else:
            # Extract device name (remove emoji)
            device_name = device_text.replace("🎹 ", "")
            
            try:
                # TODO: Connect to actual MIDI device using mido
                # For now, just update the indicator
                self.midi_connected = True
                self.midi_device_name = device_name
                print(f"✅ Selected MIDI device: {device_name}")
                self.update_midi_indicator()
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(dialog, "Error", f"Failed to connect to MIDI device:\n{e}")
                return
        
        dialog.accept()
    
    def update_midi_indicator(self):
        """Update MIDI connection indicator button"""
        if self.midi_connected:
            self.btn_midi.setText("🎹")
            self.btn_midi.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    border: 2px solid #2ecc71;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 16px;
                    min-width: 35px;
                    min-height: 27px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
            self.btn_midi.setToolTip(f"MIDI: {self.midi_device_name} - Click to change")
        else:
            self.btn_midi.setText("🎹")
            self.btn_midi.setStyleSheet("""
                QPushButton {
                    background-color: #8e44ad;
                    border: 2px solid #9b59b6;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 16px;
                    min-width: 35px;
                    min-height: 27px;
                }
                QPushButton:hover {
                    background-color: #9b59b6;
                }
            """)
            self.btn_midi.setToolTip(f"MIDI: {self.midi_device_name} - Click to select device")
    
    def change_sound(self, sound_name):
        # Map names to program numbers (General MIDI)
        sound_map = {
            "Classic Piano": 0,
            "Electric Piano": 4,
            "Organ": 19
        }
        prog = sound_map.get(sound_name, 0)
        self.synth.set_instrument(prog)
    
    def change_clef(self, index):
        """Change musical clef type"""
        clef_types = ["grand", "treble", "bass", "alto", "tenor", "soprano", "mezzosoprano", "baritone"]
        if index < len(clef_types):
            self.score_view.clef_type = clef_types[index]
            # Recalculate note positions for new clef
            if self.score_view.notes:
                for note in self.score_view.notes:
                    note['y'] = self.score_view.pitch_to_y(note['pitch'])
            self.score_view.update()
            print(f"Clef changed to: {clef_types[index]}")
    
    def change_zoom(self, value):
        """Change visual zoom (pixels per second)"""
        self.settings["visual_zoom"] = value
        
        # Update spinbox without triggering another change event
        self.zoom_spinbox.blockSignals(True)
        self.zoom_spinbox.setValue(value)
        self.zoom_spinbox.blockSignals(False)
        
        # Update visual zoom scale for staff appearance
        zoom_scale = value / 100.0
        self.score_view.visual_zoom_scale = zoom_scale
        self.score_view.staff_spacing = self.score_view.base_staff_spacing * zoom_scale
        self.score_view.left_margin = int(self.score_view.base_left_margin * zoom_scale)
        
        # CRITICAL: Update pixels_per_second based on zoom, original tempo, AND tempo multiplier
        # Formula: base * (original_tempo/120) * (tempo_multiplier) * zoom_scale
        # This ensures all three factors are always respected
        base_speed = 100
        original_tempo_factor = self.score_view.tempo_bpm / 120.0
        tempo_multiplier = self.settings.get("playback_tempo", 100) / 100.0
        self.score_view.pixels_per_second = base_speed * original_tempo_factor * tempo_multiplier * zoom_scale
        
        # Recalculate Y positions if a song is loaded (for staff display)
        if self.score_view.notes:
            for note in self.score_view.notes:
                # Recalculate y position with new staff spacing
                note['y'] = self.score_view.pitch_to_y(note['pitch'])
            
            # Reset trigger state to prevent skipping notes
            self.score_view.reset_triggers()
            
            self.score_view.update()
        
        # Save settings
        self.save_settings()
        tempo_mult = self.settings.get("playback_tempo", 100)
        print(f"Visual zoom changed to {value}% (scroll speed: {self.score_view.pixels_per_second:.1f} px/s, tempo: {tempo_mult}%)")
    
    def change_tempo(self, value):
        """Change playback tempo (actual speed of music)"""
        self.settings["playback_tempo"] = value
        
        # Update spinbox without triggering another change event
        self.tempo_spinbox.blockSignals(True)
        self.tempo_spinbox.setValue(value)
        self.tempo_spinbox.blockSignals(False)
        
        # Update the tempo multiplier in training modes
        if self.training_manager:
            for mode in self.training_manager.modes.values():
                mode.tempo_multiplier = value / 100.0
        
        # CRITICAL: Update scroll speed based on new tempo
        # Formula: pixels_per_second = base * (original_tempo/120) * (tempo_multiplier) * zoom_scale
        # Example: Song at 90 BPM, tempo slider 50%, zoom 100%
        #   -> pixels_per_second = 100 * (90/120) * 0.5 * 1.0 = 37.5 px/s
        original_tempo_factor = self.score_view.tempo_bpm / 120.0
        tempo_multiplier = value / 100.0
        self.score_view.pixels_per_second = self.score_view.base_pixels_per_second * original_tempo_factor * tempo_multiplier * self.score_view.visual_zoom_scale
        
        # Reset trigger state when tempo changes
        if self.score_view.notes:
            self.score_view.update()
        
        # CRITICAL: Reset trigger state to prevent skipping notes
        self.score_view.reset_triggers()
        
        # Save settings
        self.save_settings()
        print(f"Playback tempo changed to {value}% (scroll speed: {self.score_view.pixels_per_second:.1f} px/s)")

    def on_zoom_spinbox_changed(self, value):
        """Handle zoom spinbox value changes"""
        # Update slider without triggering another change event
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(value)
        self.zoom_slider.blockSignals(False)
        
        # Apply the zoom change
        self.change_zoom(value)
    
    def on_tempo_spinbox_changed(self, value):
        """Handle tempo spinbox value changes"""
        # Update slider without triggering another change event
        self.tempo_slider.blockSignals(True)
        self.tempo_slider.setValue(value)
        self.tempo_slider.blockSignals(False)
        
        # Apply the tempo change
        self.change_tempo(value)
    
    def load_song_from_library(self, song_id, path):
        """Load a song from the library"""
        print(f"MainWindow: Loading song_id={song_id}, path={path}")
        song = self.song_library.get_song_by_id(song_id)
        if song:
            # Use the path from the song metadata, not the signal parameter
            actual_path = song['path']
            print(f"MainWindow: Using actual path: {actual_path}")
            self.status_label.setText(f"Loading {song['name']}...")
            if os.path.exists(actual_path):
                if self.midi_engine.load_midi(actual_path):
                    self.score_view.load_midi_notes(actual_path)
                    
                    # CRITICAL: Apply current zoom settings after loading MIDI
                    # This ensures tempo calculation includes the correct zoom factor
                    visual_zoom = self.settings.get("visual_zoom", 100)
                    zoom_scale = visual_zoom / 100.0
                    
                    # Update zoom slider to show current value (without triggering change event)
                    self.zoom_slider.blockSignals(True)
                    self.zoom_slider.setValue(int(visual_zoom))
                    self.zoom_spinbox.blockSignals(True)
                    self.zoom_spinbox.setValue(int(visual_zoom))
                    self.zoom_slider.blockSignals(False)
                    self.zoom_spinbox.blockSignals(False)
                    
                    self.score_view.visual_zoom_scale = zoom_scale
                    self.score_view.staff_spacing = self.score_view.base_staff_spacing * zoom_scale
                    self.score_view.left_margin = int(self.score_view.base_left_margin * zoom_scale)
                    
                    # Recalculate pixels_per_second with correct zoom AND tempo multiplier
                    # Formula: base * (original_tempo/120) * (tempo_multiplier) * zoom_scale
                    original_tempo_factor = self.score_view.tempo_bpm / 120.0
                    tempo_multiplier = self.settings.get("playback_tempo", 100) / 100.0
                    self.score_view.pixels_per_second = self.score_view.base_pixels_per_second * original_tempo_factor * tempo_multiplier * zoom_scale
                    
                    # Recalculate Y positions only (for staff display)
                    for note in self.score_view.notes:
                        note['y'] = self.score_view.pitch_to_y(note['pitch'])
                    
                    print(f"StaffWidget: Applied zoom {visual_zoom}% after loading (pixels_per_second={self.score_view.pixels_per_second:.1f})")
                    
                    # Force repaint to show changes immediately
                    self.score_view.update()
                    
                    # Set progress bar duration
                    if self.midi_engine.events:
                        total_time = max(evt['time'] for evt in self.midi_engine.events)
                        self.progress_bar.set_duration(total_time)
                    
                    # Check and adapt to piano range
                    self.adapt_song_to_piano()
                    
                    # Sync finger assignments from staff to piano
                    self.sync_finger_assignments()
                    
                    self.status_label.setText(f"{song['name']}")
                    self.btn_play.setEnabled(True)
                    
                    # Reset to start position LAST - after all other operations
                    # Use QTimer to ensure it happens after all pending UI updates
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(50, self.score_view.go_to_start)
                else:
                    QMessageBox.critical(self, "Error", "Failed to load song.")
            else:
                QMessageBox.critical(self, "Error", f"Song file not found: {actual_path}")
    
    def update_playback_time(self, time_sec):
        # Update progress bar and score
        self.progress_bar.set_time(time_sec)
        self.score_view.set_playback_time(time_sec)
    
    def seek_to_time(self, time_sec):
        """Seek to specific time in song"""
        # Reset staff triggers when seeking
        self.score_view.reset_triggers()
        
        if hasattr(self.midi_engine, 'seek'):
            self.midi_engine.seek(time_sec)
        else:
            # Simple seek by stopping and adjusting
            was_playing = self.midi_engine.is_playing
            self.midi_engine.stop()
            self.midi_engine.paused_at = time_sec
            if was_playing:
                self.midi_engine.play()

    def _activate_piano_key(self, pitch, velocity, color=None, play_audio=True):
        """Centralized method to activate a piano key with visual and audio"""
        # Register as expected active note
        self.expected_active_notes.add(pitch)
        
        # Play audio if requested
        if play_audio:
            def play_note_async():
                self.midi_engine.synth.note_on(pitch, velocity)
                if self.midi_engine.audio_type in ['maestro', 'pygame']:
                    self.midi_engine._play_note_pygame(pitch, velocity)
            threading.Thread(target=play_note_async, daemon=True).start()
        
        # Visual feedback
        if color is None:
            color = self.get_played_note_color()
        self.piano_widget.note_on(pitch, color)
        self.score_view.note_on(pitch)
    
    def _deactivate_piano_key(self, pitch, stop_audio=True):
        """Centralized method to deactivate a piano key with visual and audio"""
        # Unregister from expected active notes
        self.expected_active_notes.discard(pitch)
        
        # Stop audio if requested
        if stop_audio:
            def stop_note_async():
                self.midi_engine.synth.note_off(pitch)
                if self.midi_engine.audio_type in ['maestro', 'pygame']:
                    self.midi_engine._stop_note_pygame(pitch)
            threading.Thread(target=stop_note_async, daemon=True).start()
        
        # Visual feedback
        self.piano_widget.note_off(pitch)
        self.score_view.note_off(pitch)
    
    def on_staff_note_triggered(self, pitch, velocity):
        """Called when a note crosses the red line on the staff"""
        # In Practice mode, NEVER auto-play - user must press keys manually
        should_play = True
        if hasattr(self, 'training_manager'):
            mode_name = self.training_manager.get_current_mode_name()
            if mode_name == 'Practice':
                should_play = False  # Show visual but no audio
        
        self._activate_piano_key(pitch, velocity, play_audio=should_play)
    
    def on_staff_note_ended(self, pitch):
        """Called when a note ends (crosses red line + duration)"""
        # In Practice mode, don't auto-stop - user controls audio
        should_stop = True
        if hasattr(self, 'training_manager'):
            mode_name = self.training_manager.get_current_mode_name()
            if mode_name == 'Practice':
                should_stop = False  # User controls when to stop
        
        self._deactivate_piano_key(pitch, stop_audio=should_stop)
    
    def on_playback_note_on(self, note, velocity):
        """Called when the MIDI file plays a note"""
        self._activate_piano_key(note, velocity, play_audio=False)
        
    def on_playback_note_off(self, note):
        """Called when the MIDI file stops a note"""
        self._deactivate_piano_key(note, stop_audio=False)
    
    def on_arduino_note_on(self, note, velocity):
        """Called when Arduino detects a note press"""
        self._activate_piano_key(note, velocity, QColor(255, 140, 0), play_audio=False)
    
    def on_arduino_note_off(self, note):
        """Called when Arduino detects a note release"""
        self._deactivate_piano_key(note, stop_audio=False)
    
    def on_user_note_pressed(self, note, velocity):
        """Called when user clicks piano key"""
        self._activate_piano_key(note, velocity, QColor(255, 140, 0), play_audio=False)
    
    def on_user_note_released(self, note):
        """Called when user releases piano key"""
        self._deactivate_piano_key(note, stop_audio=False)

    def adapt_song_to_piano(self):
        """Keep piano size fixed according to settings (no adaptation)"""
        # Piano keeps the configured number of keys from settings
        # No automatic expansion based on song range
        pass
    
    def sync_finger_assignments(self):
        """Sync finger assignments from staff to piano widget"""
        self.piano_widget.clear_finger_assignments()
        
        # Get unique pitches and their assigned fingers from the staff
        pitch_to_finger = {}
        for note in self.score_view.notes:
            pitch = note['pitch']
            note_id = note['id']
            finger = self.score_view.get_finger_for_note(note_id)
            
            # Use the first finger assignment we see for each pitch
            if pitch not in pitch_to_finger:
                pitch_to_finger[pitch] = finger
        
        # Apply to piano widget
        for pitch, finger in pitch_to_finger.items():
            self.piano_widget.set_finger_assignment(pitch, finger)
        
        print(f"MainWindow: Synced {len(pitch_to_finger)} finger assignments to piano")
    
    def show_practice_results(self, evaluation):
        """Show practice results dialog with star rating"""
        from src.ui.results_dialog import ResultsDialog
        
        results_dlg = ResultsDialog(evaluation, self)
        if results_dlg.exec():
            # User clicked "Try Again"
            self.stop_playback()
            self.score_view.set_playback_time(0)
            self.toggle_play()  # Restart in current mode
        else:
            # User clicked "Done"
            self.training_manager.set_mode("Master")
            self.mode_label.setText("🎹 Master")
            self.setWindowTitle("How To Piano")
    
    def on_mode_note_highlight(self, pitch, color):
        """Training mode wants to highlight a piano key"""
        self._activate_piano_key(pitch, 80, color, play_audio=False)
    
    def on_mode_note_unhighlight(self, pitch):
        """Training mode wants to unhighlight a piano key"""
        self._deactivate_piano_key(pitch, stop_audio=False)
    
    def on_mode_play_audio(self, pitch, velocity):
        """Training mode wants to play audio"""
        import threading
        def play_async():
            self.midi_engine.synth.note_on(pitch, velocity)
            if self.midi_engine.audio_type in ['maestro', 'pygame']:
                self.midi_engine._play_note_pygame(pitch, velocity)
        threading.Thread(target=play_async, daemon=True).start()
    
    def on_mode_stop_audio(self, pitch):
        """Training mode wants to stop audio"""
        import threading
        def stop_async():
            self.midi_engine.synth.note_off(pitch)
            if self.midi_engine.audio_type in ['maestro', 'pygame']:
                self.midi_engine._stop_note_pygame(pitch)
        threading.Thread(target=stop_async, daemon=True).start()
    
    def on_mode_message(self, message):
        """Training mode sends status message"""
        self.status_label.setText(message)
    
    def on_mode_changed(self, mode_name):
        """Training mode changed"""
        print(f"MainWindow: Training mode changed to {mode_name}")
    
    def on_song_finished(self):
        """Called when song finishes playing - wait 3 seconds before stopping to let last note fade"""
        print("MainWindow: Song finished, waiting 3 seconds for last note to fade...")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, self.stop_playback)  # Wait 3 seconds before stopping
    
    def _clear_all_active_notes(self):
        """Clear all highlighted keys and stop all sounds"""
        
        # Clear staff widget active notes first
        if hasattr(self.score_view, 'active_note_ids'):
            self.score_view.active_note_ids.clear()
        
        # Clear piano widget active notes
        if hasattr(self.piano_widget, 'active_notes'):
            self.piano_widget.active_notes.clear()
        
        # Clear expected active notes
        self.expected_active_notes.clear()
        
        # Turn off all piano keys (88 keys from MIDI 21 to 108)
        for note in range(21, 109):
            self.piano_widget.note_off(note)
            self.score_view.note_off(note)
            
            # Stop audio for each note
            def stop_async(pitch):
                try:
                    self.midi_engine.synth.note_off(pitch)
                    if self.midi_engine.audio_type in ['maestro', 'pygame']:
                        self.midi_engine._stop_note_pygame(pitch)
                except Exception as e:
                    pass  # Ignore errors for notes that weren't playing
            
            threading.Thread(target=lambda n=note: stop_async(n), daemon=True).start()
        
        # Also stop maestro sampler if available
        if hasattr(self.midi_engine, 'maestro_sampler') and self.midi_engine.maestro_sampler:
            try:
                self.midi_engine.maestro_sampler.stop_all()
            except Exception as e:
                print(f"Error stopping maestro sampler: {e}")
        
        # Force UI update
        self.piano_widget.update()
        self.score_view.update()
    
    def _cleanup_orphaned_keys(self):
        """Remove stuck keys that shouldn't be active (runs every 100ms)"""
        # Get currently active notes from piano widget
        if not hasattr(self.piano_widget, 'active_notes'):
            return
        
        current_active = set(self.piano_widget.active_notes.keys())
        
        # Find notes that are active but shouldn't be
        orphaned_notes = current_active - self.expected_active_notes
        
        if orphaned_notes:
            # Clean up orphaned keys
            for note in orphaned_notes:
                self.piano_widget.note_off(note)
                self.score_view.note_off(note)
                
                # Stop audio
                try:
                    self.midi_engine.synth.note_off(note)
                    if self.midi_engine.audio_type in ['maestro', 'pygame']:
                        self.midi_engine._stop_note_pygame(note)
                except Exception as e:
                    pass
            
            # Update display
            self.piano_widget.update()
    
    def get_played_note_color(self):
        """Get played note color from settings as QColor"""
        color_data = self.settings.get("played_note_color", [0, 120, 255])
        return QColor(color_data[0], color_data[1], color_data[2])
    
    def load_settings(self):
        """Load settings from file or return defaults"""
        default_settings = {
            "keys": 88,
            "port": "COM3",
            "start_key": "A0 (21)",
            "show_key_labels": True,
            "show_finger_colors": True,
            "show_finger_numbers": True,
            "show_active_note_colors": True,
            "sound": "Classic Piano",
            "volume": 80,
            "metronome_volume": 50,
            "audio_latency": 50,
            "preparation_time": 3,
            "wait_time": 10,
            "show_hints": True,
            "auto_pause": False,
            "show_mistakes": True,
            "repeat_section": False,
            "practice_tempo": 75,
            "baud_rate": 9600,
            "auto_reconnect": True,
            "played_note_color": [0, 120, 255],  # Electric blue default
            "visual_zoom": 100,  # Default 100% zoom
            "playback_tempo": 100  # Default 100% tempo
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
                    print(f"Settings loaded from {self.settings_file}")
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return default_settings
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def detect_arduino_connection(self):
        """Detect Arduino connection automatically"""
        print("\n🔍 Detecting Arduino connection...")
        
        # Try to get saved port from settings first
        saved_port = self.settings.get("ledteacher_port", None)
        
        if saved_port and saved_port != "None":
            print(f"  Trying saved port: {saved_port}")
            if self.try_connect_arduino(saved_port):
                return
        
        # Auto-detect Arduino ports
        ports = serial.tools.list_ports.comports()
        arduino_keywords = ['arduino', 'ch340', 'ch341', 'cp210', 'ftdi', 'usb-serial']
        
        for port in ports:
            port_desc = port.description.lower()
            if any(keyword in port_desc for keyword in arduino_keywords):
                print(f"  Found potential Arduino: {port.device} - {port.description}")
                if self.try_connect_arduino(port.device):
                    return
        
        print("  ❌ No Arduino detected")
    
    def try_connect_arduino(self, port):
        """Try to connect to Arduino on specified port"""
        try:
            print(f"    Opening {port}...")
            ser = serial.Serial(port, 115200, timeout=0.1)
            time.sleep(2)  # Wait for Arduino reset
            
            # Check if Arduino responds
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"    Response: {response}")
                
                if response == "READY":
                    print(f"    ✅ Arduino connected on {port}!")
                    self.arduino_serial = ser
                    self.arduino_connected = True
                    self.update_arduino_indicator()
                    return True
            
            # Send PING to check connection
            ser.write(b"PING\\n")
            time.sleep(0.1)
            
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"    Response: {response}")
                
                if "PONG" in response or "READY" in response:
                    print(f"    ✅ Arduino connected on {port}!")
                    self.arduino_serial = ser
                    self.arduino_connected = True
                    self.update_arduino_indicator()
                    return True
            
            ser.close()
            print(f"    ❌ No valid response from {port}")
            
        except Exception as e:
            print(f"    ❌ Error connecting to {port}: {e}")
        
        return False
    
    def update_arduino_indicator(self):
        """Update Arduino connection indicator button"""
        if self.arduino_connected:
            self.btn_arduino.setText("\ud83d\udd0c")
            self.btn_arduino.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    border: 2px solid #2ecc71;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 16px;
                    min-width: 35px;
                    min-height: 27px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
            self.btn_arduino.setToolTip("Arduino: Connected - Click to open console")
        else:
            self.btn_arduino.setText("\ud83d\udd0c")
            self.btn_arduino.setStyleSheet("""
                QPushButton {
                    background-color: #c0392b;
                    border: 2px solid #e74c3c;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 16px;
                    min-width: 35px;
                    min-height: 27px;
                }
                QPushButton:hover {
                    background-color: #e74c3c;
                }
            """)
            self.btn_arduino.setToolTip("Arduino: Disconnected")
    
    def send_arduino_led_on(self, midi_note, velocity=100):
        """Send LED ON command to Arduino when piano key is pressed"""
        if not self.arduino_connected or not self.arduino_serial:
            return
        
        try:
            command = f"ON:{midi_note}:{velocity}\\n"
            self.arduino_serial.write(command.encode())
            
            # Log to console if open
            if self.arduino_console_dialog and self.arduino_console_dialog.isVisible():
                self.arduino_console_dialog.log_sent(command.strip())
                
                # Read response
                time.sleep(0.01)
                if self.arduino_serial.in_waiting > 0:
                    response = self.arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        self.arduino_console_dialog.log_received(response)
        
        except Exception as e:
            print(f"Error sending LED ON: {e}")
            self.arduino_connected = False
            self.update_arduino_indicator()
    
    def send_arduino_led_off(self, midi_note):
        """Send LED OFF command to Arduino when piano key is released"""
        if not self.arduino_connected or not self.arduino_serial:
            return
        
        try:
            command = f"OFF:{midi_note}\\n"
            self.arduino_serial.write(command.encode())
            
            # Log to console if open
            if self.arduino_console_dialog and self.arduino_console_dialog.isVisible():
                self.arduino_console_dialog.log_sent(command.strip())
                
                # Read response
                time.sleep(0.01)
                if self.arduino_serial.in_waiting > 0:
                    response = self.arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        self.arduino_console_dialog.log_received(response)
        
        except Exception as e:
            print(f"Error sending LED OFF: {e}")
            self.arduino_connected = False
            self.update_arduino_indicator()
    
    def open_arduino_console(self):
        """Open Arduino console dialog"""
        if not self.arduino_connected:
            QMessageBox.warning(self, "Arduino Not Connected", 
                              "Arduino is not connected. Please check connection in Settings.")
            return
        
        if self.arduino_console_dialog is None:
            self.arduino_console_dialog = ArduinoConsoleDialog(self.arduino_serial, self)
        
        self.arduino_console_dialog.show()
        self.arduino_console_dialog.raise_()
        self.arduino_console_dialog.activateWindow()
    
    def closeEvent(self, event):
        """Clean shutdown of all components"""
        print("🛑 Cerrando aplicación...")
        
        try:
            # 1. Stop MIDI playback
            if hasattr(self, 'midi_engine') and self.midi_engine:
                print("  - Deteniendo MIDI engine...")
                self.midi_engine.stop()
                self.midi_engine.cleanup()
            
            # 2. Stop all audio
            if hasattr(self, 'synth') and self.synth:
                print("  - Deteniendo sintetizador...")
                self.synth.all_notes_off()
                self.synth.cleanup()
            
            # 3. Stop Arduino thread
            if hasattr(self, 'arduino') and self.arduino:
                print("  - Deteniendo Arduino...")
                self.arduino.stop()
            
            if hasattr(self, 'arduino_thread') and self.arduino_thread:
                self.arduino_thread.quit()
                self.arduino_thread.wait(1000)  # Wait max 1 second
            
            # 4. Save settings
            self.save_settings()
            print("✅ Aplicación cerrada correctamente")
            
        except Exception as e:
            print(f"⚠️ Error al cerrar: {e}")
        finally:
            event.accept()
        """Clean shutdown of all components"""
        print("🛑 Cerrando aplicación...")
        
        try:
            # 1. Stop MIDI playback
            if hasattr(self, 'midi_engine') and self.midi_engine:
                print("  - Deteniendo MIDI engine...")
                self.midi_engine.stop()
                self.midi_engine.cleanup()
            
            # 2. Stop all audio
            if hasattr(self, 'synth') and self.synth:
                print("  - Deteniendo sintetizador...")
                self.synth.all_notes_off()
                self.synth.cleanup()
            
            # 3. Stop Arduino thread
            if hasattr(self, 'arduino') and self.arduino:
                print("  - Deteniendo Arduino...")
                self.arduino.stop()
            
            if hasattr(self, 'arduino_thread') and self.arduino_thread:
                self.arduino_thread.quit()
                self.arduino_thread.wait(1000)  # Wait max 1 second
            
            # 4. Close Arduino connection
            if hasattr(self, 'arduino_serial') and self.arduino_serial:
                print("  - Cerrando conexión Arduino...")
                try:
                    self.arduino_serial.close()
                except:
                    pass
            
            # 5. Save settings
            self.save_settings()
            print("✅ Aplicación cerrada correctamente")
            
        except Exception as e:
            print(f"⚠️ Error al cerrar: {e}")
        finally:
            event.accept()


class ArduinoConsoleDialog(QDialog):
    """Console dialog for monitoring Arduino LED commands"""
    
    def __init__(self, serial_port, parent=None):
        super().__init__(parent)
        self.serial_port = serial_port
        self.setWindowTitle("Arduino LED Console")
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🔌 Arduino LED Console - Real-time Monitoring")
        title.setStyleSheet("""
            color: #2ecc71;
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            background-color: #1e1e1e;
            border-bottom: 2px solid #27ae60;
        """)
        layout.addWidget(title)
        
        # Console output
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.console)
        
        # Info label
        info = QLabel("💡 Press piano keys to see LED commands in real-time")
        info.setStyleSheet("""
            color: #8b949e;
            font-size: 10px;
            padding: 5px;
            background-color: #161b22;
        """)
        layout.addWidget(info)
        
        # Button row
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Clear Console")
        clear_btn.clicked.connect(self.console.clear)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
        """)
        btn_layout.addWidget(clear_btn)
        
        test_btn = QPushButton("🎵 Test C Major Scale")
        test_btn.clicked.connect(self.test_scale)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #388bfd;
            }
        """)
        btn_layout.addWidget(test_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("✖ Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #da3633;
                color: white;
            }
        """)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Initial message
        self.console.append("<span style='color: #58a6ff;'>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>")
        self.console.append("<span style='color: #2ecc71; font-weight: bold;'>✓ Arduino Connected</span>")
        self.console.append("<span style='color: #8b949e;'>Monitoring LED commands...</span>")
        self.console.append("<span style='color: #58a6ff;'>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>")
        self.console.append("")
    
    def log_sent(self, command):
        """Log sent command"""
        timestamp = time.strftime("%H:%M:%S")
        self.console.append(f"<span style='color: #8b949e;'>[{timestamp}]</span> "
                          f"<span style='color: #79c0ff; font-weight: bold;'>➤</span> "
                          f"<span style='color: #79c0ff;'>{command}</span>")
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )
    
    def log_received(self, response):
        """Log received response"""
        timestamp = time.strftime("%H:%M:%S")
        self.console.append(f"<span style='color: #8b949e;'>[{timestamp}]</span> "
                          f"<span style='color: #2ecc71; font-weight: bold;'>◄</span> "
                          f"<span style='color: #2ecc71;'>{response}</span>")
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )
    
    def test_scale(self):
        """Test C major scale"""
        if not self.serial_port:
            return
        
        self.console.append("")
        self.console.append("<span style='color: #f0883e; font-weight: bold;'>🎵 Testing C Major Scale...</span>")
        
        # C major scale: C4-C5 (60-72)
        notes = [60, 62, 64, 65, 67, 69, 71, 72]
        note_names = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
        
        try:
            for note, name in zip(notes, note_names):
                # ON
                command = f"ON:{note}:100"
                self.serial_port.write((command + "\n").encode())
                self.log_sent(command)
                
                time.sleep(0.05)
                if self.serial_port.in_waiting > 0:
                    response = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        self.log_received(response)
                
                time.sleep(0.3)
                
                # OFF
                command = f"OFF:{note}"
                self.serial_port.write((command + "\n").encode())
                self.log_sent(command)
                
                time.sleep(0.05)
                if self.serial_port.in_waiting > 0:
                    response = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        self.log_received(response)
                
                time.sleep(0.1)
            
            self.console.append("<span style='color: #2ecc71; font-weight: bold;'>✓ Test completed</span>")
            self.console.append("")
            
        except Exception as e:
            self.console.append(f"<span style='color: #f85149;'>❌ Error: {e}</span>")
            self.console.append("")
