"""
Results Dialog - Shows performance evaluation after practice
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class ResultsDialog(QDialog):
    def __init__(self, evaluation_result, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Practice Results")
        self.resize(600, 700)
        self.evaluation = evaluation_result
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🎹 Practice Session Complete!")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Overall Stars
        stars_widget = self._create_stars_widget()
        layout.addWidget(stars_widget)
        
        # Overall Score
        score_label = QLabel(f"Overall Score: {self.evaluation['average_score']:.1f}%")
        score_label.setFont(QFont("Arial", 16))
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(score_label)
        
        # Detailed Scores
        details_group = self._create_details_group()
        layout.addWidget(details_group)
        
        # Statistics
        stats_group = self._create_stats_group()
        layout.addWidget(stats_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        retry_btn = QPushButton("🔄 Try Again")
        retry_btn.clicked.connect(self.accept)
        retry_btn.setMinimumHeight(40)
        button_layout.addWidget(retry_btn)
        
        close_btn = QPushButton("✓ Done")
        close_btn.clicked.connect(self.reject)
        close_btn.setMinimumHeight(40)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_stars_widget(self):
        """Create widget showing star rating"""
        widget = QGroupBox()
        layout = QVBoxLayout(widget)
        
        stars = self.evaluation['overall_stars']
        star_text = "⭐" * stars + "☆" * (5 - stars)
        
        stars_label = QLabel(star_text)
        stars_label.setFont(QFont("Arial", 40))
        stars_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stars_label)
        
        # Performance message
        messages = {
            5: "🎉 Perfect Performance!",
            4: "👏 Excellent Work!",
            3: "👍 Good Job!",
            2: "💪 Keep Practicing!",
            1: "📚 Need More Practice",
            0: "🎯 Let's Try Again"
        }
        
        message = QLabel(messages.get(stars, ""))
        message.setFont(QFont("Arial", 14))
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        return widget
    
    def _create_details_group(self):
        """Create detailed scores for each criterion"""
        group = QGroupBox("Detailed Evaluation")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        criteria = [
            ("🎯 Note Accuracy", self.evaluation['note_accuracy']),
            ("⏱️ Timing Precision", self.evaluation['timing_precision']),
            ("🌊 Fluency", self.evaluation['fluency']),
            ("🔊 Dynamics", self.evaluation['dynamics']),
            ("🎨 Expression", self.evaluation['expression'])
        ]
        
        row = 0
        for label_text, score in criteria:
            # Label
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 12))
            layout.addWidget(label, row, 0)
            
            # Progress bar
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(score))
            progress.setTextVisible(True)
            progress.setFormat(f"{score:.1f}%")
            progress.setMinimumHeight(25)
            
            # Color based on score
            if score >= 80:
                color = "#27ae60"  # Green
            elif score >= 60:
                color = "#f39c12"  # Orange
            else:
                color = "#e74c3c"  # Red
            
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #bdc3c7;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #ecf0f1;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            
            layout.addWidget(progress, row, 1)
            
            # Status icon
            status = "✓" if score >= 80 else "✗"
            status_label = QLabel(status)
            status_label.setFont(QFont("Arial", 16))
            layout.addWidget(status_label, row, 2)
            
            row += 1
        
        return group
    
    def _create_stats_group(self):
        """Create statistics group"""
        group = QGroupBox("Statistics")
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        details = self.evaluation['details']
        
        stats = [
            ("Total Notes Expected:", details['total_expected']),
            ("Notes Played:", details['total_played']),
            ("Correct Notes:", details['total_expected'] - details['missed_notes']),
            ("Wrong Notes:", details['wrong_notes']),
            ("Missed Notes:", details['missed_notes']),
            ("Extra Notes:", details['extra_notes']),
            ("Timing Errors:", details['timing_errors']),
            ("Long Pauses:", details['long_pauses'])
        ]
        
        row = 0
        for label_text, value in stats:
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 11))
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
            
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            layout.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignRight)
            
            row += 1
        
        return group
    
    def _apply_styles(self):
        """Apply dark theme styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
                color: white;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
