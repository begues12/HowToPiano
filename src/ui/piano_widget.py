from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

class PianoWidget(QWidget):
    def __init__(self, num_keys=88, parent=None):
        super().__init__(parent)
        self.num_keys = num_keys
        self.start_note = 21 # Default for 88 keys (A0)
        self.active_notes = {} # {note: color}
        self.update_range()
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)

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
        white_key_rects = {} # note -> rect
        
        for i in range(self.num_keys):
            note = self.start_note + i
            if not self.is_black(note):
                r = QRectF(x, 0, key_width, height)
                white_key_rects[note] = r
                
                # Color
                if note in self.active_notes:
                    brush = QBrush(self.active_notes[note])
                else:
                    brush = QBrush(Qt.GlobalColor.white)
                
                painter.setBrush(brush)
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawRect(r)
                
                # Label C notes
                if note % 12 == 0:
                    painter.drawText(r, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, f"C{note//12 - 1}")

                x += key_width

        # Draw Black Keys
        # Black keys are usually thinner and shorter
        black_key_width = key_width * 0.6
        black_key_height = height * 0.6
        
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
                
                if note in self.active_notes:
                    brush = QBrush(self.active_notes[note])
                else:
                    brush = QBrush(Qt.GlobalColor.black)
                
                painter.setBrush(brush)
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawRect(r)
            else:
                current_white_x += key_width

    def is_black(self, note):
        # MIDI note 0 is C-1.
        # 0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F, 6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B
        n = note % 12
        return n in [1, 3, 6, 8, 10]
