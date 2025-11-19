import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QThread, QSize

from src.core.arduino_conn import ArduinoWorker
from src.core.synth import PianoSynth
from src.core.midi_engine import MidiEngine
from src.ui.score_view import SongLibrary
from src.ui.staff_widget import StaffWidget
from src.ui.settings_dialog import SettingsDialog
from src.ui.piano_widget import PianoWidget
from src.ui.song_list_widget import SongListWidget
from PyQt6.QtGui import QColor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("How To Piano")
        self.resize(1200, 900)
        
        # Default Settings
        self.settings = {
            "keys": 88,
            "port": "COM3"
        }

        # Initialize Core Components
        # Try to find a soundfont in assets
        sf_path = os.path.join(os.getcwd(), "assets", "soundfonts", "default.sf2")
        if not os.path.exists(sf_path):
            # Fallback or ask user? For now just warn
            print("No default soundfont found.")
        
        self.synth = PianoSynth(sf_path)
        self.midi_engine = MidiEngine(self.synth)
        
        # Initialize Song Library
        self.song_library = SongLibrary()
        
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
        
        # Piano Widget (Piano - bottom, full width at bottom of entire window)
        self.piano_widget = PianoWidget(num_keys=self.settings["keys"])
        self.piano_widget.setMinimumHeight(100)
        self.piano_widget.setMaximumHeight(150)
        main_v_layout.addWidget(self.piano_widget)

        # Arduino (Mock by default for safety, user can configure)
        self.arduino = ArduinoWorker(port="COM3", mock=True)
        self.arduino_thread = QThread()
        self.arduino.moveToThread(self.arduino_thread)
        self.arduino_thread.started.connect(self.arduino.run)
        
        # Connect Arduino -> MidiEngine
        self.arduino.note_on.connect(self.midi_engine.on_user_note_on)
        self.arduino.note_off.connect(self.midi_engine.on_user_note_off)
        
        # Connect Arduino -> PianoWidget (Visual Feedback)
        self.arduino.note_on.connect(lambda n, v: self.piano_widget.note_on(n, QColor("green")))
        self.arduino.note_off.connect(lambda n: self.piano_widget.note_off(n))
        
        # Connect PianoWidget Mouse -> MidiEngine (Interactive Piano)
        self.piano_widget.note_pressed.connect(self.midi_engine.on_user_note_on)
        self.piano_widget.note_released.connect(self.midi_engine.on_user_note_off)
        
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
        svg_school = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/></svg>'
        svg_settings = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>'
        
        btn_style = """
            QPushButton {
                background-color: #34495e;
                border: none;
                border-radius: 3px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
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
        self.btn_train.setIcon(create_svg_icon(svg_school))
        self.btn_train.setIconSize(QSize(18, 18))
        self.btn_train.clicked.connect(self.open_train_dialog)
        self.btn_train.setStyleSheet(btn_style.replace("#34495e", "#2980b9"))
        self.btn_train.setToolTip("Training modes")
        controls_layout.addWidget(self.btn_train)
        
        controls_layout.addSpacing(10)
        
        # MIDI Input selector
        self.midi_input_selector = QComboBox()
        self.midi_input_selector.currentTextChanged.connect(self.change_midi_input)
        self.midi_input_selector.setStyleSheet("""
            QComboBox {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 140px;
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
        controls_layout.addWidget(self.midi_input_selector)
        self.refresh_midi_inputs()
        
        controls_layout.addSpacing(8)
        
        # Sound selector (compact)
        self.sound_selector = QComboBox()
        self.sound_selector.addItems(["Classic Piano", "Electric Piano", "Organ"])
        self.sound_selector.currentTextChanged.connect(self.change_sound)
        self.sound_selector.setStyleSheet("""
            QComboBox {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 120px;
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
        controls_layout.addWidget(self.sound_selector)
        
        controls_layout.addStretch()
        
        # Current mode indicator (compact)
        self.mode_label = QLabel("Master Mode")
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
        
        # Add stretch to push controls to the left
        controls_layout.addStretch()
        
        # Status Bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        
        # Connect Engine Signals
        self.midi_engine.playback_update.connect(self.update_playback_time)
        self.midi_engine.note_on_signal.connect(self.on_playback_note_on)
        self.midi_engine.note_off_signal.connect(self.on_playback_note_off)
        self.midi_engine.practice_finished.connect(self.show_practice_results)

    def open_midi(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open MIDI File", "", "MIDI Files (*.mid *.midi)")
        if file_name:
            self.status_label.setText(f"Loading {os.path.basename(file_name)}...")
            if self.midi_engine.load_midi(file_name):
                # Add to library
                self.song_library.add_song(file_name)
                # Load into staff widget
                self.score_view.load_midi_notes(file_name)
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
            print(f"New Settings: {self.settings}")
            
            # Update Piano Widget
            self.piano_widget.set_num_keys(self.settings["keys"])
            
            # TODO: Apply settings (e.g. reconnect Arduino if port changed)

    def toggle_play(self):
        if self.midi_engine.is_playing:
            self.pause_playback()
        else:
            self.midi_engine.play()
            self.btn_play.setEnabled(False)
            self.btn_pause.setEnabled(True)
            mode_name = self.midi_engine.mode
            self.status_label.setText(f"▶ Playing ({mode_name} Mode)")
            self.setWindowTitle(f"How To Piano - ▶ Playing ({mode_name} Mode)")
            
            # Visual feedback - highlight play button
            self.btn_pause.setStyleSheet(self.btn_pause.styleSheet().replace("#f39c12", "#e67e22"))
    
    def pause_playback(self):
        self.midi_engine.pause()
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        mode_name = self.midi_engine.mode
        self.status_label.setText(f"⏸ Paused ({mode_name} Mode)")
        self.setWindowTitle(f"How To Piano - ⏸ Paused ({mode_name} Mode)")

    def stop_playback(self):
        self.midi_engine.stop()
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        mode_name = self.midi_engine.mode
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
        self.midi_engine.mode = mode
        
        # Update mode label with icon
        mode_icons = {
            "Master": "🎹",
            "Student": "🎓",
            "Practice": "📝",
            "Corrector": "✏️"
        }
        icon = mode_icons.get(mode, "🎵")
        self.mode_label.setText(f"{icon} {mode}")
        self.mode_label.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold; background-color: #34495e; padding: 5px 10px; border-radius: 3px;")
        
        dialog.accept()
        
        # Start countdown for all practice modes (Student, Practice, Corrector)
        if mode in ["Student", "Practice", "Corrector"]:
            self.score_view.start_countdown(callback=lambda: self.start_training_mode(mode))
        else:
            # Master mode - just update status
            self.setWindowTitle(f"How To Piano - {mode} Mode")
            self.status_label.setText(f"Ready - {mode} Mode")
    
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

    def refresh_midi_inputs(self):
        """Detect and list available MIDI input devices"""
        import mido
        
        self.midi_input_selector.clear()
        
        # Add mock mode option
        self.midi_input_selector.addItem("Mock Mode (Demo)")
        
        # Get available MIDI input ports
        try:
            input_names = mido.get_input_names()
            if input_names:
                for port_name in input_names:
                    self.midi_input_selector.addItem(port_name)
            else:
                self.midi_input_selector.addItem("No MIDI devices found")
        except Exception as e:
            print(f"Error detecting MIDI devices: {e}")
            self.midi_input_selector.addItem("Error detecting devices")
        
        # Set mock mode as default
        self.midi_input_selector.setCurrentIndex(0)
    
    def change_midi_input(self, device_name):
        """Change MIDI input device"""
        if not device_name or "Mock Mode" in device_name:
            # Switch to mock mode
            print("Switching to Mock Mode")
            # TODO: Restart Arduino worker with mock=True
            self.setWindowTitle(f"How To Piano - MIDI: Mock Mode")
        elif "No MIDI" in device_name or "Error" in device_name:
            return
        else:
            # Real MIDI device selected
            print(f"Selected MIDI device: {device_name}")
            # TODO: Connect to actual MIDI device using mido
            self.setWindowTitle(f"How To Piano - MIDI: {device_name}")
    
    def change_sound(self, sound_name):
        # Map names to program numbers (General MIDI)
        sound_map = {
            "Classic Piano": 0,
            "Electric Piano": 4,
            "Organ": 19
        }
        prog = sound_map.get(sound_name, 0)
        self.synth.set_instrument(prog)

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
                    self.status_label.setText(f"{song['name']}")
                    self.btn_play.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Failed to load song.")
            else:
                QMessageBox.critical(self, "Error", f"Song file not found: {actual_path}")
    
    def update_playback_time(self, time_sec):
        # Update status or scroll score
        # self.status_label.setText(f"Time: {time_sec:.1f}s")
        self.score_view.set_playback_time(time_sec)

    def on_playback_note_on(self, note, velocity):
        # Called when the MIDI file plays a note
        self.piano_widget.note_on(note, QColor("blue"))
        self.score_view.note_on(note)
        
    def on_playback_note_off(self, note):
        self.piano_widget.note_off(note)
        self.score_view.note_off(note)

    def show_practice_results(self, evaluation):
        """Show practice results dialog with star rating"""
        from src.ui.results_dialog import ResultsDialog
        
        results_dlg = ResultsDialog(evaluation, self)
        if results_dlg.exec():
            # User clicked "Try Again"
            self.midi_engine.stop()
            self.score_view.set_playback_time(0)
            self.start_practice_mode()
        else:
            # User clicked "Done"
            self.midi_engine.mode = "Master"
            self.mode_label.setText("Master Mode")
            self.setWindowTitle("How To Piano")
    
    def closeEvent(self, event):
        self.arduino.stop()
        self.arduino_thread.quit()
        self.arduino_thread.wait()
        event.accept()
