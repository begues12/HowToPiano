"""
Practice Results Dialog - Shows detailed statistics after completing Practice Mode
Displays accuracy, timing, mistakes, and a 5-star rating
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QGroupBox, QScrollArea, QWidget,
                              QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
import time


class PracticeResultsDialog(QDialog):
    """
    Dialog showing practice session results with detailed statistics
    
    Rating criteria (5 stars):
    - Accuracy: 0-100% (40% weight)
    - Timing consistency: Low variance in response times (30% weight)
    - Mistake distribution: Few clusters of mistakes (15% weight)
    - Completion: Finished vs stopped early (15% weight)
    """
    
    # Signals
    retry_clicked = pyqtSignal()
    continue_clicked = pyqtSignal()
    
    def __init__(self, session_stats, parent=None):
        """
        Args:
            session_stats: Dictionary with practice session data
                {
                    'total_notes': int,
                    'correct_notes': int,
                    'mistakes': list of dicts,
                    'accuracy': float,
                    'duration': float (optional),
                    'completed': bool (optional)
                }
        """
        super().__init__(parent)
        
        self.stats = session_stats
        self.setWindowTitle("🎹 Practice Results")
        self.setModal(True)
        self.setMinimumSize(600, 700)
        
        self._setup_ui()
        self._calculate_rating()
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("📊 Practice Session Results")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Star rating
        self.star_widget = self._create_star_display()
        layout.addWidget(self.star_widget)
        
        # Overall score label
        self.score_label = QLabel()
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_font = QFont()
        score_font.setPointSize(14)
        score_font.setBold(True)
        self.score_label.setFont(score_font)
        layout.addWidget(self.score_label)
        
        # Statistics panels
        stats_scroll = QScrollArea()
        stats_scroll.setWidgetResizable(True)
        stats_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        stats_container = QWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setSpacing(15)
        
        # Accuracy panel
        stats_layout.addWidget(self._create_accuracy_panel())
        
        # Timing panel
        stats_layout.addWidget(self._create_timing_panel())
        
        # Mistakes panel
        stats_layout.addWidget(self._create_mistakes_panel())
        
        # Performance details
        stats_layout.addWidget(self._create_details_panel())
        
        stats_scroll.setWidget(stats_container)
        layout.addWidget(stats_scroll, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        retry_btn = QPushButton("🔄 Try Again")
        retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        retry_btn.clicked.connect(self._on_retry)
        button_layout.addWidget(retry_btn)
        
        continue_btn = QPushButton("➡️ Continue")
        continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        continue_btn.clicked.connect(self._on_continue)
        button_layout.addWidget(continue_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                background-color: #34495e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
    
    def _create_star_display(self):
        """Create the star rating display"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        self.star_labels = []
        for i in range(5):
            star_label = QLabel("⭐")
            star_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            star_font = QFont()
            star_font.setPointSize(32)
            star_label.setFont(star_font)
            layout.addWidget(star_label)
            self.star_labels.append(star_label)
        
        return container
    
    def _create_accuracy_panel(self):
        """Create accuracy statistics panel"""
        group = QGroupBox("🎯 Accuracy")
        layout = QVBoxLayout()
        
        # Accuracy percentage
        accuracy = self.stats.get('accuracy', 0)
        accuracy_label = QLabel(f"<b>Overall Accuracy:</b> {accuracy:.1f}%")
        accuracy_label.setStyleSheet(f"font-size: 16px; color: {self._get_accuracy_color(accuracy)};")
        layout.addWidget(accuracy_label)
        
        # Notes breakdown
        total = self.stats.get('total_notes', 0)
        correct = self.stats.get('correct_notes', 0)
        wrong = total - correct
        
        breakdown = QLabel(
            f"✅ Correct notes: <b>{correct}</b> / {total}<br>"
            f"❌ Wrong notes: <b>{wrong}</b>"
        )
        breakdown.setStyleSheet("font-size: 13px; margin-top: 5px;")
        layout.addWidget(breakdown)
        
        # Progress bar visual
        progress_bar = self._create_progress_bar(accuracy)
        layout.addWidget(progress_bar)
        
        group.setLayout(layout)
        return group
    
    def _create_timing_panel(self):
        """Create timing analysis panel"""
        group = QGroupBox("⏱️ Timing Analysis")
        layout = QVBoxLayout()
        
        mistakes = self.stats.get('mistakes', [])
        
        if not mistakes:
            timing_label = QLabel("🌟 <b>Perfect!</b> No mistakes to analyze.")
            timing_label.setStyleSheet("font-size: 14px; color: #27ae60;")
            layout.addWidget(timing_label)
        else:
            # Calculate timing consistency
            timing_score, timing_desc = self._calculate_timing_score(mistakes)
            
            timing_label = QLabel(f"<b>Timing Consistency:</b> {timing_desc}")
            timing_label.setStyleSheet(f"font-size: 14px; color: {self._get_timing_color(timing_score)};")
            layout.addWidget(timing_label)
            
            # Additional timing info
            if len(mistakes) > 1:
                # Find sections with multiple mistakes (clusters)
                clusters = self._find_mistake_clusters(mistakes)
                if clusters:
                    cluster_text = f"⚠️ Found {len(clusters)} difficult section(s) with multiple mistakes"
                    cluster_label = QLabel(cluster_text)
                    cluster_label.setStyleSheet("font-size: 12px; color: #f39c12; margin-top: 5px;")
                    layout.addWidget(cluster_label)
        
        group.setLayout(layout)
        return group
    
    def _create_mistakes_panel(self):
        """Create mistakes breakdown panel"""
        group = QGroupBox("📝 Mistakes Breakdown")
        layout = QVBoxLayout()
        
        mistakes = self.stats.get('mistakes', [])
        
        if not mistakes:
            no_mistakes = QLabel("🎉 <b>Perfect Performance!</b><br>No mistakes detected.")
            no_mistakes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_mistakes.setStyleSheet("font-size: 14px; color: #27ae60; padding: 10px;")
            layout.addWidget(no_mistakes)
        else:
            # Show mistake count
            mistake_count = QLabel(f"Total mistakes: <b>{len(mistakes)}</b>")
            mistake_count.setStyleSheet("font-size: 13px; margin-bottom: 10px;")
            layout.addWidget(mistake_count)
            
            # Show first few mistakes
            max_show = min(5, len(mistakes))
            for i, mistake in enumerate(mistakes[:max_show]):
                mistake_text = self._format_mistake(mistake, i + 1)
                mistake_label = QLabel(mistake_text)
                mistake_label.setStyleSheet("""
                    font-size: 11px;
                    padding: 5px;
                    background-color: #2c3e50;
                    border-left: 3px solid #e74c3c;
                    margin-bottom: 5px;
                """)
                mistake_label.setWordWrap(True)
                layout.addWidget(mistake_label)
            
            if len(mistakes) > max_show:
                more_label = QLabel(f"... and {len(mistakes) - max_show} more mistake(s)")
                more_label.setStyleSheet("font-size: 11px; color: #95a5a6; font-style: italic;")
                layout.addWidget(more_label)
        
        group.setLayout(layout)
        return group
    
    def _create_details_panel(self):
        """Create additional details panel"""
        group = QGroupBox("📋 Session Details")
        layout = QVBoxLayout()
        
        # Duration
        duration = self.stats.get('duration', 0)
        if duration > 0:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_text = f"⏱️ Duration: <b>{minutes}m {seconds}s</b>"
        else:
            duration_text = "⏱️ Duration: <b>N/A</b>"
        
        duration_label = QLabel(duration_text)
        duration_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(duration_label)
        
        # Completion status
        completed = self.stats.get('completed', True)
        if completed:
            completion_text = "✅ Status: <b>Completed</b>"
            completion_color = "#27ae60"
        else:
            completion_text = "⏹️ Status: <b>Stopped Early</b>"
            completion_color = "#f39c12"
        
        completion_label = QLabel(completion_text)
        completion_label.setStyleSheet(f"font-size: 13px; color: {completion_color};")
        layout.addWidget(completion_label)
        
        # Timestamp
        timestamp = self.stats.get('timestamp', time.time())
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        time_label = QLabel(f"📅 Date: <b>{time_str}</b>")
        time_label.setStyleSheet("font-size: 12px; color: #95a5a6;")
        layout.addWidget(time_label)
        
        group.setLayout(layout)
        return group
    
    def _create_progress_bar(self, percentage):
        """Create a visual progress bar"""
        container = QWidget()
        container.setFixedHeight(30)
        container.setStyleSheet(f"""
            background-color: #34495e;
            border-radius: 15px;
        """)
        
        bar = QWidget(container)
        bar_width = int((percentage / 100) * (container.width() - 10))
        bar.setGeometry(5, 5, bar_width, 20)
        bar.setStyleSheet(f"""
            background-color: {self._get_accuracy_color(percentage)};
            border-radius: 10px;
        """)
        
        return container
    
    def _calculate_rating(self):
        """Calculate overall 5-star rating"""
        # Weights
        ACCURACY_WEIGHT = 0.40
        TIMING_WEIGHT = 0.30
        DISTRIBUTION_WEIGHT = 0.15
        COMPLETION_WEIGHT = 0.15
        
        # 1. Accuracy score (0-1)
        accuracy = self.stats.get('accuracy', 0) / 100
        
        # 2. Timing score (0-1)
        mistakes = self.stats.get('mistakes', [])
        timing_score, _ = self._calculate_timing_score(mistakes)
        timing_score = timing_score / 100
        
        # 3. Distribution score (0-1) - penalize clustered mistakes
        distribution_score = self._calculate_distribution_score(mistakes)
        
        # 4. Completion score (0-1)
        completion_score = 1.0 if self.stats.get('completed', True) else 0.5
        
        # Calculate weighted score
        total_score = (
            accuracy * ACCURACY_WEIGHT +
            timing_score * TIMING_WEIGHT +
            distribution_score * DISTRIBUTION_WEIGHT +
            completion_score * COMPLETION_WEIGHT
        )
        
        # Convert to stars (0-5)
        stars = round(total_score * 5)
        stars = max(0, min(5, stars))  # Clamp to 0-5
        
        self.rating_stars = stars
        self.rating_score = total_score * 100
        
        # Update UI
        self._update_star_display()
        self._update_score_label()
    
    def _calculate_timing_score(self, mistakes):
        """Calculate timing consistency score"""
        if not mistakes:
            return 100, "Excellent"
        
        # Look at mistake distribution across the song
        total_notes = self.stats.get('total_notes', 1)
        mistake_rate = len(mistakes) / total_notes
        
        if mistake_rate < 0.05:  # Less than 5% mistakes
            return 90, "Excellent"
        elif mistake_rate < 0.10:  # Less than 10%
            return 75, "Good"
        elif mistake_rate < 0.20:  # Less than 20%
            return 60, "Fair"
        elif mistake_rate < 0.30:  # Less than 30%
            return 40, "Needs Practice"
        else:
            return 20, "Keep Practicing"
    
    def _calculate_distribution_score(self, mistakes):
        """Calculate how evenly distributed mistakes are (clustered = bad)"""
        if not mistakes:
            return 1.0
        
        clusters = self._find_mistake_clusters(mistakes)
        
        # Penalize based on cluster count
        if not clusters:
            return 1.0
        elif len(clusters) == 1:
            return 0.8
        elif len(clusters) == 2:
            return 0.6
        elif len(clusters) == 3:
            return 0.4
        else:
            return 0.2
    
    def _find_mistake_clusters(self, mistakes):
        """Find clusters of mistakes (within 5 seconds of each other)"""
        if len(mistakes) < 2:
            return []
        
        clusters = []
        current_cluster = [mistakes[0]]
        
        for i in range(1, len(mistakes)):
            time_diff = mistakes[i]['time'] - mistakes[i-1]['time']
            if time_diff <= 5.0:  # Within 5 seconds
                current_cluster.append(mistakes[i])
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [mistakes[i]]
        
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)
        
        return clusters
    
    def _format_mistake(self, mistake, index):
        """Format a mistake for display"""
        time_pos = mistake.get('time', 0)
        expected = mistake.get('expected', [])
        played = mistake.get('played', 0)
        
        # Convert MIDI notes to names
        expected_names = [self._midi_to_note_name(n) for n in expected]
        played_name = self._midi_to_note_name(played)
        
        expected_str = ', '.join(expected_names) if expected_names else 'N/A'
        
        return (
            f"<b>#{index}</b> at {time_pos:.1f}s<br>"
            f"Expected: <span style='color: #3498db;'>{expected_str}</span><br>"
            f"Played: <span style='color: #e74c3c;'>{played_name}</span>"
        )
    
    def _midi_to_note_name(self, midi_note):
        """Convert MIDI note number to name"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note = note_names[midi_note % 12]
        return f"{note}{octave}"
    
    def _update_star_display(self):
        """Update star display based on rating"""
        for i, star_label in enumerate(self.star_labels):
            if i < self.rating_stars:
                star_label.setText("⭐")
                star_label.setStyleSheet("color: #f39c12;")
            else:
                star_label.setText("☆")
                star_label.setStyleSheet("color: #7f8c8d;")
    
    def _update_score_label(self):
        """Update score label with rating message"""
        if self.rating_stars == 5:
            message = "🎉 Perfect Performance!"
            color = "#27ae60"
        elif self.rating_stars == 4:
            message = "🌟 Excellent Work!"
            color = "#2ecc71"
        elif self.rating_stars == 3:
            message = "👍 Good Job!"
            color = "#3498db"
        elif self.rating_stars == 2:
            message = "📚 Keep Practicing!"
            color = "#f39c12"
        else:
            message = "💪 Don't Give Up!"
            color = "#e67e22"
        
        self.score_label.setText(f"{message}<br><span style='font-size: 12px;'>Overall Score: {self.rating_score:.1f}%</span>")
        self.score_label.setStyleSheet(f"color: {color};")
    
    def _get_accuracy_color(self, accuracy):
        """Get color based on accuracy percentage"""
        if accuracy >= 90:
            return "#27ae60"  # Green
        elif accuracy >= 75:
            return "#2ecc71"  # Light green
        elif accuracy >= 60:
            return "#3498db"  # Blue
        elif accuracy >= 40:
            return "#f39c12"  # Orange
        else:
            return "#e74c3c"  # Red
    
    def _get_timing_color(self, timing_score):
        """Get color based on timing score"""
        if timing_score >= 80:
            return "#27ae60"
        elif timing_score >= 60:
            return "#3498db"
        elif timing_score >= 40:
            return "#f39c12"
        else:
            return "#e74c3c"
    
    def _on_retry(self):
        """Handle retry button click"""
        self.retry_clicked.emit()
        self.accept()
    
    def _on_continue(self):
        """Handle continue button click"""
        self.continue_clicked.emit()
        self.accept()
