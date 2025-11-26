from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class LoadingDialog(QDialog):
    """Modern loading dialog with cancel button"""
    cancel_requested = pyqtSignal()
    
    def __init__(self, title="Loading", message="Please wait...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 180)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
                background-color: #34495e;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 3px;
            }
            QPushButton {
                background-color: #c0392b;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title label
        self.title_label = QLabel(message)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.title_label.setFont(font)
        layout.addWidget(self.title_label)
        
        # Progress bar (indeterminate by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate mode
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #bdc3c7; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        layout.addSpacing(10)
        
        # Cancel button
        self.btn_cancel = QPushButton("✕ Cancel")
        self.btn_cancel.clicked.connect(self.on_cancel)
        layout.addWidget(self.btn_cancel)
        
        self.cancelled = False
    
    def set_message(self, message):
        """Update the main message"""
        self.title_label.setText(message)
    
    def set_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
    
    def set_progress(self, value, maximum=100):
        """Set determinate progress (0-100)"""
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
    
    def set_indeterminate(self):
        """Set indeterminate progress (spinning)"""
        self.progress_bar.setMaximum(0)
    
    def on_cancel(self):
        """Handle cancel button click"""
        self.cancelled = True
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("Cancelling...")
        self.cancel_requested.emit()
    
    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled
