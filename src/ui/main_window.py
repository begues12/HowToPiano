import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Piano Teacher")
        self.resize(1024, 768)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Score View Placeholder
        self.score_view = QLabel("Score View (Professional Sheet Music will be here)")
        self.score_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_view.setStyleSheet("background-color: white; font-size: 20px; border: 1px solid #ccc;")
        self.main_layout.addWidget(self.score_view, stretch=3)

        # Controls Area
        controls_layout = QHBoxLayout()
        self.main_layout.addLayout(controls_layout, stretch=1)

        # Mode Selection
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Practice", "Student", "Practice (Wait)", "Corrector", "Master"])
        controls_layout.addWidget(QLabel("Mode:"))
        controls_layout.addWidget(self.mode_selector)

        # Playback Controls
        self.btn_open = QPushButton("Open MIDI")
        self.btn_open.clicked.connect(self.open_midi)
        controls_layout.addWidget(self.btn_open)

        self.btn_play = QPushButton("Play")
        controls_layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton("Stop")
        controls_layout.addWidget(self.btn_stop)

        # Piano Settings
        self.sound_selector = QComboBox()
        self.sound_selector.addItems(["Classic", "Electric", "Organ"])
        controls_layout.addWidget(QLabel("Sound:"))
        controls_layout.addWidget(self.sound_selector)

    def open_midi(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open MIDI File", "", "MIDI Files (*.mid *.midi)")
        if file_name:
            print(f"Selected file: {file_name}")
            # TODO: Load MIDI
