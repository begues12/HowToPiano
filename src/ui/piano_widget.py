from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent

class PianoWidget(QWidget):
    # Signals for mouse interaction
    note_pressed = pyqtSignal(int, int)  # note, velocity
    note_released = pyqtSignal(int)  # note
    
    def __init__(self, num_keys=88, parent=None):
        super().__init__(parent)
        self.num_keys = num_keys
        self.start_note = 21 # Default for 88 keys (A0)
        self.physical_keys = num_keys  # Actual physical piano size
        self.active_notes = {} # {note: color}
        self.mouse_pressed_notes = set()  # Track notes pressed by mouse
        self.update_range()
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects
        
        # Store key rectangles for click detection
        self.white_key_rects = {}  # {note: QRectF}
        self.black_key_rects = {}  # {note: QRectF}
        
        # Finger assignment and colors
        self.finger_assignments = {}  # {note: finger_number (1-5)}
        self.finger_colors = {
            1: QColor(255, 100, 100),   # Red - Thumb
            2: QColor(100, 200, 100),   # Green - Index
            3: QColor(100, 150, 255),   # Blue - Middle
            4: QColor(255, 200, 100),   # Yellow - Ring
            5: QColor(200, 100, 255)    # Purple - Pinky
        }
        self.show_note_names = True  # Show note names on keys

    def set_num_keys(self, n):
        self.num_keys = n
        self.update_range()
        self.update()

    def update_range(self):
        # Standard ranges
        if self.num_keys == 88:
            self.start_note = 21 # A0
        elif self.num_keys == 76:
            self.start_note = 28 # E1
        elif self.num_keys == 61:
            self.start_note = 36 # C2
        elif self.num_keys == 49:
            self.start_note = 36 # C2
        else:
            self.start_note = 21

    def note_on(self, note, color=QColor("red")):
        self.active_notes[note] = color
        self.update()

    def note_off(self, note):
        if note in self.active_notes:
            del self.active_notes[note]
        self.update()
    
    def set_finger_assignment(self, note, finger):
        """Assign a finger (1-5) to a note"""
        if 1 <= finger <= 5:
            self.finger_assignments[note] = finger
            self.update()
    
    def clear_finger_assignments(self):
        """Clear all finger assignments"""
        self.finger_assignments = {}
        self.update()
    
    def get_finger_color(self, finger):
        """Get color for a specific finger"""
        return self.finger_colors.get(finger, QColor(128, 128, 128))
    
    def get_note_name(self, note):
        """Get the name of a note (e.g., C4, D#5)"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note // 12) - 1
        name = note_names[note % 12]
        return f"{name}{octave}"
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Calculate white key width
        # Count white keys
        white_keys_count = 0
        for i in range(self.num_keys):
            note = self.start_note + i
            if not self.is_black(note):
                white_keys_count += 1
        
        if white_keys_count == 0: return

        key_width = width / white_keys_count
        
        # Draw White Keys
        x = 0
        self.white_key_rects = {} # note -> rect
        
        for i in range(self.num_keys):
            note = self.start_note + i
            if not self.is_black(note):
                r = QRectF(x, 0, key_width, height)
                self.white_key_rects[note] = r
                
                # Color
                if note in self.active_notes:
                    brush = QBrush(self.active_notes[note])
                elif note in self.finger_assignments:
                    # Use finger color with transparency
                    finger = self.finger_assignments[note]
                    color = self.get_finger_color(finger)
                    color.setAlpha(80)  # Semi-transparent
                    brush = QBrush(color)
                else:
                    brush = QBrush(Qt.GlobalColor.white)
                
                painter.setBrush(brush)
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawRect(r)
                
                # Draw note name
                if self.show_note_names:
                    painter.setPen(QPen(Qt.GlobalColor.black))
                    painter.drawText(r, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, 
                                   self.get_note_name(note))
                
                # Draw finger number if assigned
                if note in self.finger_assignments:
                    finger = self.finger_assignments[note]
                    painter.setPen(QPen(self.get_finger_color(finger)))
                    from PyQt6.QtGui import QFont
                    font = QFont("Arial", 14, QFont.Weight.Bold)
                    painter.setFont(font)
                    painter.drawText(r, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, 
                                   str(finger))

                x += key_width

        # Draw Black Keys
        # Black keys are usually thinner and shorter
        black_key_width = key_width * 0.6
        black_key_height = height * 0.6
        
        self.black_key_rects = {}
        
        # We need to position them relative to white keys
        # A black key is between two white keys.
        # C# is between C and D.
        
        # Reset x traversal to find positions
        current_white_x = 0
        
        for i in range(self.num_keys):
            note = self.start_note + i
            if self.is_black(note):
                # It sits on top of the boundary between the previous white key and the next
                # Previous white key started at current_white_x - key_width
                # Center is at current_white_x
                bx = current_white_x - (black_key_width / 2)
                r = QRectF(bx, 0, black_key_width, black_key_height)
                self.black_key_rects[note] = r
                
                if note in self.active_notes:
                    brush = QBrush(self.active_notes[note])
                elif note in self.finger_assignments:
                    # Use finger color with transparency
                    finger = self.finger_assignments[note]
                    color = self.get_finger_color(finger)
                    color.setAlpha(120)  # Semi-transparent
                    brush = QBrush(color)
                else:
                    brush = QBrush(Qt.GlobalColor.black)
                
                painter.setBrush(brush)
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawRect(r)
                
                # Draw note name on black keys
                if self.show_note_names:
                    painter.setPen(QPen(Qt.GlobalColor.white))
                    from PyQt6.QtGui import QFont
                    font = QFont("Arial", 8)
                    painter.setFont(font)
                    painter.drawText(r, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, 
                                   self.get_note_name(note))
                
                # Draw finger number if assigned
                if note in self.finger_assignments:
                    finger = self.finger_assignments[note]
                    painter.setPen(QPen(Qt.GlobalColor.white))
                    font = QFont("Arial", 12, QFont.Weight.Bold)
                    painter.setFont(font)
                    painter.drawText(r, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, 
                                   str(finger))
            else:
                current_white_x += key_width

    def is_black(self, note):
        # MIDI note 0 is C-1.
        # 0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F, 6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B
        n = note % 12
        return n in [1, 3, 6, 8, 10]
    
    def get_note_at_position(self, pos):
        """Get the note number at the given position, or None"""
        # Check black keys first (they're on top)
        for note, rect in self.black_key_rects.items():
            if rect.contains(pos):
                return note
        
        # Check white keys
        for note, rect in self.white_key_rects.items():
            if rect.contains(pos):
                return note
        
        return None
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press on piano keys"""
        if event.button() == Qt.MouseButton.LeftButton:
            note = self.get_note_at_position(event.position())
            if note is not None and note not in self.mouse_pressed_notes:
                self.mouse_pressed_notes.add(note)
                velocity = 100  # Default velocity for mouse clicks
                self.note_pressed.emit(note, velocity)
                self.note_on(note, QColor("cyan"))  # Visual feedback
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Release all notes pressed by mouse
            for note in list(self.mouse_pressed_notes):
                self.mouse_pressed_notes.remove(note)
                self.note_released.emit(note)
                self.note_off(note)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse drag across keys"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            note = self.get_note_at_position(event.position())
            
            # Press new note if hovering over one not already pressed
            if note is not None and note not in self.mouse_pressed_notes:
                self.mouse_pressed_notes.add(note)
                velocity = 100
                self.note_pressed.emit(note, velocity)
                self.note_on(note, QColor("cyan"))
            
            # Release notes we're no longer over
            for pressed_note in list(self.mouse_pressed_notes):
                if pressed_note != note:
                    self.mouse_pressed_notes.remove(pressed_note)
                    self.note_released.emit(pressed_note)
                    self.note_off(pressed_note)
