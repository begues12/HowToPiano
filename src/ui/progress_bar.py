from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent

class ProgressBar(QWidget):
    """Interactive progress bar for song playback"""
    seek_requested = pyqtSignal(float)  # Emit when user clicks to seek
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_duration = 0.0  # Total song duration in seconds
        self.current_time = 0.0    # Current playback time
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setMouseTracking(True)
        self.hover_time = None
        
    def set_duration(self, duration):
        """Set total song duration"""
        self.total_duration = duration
        self.update()
    
    def set_time(self, time):
        """Update current playback time"""
        self.current_time = time
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle click to seek"""
        if event.button() == Qt.MouseButton.LeftButton and self.total_duration > 0:
            # Calculate time based on click position
            x = event.position().x()
            width = self.width()
            time = (x / width) * self.total_duration
            self.seek_requested.emit(time)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Show time tooltip on hover"""
        if self.total_duration > 0:
            x = event.position().x()
            width = self.width()
            self.hover_time = (x / width) * self.total_duration
            self.update()
    
    def leaveEvent(self, event):
        """Clear hover tooltip"""
        self.hover_time = None
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.fillRect(0, 0, width, height, QColor(44, 62, 80))
        
        # Progress bar background track
        bar_height = 8
        bar_y = (height - bar_height) // 2
        painter.setBrush(QBrush(QColor(52, 73, 94)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(10, bar_y, width - 20, bar_height, 4, 4)
        
        if self.total_duration > 0:
            # Progress bar filled portion
            progress_width = ((width - 20) * self.current_time / self.total_duration)
            painter.setBrush(QBrush(QColor(52, 152, 219)))  # Blue progress
            painter.drawRoundedRect(10, bar_y, progress_width, bar_height, 4, 4)
            
            # Time markers every 10 seconds
            marker_interval = 10.0  # seconds
            num_markers = int(self.total_duration / marker_interval)
            
            painter.setPen(QPen(QColor(149, 165, 166), 1))
            for i in range(1, num_markers + 1):
                marker_time = i * marker_interval
                marker_x = 10 + ((width - 20) * marker_time / self.total_duration)
                painter.drawLine(int(marker_x), bar_y - 3, int(marker_x), bar_y + bar_height + 3)
            
            # Current time text
            current_str = self._format_time(self.current_time)
            total_str = self._format_time(self.total_duration)
            time_text = f"{current_str} / {total_str}"
            
            painter.setPen(QPen(QColor(236, 240, 241)))
            painter.drawText(15, height - 8, time_text)
            
            # Hover tooltip
            if self.hover_time is not None:
                hover_x = 10 + ((width - 20) * self.hover_time / self.total_duration)
                painter.setPen(QPen(QColor(241, 196, 15), 2))
                painter.drawLine(int(hover_x), bar_y, int(hover_x), bar_y + bar_height)
                
                # Tooltip text
                hover_str = self._format_time(self.hover_time)
                painter.setPen(QPen(QColor(241, 196, 15)))
                painter.drawText(int(hover_x) - 20, bar_y - 5, hover_str)
    
    def _format_time(self, seconds):
        """Format seconds as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
