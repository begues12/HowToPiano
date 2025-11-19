from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QFontDatabase
import mido
import os

class StaffWidget(QWidget):
    """Interactive musical staff that displays and highlights notes during playback"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)
        self.setStyleSheet("background-color: white;")
        
        # Load Bravura font for music symbols
        font_path = os.path.join(os.getcwd(), "assets", "fonts", "Bravura.otf")
        if os.path.exists(font_path):
            self.font_id = QFontDatabase.addApplicationFont(font_path)
            if self.font_id != -1:
                self.music_font_family = QFontDatabase.applicationFontFamilies(self.font_id)[0]
                print(f"StaffWidget: Loaded Bravura font: {self.music_font_family}")
            else:
                print("StaffWidget: Failed to load Bravura font")
                self.music_font_family = "Arial"
        else:
            print(f"StaffWidget: Bravura font not found at {font_path}")
            self.music_font_family = "Arial"
        
        # Musical data
        self.notes = []  # List of {id, time, pitch, duration, x, y, chord_id}
        self.chords = []  # List of chord groups: {id, time, note_ids: [ids]}
        self.active_note_ids = set()  # IDs of notes currently being played
        self.active_chord_id = None  # Currently active chord group
        self.current_time = 0  # Current playback time in seconds
        self.pixels_per_second = 100  # Horizontal spacing
        self.scroll_offset = 0  # Horizontal scroll position
        
        # Staff parameters
        self.staff_spacing = 15  # Pixels between staff lines
        self.top_margin = 50
        self.bottom_margin = 50
        self.left_margin = 100  # Space for fixed clef
        self.preparation_time = 3.0  # 3 seconds before start
        
        # Countdown state
        self.countdown_active = False
        self.countdown_value = 3
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._countdown_tick)
        
        # Finger assignment and colors (matching PianoWidget)
        self.finger_colors = {
            1: QColor(255, 100, 100),   # Red - Thumb
            2: QColor(100, 200, 100),   # Green - Index
            3: QColor(100, 150, 255),   # Blue - Middle
            4: QColor(255, 200, 100),   # Yellow - Ring
            5: QColor(200, 100, 255)    # Purple - Pinky
        }
        self.note_fingers = {}  # {note_id: finger_number}
        
        # Note name to MIDI number mapping
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
    def load_midi_notes(self, midi_path):
        """Load notes from MIDI file"""
        try:
            mid = mido.MidiFile(midi_path)
            self.notes = []
            
            # Convert ticks to seconds
            tempo = 500000  # Default tempo (120 BPM)
            ticks_per_beat = mid.ticks_per_beat
            
            # Combine all tracks into single timeline
            events = []
            for track_idx, track in enumerate(mid.tracks):
                current_tick = 0
                current_tempo = tempo
                
                for msg in track:
                    current_tick += msg.time
                    
                    # Update tempo if we see tempo change
                    if msg.type == 'set_tempo':
                        current_tempo = msg.tempo
                    
                    if msg.type in ['note_on', 'note_off']:
                        # Convert ticks to seconds
                        time_seconds = mido.tick2second(current_tick, ticks_per_beat, current_tempo)
                        
                        events.append({
                            'time': time_seconds,
                            'type': msg.type,
                            'note': msg.note,
                            'velocity': msg.velocity if hasattr(msg, 'velocity') else 0,
                            'track': track_idx
                        })
            
            # Sort all events by time
            events.sort(key=lambda e: e['time'])
            
            # Track active notes
            active_notes = {}  # pitch -> start_time
            
            for event in events:
                if event['type'] == 'note_on' and event['velocity'] > 0:
                    # Note starts
                    if event['note'] not in active_notes:
                        active_notes[event['note']] = event['time']
                
                elif event['type'] == 'note_off' or (event['type'] == 'note_on' and event['velocity'] == 0):
                    # Note ends
                    if event['note'] in active_notes:
                        start_time = active_notes[event['note']]
                        duration = event['time'] - start_time
                        
                        # Calculate position (add preparation time offset)
                        x = (start_time + self.preparation_time) * self.pixels_per_second
                        y = self.pitch_to_y(event['note'])
                        
                        note_id = len(self.notes)  # Unique ID for this note
                        self.notes.append({
                            'id': note_id,
                            'time': start_time,
                            'pitch': event['note'],
                            'duration': duration,
                            'x': x,
                            'y': y
                        })
                        del active_notes[event['note']]
            
            # Group notes into chords (notes that start at the same time)
            self.chords = []
            chord_tolerance = 0.02  # 20ms tolerance for simultaneous notes
            
            chord_id = 0
            i = 0
            while i < len(self.notes):
                chord_time = self.notes[i]['time']
                chord_note_ids = [self.notes[i]['id']]
                self.notes[i]['chord_id'] = chord_id
                
                # Find all notes that start at approximately the same time
                j = i + 1
                while j < len(self.notes) and abs(self.notes[j]['time'] - chord_time) < chord_tolerance:
                    chord_note_ids.append(self.notes[j]['id'])
                    self.notes[j]['chord_id'] = chord_id
                    j += 1
                
                self.chords.append({
                    'id': chord_id,
                    'time': chord_time,
                    'note_ids': chord_note_ids
                })
                
                chord_id += 1
                i = j
            
            print(f"StaffWidget: Loaded {len(self.notes)} notes in {len(self.chords)} chords")
            if len(self.notes) > 0:
                print(f"StaffWidget: First note at time {self.notes[0]['time']:.2f}s, pitch {self.notes[0]['pitch']}")
                print(f"StaffWidget: Sample chord sizes: {[len(c['note_ids']) for c in self.chords[:5]]}")
            
            # Assign fingers based on note positions
            self._assign_fingers_to_notes()
            
            self.update()
            return True
            
        except Exception as e:
            import traceback
            print(f"StaffWidget: Error loading MIDI: {e}")
            traceback.print_exc()
            return False
    
    def pitch_to_y(self, midi_note):
        """Convert MIDI note number to Y position on staff"""
        # Treble clef staff lines (bottom to top):
        # Line 1: E4 (MIDI 64)
        # Line 2: G4 (MIDI 67) 
        # Line 3: B4 (MIDI 71) - middle line
        # Line 4: D5 (MIDI 74)
        # Line 5: F5 (MIDI 77)
        
        center_y = self.height() / 2
        
        # Reference: B4 (MIDI 71) is on the middle line (line 3)
        reference_note = 71  # B4
        reference_y = center_y  # Middle line
        
        # Each half-step (semitone) moves by staff_spacing/2
        # Notes go UP as MIDI number increases, but Y goes DOWN
        distance = reference_note - midi_note
        y = reference_y + (distance * self.staff_spacing / 2)
        
        return y
    
    def get_note_range(self):
        """Get the min and max pitch in loaded notes"""
        if not self.notes:
            return None, None
        pitches = [note['pitch'] for note in self.notes]
        return min(pitches), max(pitches)
    
    def transpose_notes(self, semitones):
        """Transpose all notes by the given number of semitones"""
        if not self.notes:
            return
        
        for note in self.notes:
            note['pitch'] += semitones
            # Recalculate y position
            note['y'] = self.pitch_to_y(note['pitch'])
        
        print(f"StaffWidget: Transposed all notes by {semitones} semitones")
    
    def check_and_adapt_to_keyboard(self, piano_start, piano_end):
        """Check note range - no longer transposes, just returns info"""
        min_pitch, max_pitch = self.get_note_range()
        
        if min_pitch is None:
            return 0
        
        print(f"Song range: {min_pitch}-{max_pitch}, Piano display will expand to fit")
        return 0
    
    def _assign_fingers_to_notes(self):
        """Assign fingers to notes based on pitch and hand position"""
        if not self.notes:
            return
        
        # Simple finger assignment based on relative pitch
        # For right hand: lower notes = thumb (1), higher = pinky (5)
        for note in self.notes:
            pitch = note['pitch']
            note_id = note['id']
            
            # Assign finger based on pitch range
            # Middle C (60) area uses all fingers
            if pitch < 55:
                finger = 1  # Thumb for very low notes
            elif pitch < 60:
                finger = 2  # Index
            elif pitch < 65:
                finger = 3  # Middle
            elif pitch < 70:
                finger = 4  # Ring
            else:
                finger = 5  # Pinky for high notes
            
            self.note_fingers[note_id] = finger
        
        print(f"StaffWidget: Assigned fingers to {len(self.note_fingers)} notes")
    
    def get_finger_for_note(self, note_id):
        """Get the assigned finger for a note"""
        return self.note_fingers.get(note_id, 3)  # Default to middle finger
    
    def start_countdown(self, callback=None):
        """Start 3-2-1 countdown before practice mode"""
        self.countdown_active = True
        self.countdown_value = 3
        self.countdown_callback = callback
        self.countdown_timer.start(1000)  # 1 second intervals
        self.update()
    
    def _countdown_tick(self):
        """Handle countdown timer tick"""
        self.countdown_value -= 1
        
        if self.countdown_value <= 0:
            self.countdown_timer.stop()
            self.countdown_active = False
            # Call the callback to start playback
            if self.countdown_callback:
                self.countdown_callback()
        
        self.update()
    
    def set_playback_time(self, time_sec):
        """Update current playback time and auto-scroll"""
        self.current_time = time_sec
        
        # Auto-scroll to keep red line at left margin + some offset
        # Add preparation time to match note positions
        target_x = (time_sec + self.preparation_time) * self.pixels_per_second
        playback_line_x = self.left_margin + 50  # Position of red line
        self.scroll_offset = target_x - playback_line_x
        
        # Don't update active_notes here - let note_on/note_off handle it
        # This prevents false highlighting of notes that overlap in time
        
        self.update()
    
    def note_on(self, pitch):
        """Highlight the specific note(s) with this pitch at current time"""
        # Find notes with this pitch that are at the current playback time
        tolerance = 0.05  # 50ms tolerance
        
        for note in self.notes:
            if note['pitch'] == pitch and abs(note['time'] - self.current_time) < tolerance:
                note_id = note['id']
                chord_id = note.get('chord_id')
                
                # Activate this note
                self.active_note_ids.add(note_id)
                
                # If it's part of a chord, activate all notes in that chord
                if chord_id is not None:
                    chord = next((c for c in self.chords if c['id'] == chord_id), None)
                    if chord:
                        for cid in chord['note_ids']:
                            self.active_note_ids.add(cid)
                        self.active_chord_id = chord_id
                break
        
        self.update()
    
    def note_off(self, pitch):
        """Remove highlight from specific note(s) with this pitch"""
        # Find and deactivate notes with this pitch that were recently activated
        notes_to_deactivate = []
        
        for note in self.notes:
            if note['pitch'] == pitch and note['id'] in self.active_note_ids:
                notes_to_deactivate.append(note)
        
        for note in notes_to_deactivate:
            note_id = note['id']
            chord_id = note.get('chord_id')
            
            # Deactivate this note
            self.active_note_ids.discard(note_id)
            
            # If it was part of a chord, deactivate the whole chord
            if chord_id is not None and chord_id == self.active_chord_id:
                chord = next((c for c in self.chords if c['id'] == chord_id), None)
                if chord:
                    for cid in chord['note_ids']:
                        self.active_note_ids.discard(cid)
                    self.active_chord_id = None
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("white"))
        
        # If countdown is active, draw it over everything
        if self.countdown_active:
            self.draw_countdown(painter)
        else:
            # Draw staff lines (5 lines for treble clef)
            self.draw_staff(painter)
            
            # Draw notes
            self.draw_notes(painter)
            
            # Draw playback cursor
            self.draw_cursor(painter)
            
            # Draw time labels
            self.draw_time_labels(painter)
    
    def draw_staff(self, painter):
        """Draw the 5-line staff"""
        pen = QPen(QColor("black"), 2)
        painter.setPen(pen)
        
        # Calculate staff position
        center_y = self.height() / 2
        
        # Draw 5 lines (standard staff) - start from left margin
        # Lines from bottom to top: E4, G4, B4, D5, F5
        for i in range(5):
            y = center_y - (2 * self.staff_spacing) + (i * self.staff_spacing)
            painter.drawLine(self.left_margin, int(y), self.width(), int(y))
        
        # Draw treble clef symbol - FIXED on the left, doesn't scroll
        # In Bravura/SMuFL, treble clef is Unicode E050
        painter.setFont(QFont(self.music_font_family, 80))
        clef_x = 10  # Fixed position
        clef_y = center_y - self.staff_spacing  # Position on second line from bottom (G4)
        painter.drawText(int(clef_x), int(clef_y + 50), "\uE050")
    
    def draw_notes(self, painter):
        """Draw all notes as ellipses"""
        drawn_count = 0
        playback_line_x = self.left_margin + 50  # Position of red line
        
        for note in self.notes:
            note_x = note['x'] - self.scroll_offset
            
            # Only draw notes that are visible and haven't passed the red line yet
            # Hide notes that are behind the playback line
            if note_x >= self.left_margin and note_x <= self.width() + 50:
                note_y = note['y']
                note_id = note['id']
                
                # Get finger assignment for this note
                finger = self.get_finger_for_note(note_id)
                finger_color = self.finger_colors.get(finger, QColor(128, 128, 128))
                
                # Choose color based on state - check if THIS specific note is active
                if note_id in self.active_note_ids:
                    color = finger_color  # Use finger color when playing
                    color = color.lighter(120)  # Brighten for visibility
                else:
                    color = finger_color  # Always use finger color
                
                # Draw ledger lines first (if needed)
                self.draw_ledger_lines(painter, note_x, note_y, 15)
                
                # Draw note head (filled ellipse, slightly tilted)
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(color, 1.5))
                
                # Note head size - smaller (wider than tall)
                note_width = 6
                note_height = 4.5
                painter.drawEllipse(QPointF(note_x, note_y), note_width, note_height)
                
                # Draw stem
                stem_height = 28
                stem_pen = QPen(color, 1.2)
                painter.setPen(stem_pen)
                
                if note['pitch'] >= 71:  # Stem down for notes on or above middle line (B4)
                    # Stem on left side of notehead, pointing down
                    stem_x = note_x - note_width + 0.5
                    painter.drawLine(int(stem_x), int(note_y),
                                   int(stem_x), int(note_y + stem_height))
                else:  # Stem up for lower notes
                    # Stem on right side of notehead, pointing up
                    stem_x = note_x + note_width - 0.5
                    painter.drawLine(int(stem_x), int(note_y),
                                   int(stem_x), int(note_y - stem_height))
                
                drawn_count += 1
        
        # Debug: show how many notes are visible
        painter.setPen(QPen(QColor("green"), 1))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, self.height() - 10, f"Notes: {drawn_count}/{len(self.notes)}")
    
    def draw_ledger_lines(self, painter, x, y, width):
        """Draw ledger lines for notes outside the staff"""
        center_y = self.height() / 2
        # Staff extends 2 lines above and below center
        staff_top = center_y - (2 * self.staff_spacing)
        staff_bottom = center_y + (2 * self.staff_spacing)
        
        painter.setPen(QPen(QColor("black"), 1.5))
        
        # Above staff (higher notes)
        if y < staff_top - self.staff_spacing / 2:
            line_y = staff_top - self.staff_spacing
            while line_y >= y - self.staff_spacing / 2:
                painter.drawLine(int(x - width), int(line_y),
                               int(x + width), int(line_y))
                line_y -= self.staff_spacing
        
        # Below staff (lower notes)
        elif y > staff_bottom + self.staff_spacing / 2:
            line_y = staff_bottom + self.staff_spacing
            while line_y <= y + self.staff_spacing / 2:
                painter.drawLine(int(x - width), int(line_y),
                               int(x + width), int(line_y))
                line_y += self.staff_spacing
    
    def draw_cursor(self, painter):
        """Draw vertical line showing current playback position"""
        # Red line is fixed at left margin + 50px
        cursor_x = self.left_margin + 50
        
        painter.setPen(QPen(QColor(255, 0, 0, 150), 3))
        painter.drawLine(int(cursor_x), 0, int(cursor_x), self.height())
    
    def draw_time_labels(self, painter):
        """Draw time markers"""
        painter.setPen(QPen(QColor("gray"), 1))
        painter.setFont(QFont("Arial", 10))
        
        # Draw time markers every second (accounting for preparation offset)
        start_time = -self.preparation_time
        for i in range(int(start_time), int(self.current_time) + 20):
            x = ((i + self.preparation_time) * self.pixels_per_second) - self.scroll_offset
            if self.left_margin <= x <= self.width():
                painter.drawText(int(x + 5), 20, f"{i}s")
    
    def draw_countdown(self, painter):
        """Draw countdown overlay (3... 2... 1...)"""
        # Semi-transparent overlay
        overlay = QColor(0, 0, 0, 180)
        painter.fillRect(self.rect(), overlay)
        
        # Draw countdown number
        painter.setPen(QPen(QColor("white"), 2))
        painter.setFont(QFont("Arial", 150, QFont.Weight.Bold))
        
        text = str(self.countdown_value)
        text_rect = painter.fontMetrics().boundingRect(text)
        
        # Center the text
        x = (self.width() - text_rect.width()) // 2
        y = (self.height() + text_rect.height()) // 2
        
        painter.drawText(x, y, text)
