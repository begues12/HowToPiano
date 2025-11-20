from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QFontDatabase
import mido
import os

class StaffWidget(QWidget):
    """Interactive musical staff that displays and highlights notes during playback"""
    
    # Signals emitted when notes cross the red line
    note_triggered = pyqtSignal(int, int)  # (pitch, velocity) - note should play
    note_ended = pyqtSignal(int)  # (pitch) - note should stop
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)
        self.setStyleSheet("background-color: #FFFEF9;")  # Warm cream background (professional score paper)
        
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
        self.played_note_color = QColor(30, 144, 255)  # Dodger blue (professional highlight)
        self.active_chord_id = None  # Currently active chord group
        self.current_time = 0  # Current playback time in seconds
        self.scroll_offset = 0  # Horizontal scroll position
        
        # Staff parameters
        self.base_staff_spacing = 15  # Base pixels between staff lines (at 100% zoom)
        self.staff_spacing = 15  # Current pixels between staff lines (scaled by zoom)
        self.visual_zoom_scale = 1.0  # Visual zoom multiplier (1.0 = 100%)
        self.top_margin = 100  # Professional spacing for tempo marking
        self.bottom_margin = 60  # Balanced bottom margin
        self.base_left_margin = 220  # Increased for clef + key signature + time signature
        self.left_margin = 220  # Current space for fixed clef (scaled by zoom)
        self.pixels_per_second = 100  # FIXED scrolling speed
        
        # Preparation time - controlled by settings.json (default 3 seconds)
        # This determines how far ahead of the red line the first note appears
        # distance = preparation_time * pixels_per_second (e.g., 3s * 100px/s = 300px)
        self.preparation_time = 3.0  # Default - will be overridden by settings
        
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
        
        # Red line triggering system
        self.triggered_notes = set()  # IDs of notes that have already been triggered
        self.last_check_time = -1.0  # Last time we checked for note triggers
        
        # Visual options
        self.show_note_colors = True  # Toggle for colored notes
        
        # Clef type
        self.clef_type = "grand"  # Options: "treble", "bass", "alto", "grand" (both staves)
        
        # Note name to MIDI number mapping
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Beam groups for connected eighth/sixteenth notes
        self.beam_groups = []  # List of lists: [[note_id1, note_id2, ...], ...]
        
        # Music notation metadata
        self.time_signature = (4, 4)  # (numerator, denominator) - 4/4 by default
        self.key_signature = 0  # Number of sharps (positive) or flats (negative)
        self.tempo_bpm = 120  # Beats per minute
        self.tempo_text = "Moderato"  # Tempo indication text
        self.piece_title = ""  # Title of the piece
        self.composer = ""  # Composer/author name
        
        # Spacing improvements for professional layout
        self.min_note_spacing = 35  # Base horizontal space between notes (will be scaled)
        self.use_proportional_spacing = True  # Use duration-based spacing
        self.chord_stack_offset = 2  # Minimal offset for chord notes (scaled by zoom)
        
    def load_midi_notes(self, midi_path):
        """Load notes from MIDI file"""
        try:
            mid = mido.MidiFile(midi_path)
            self.notes = []
            
            # Convert ticks to seconds
            tempo = 500000  # Default tempo (120 BPM)
            ticks_per_beat = mid.ticks_per_beat
            
            # Extract metadata from MIDI
            for track in mid.tracks:
                # Try to extract title and composer from track name
                if hasattr(track, 'name') and track.name:
                    if not self.piece_title and track.name.strip():
                        self.piece_title = track.name.strip()
                
                for msg in track:
                    if msg.type == 'set_tempo':
                        tempo = msg.tempo
                        self.tempo_bpm = int(60000000 / tempo)  # Convert microseconds to BPM
                        # Set tempo text based on BPM
                        if self.tempo_bpm < 60:
                            self.tempo_text = "Largo"
                        elif self.tempo_bpm < 76:
                            self.tempo_text = "Adagio"
                        elif self.tempo_bpm < 108:
                            self.tempo_text = "Andante"
                        elif self.tempo_bpm < 120:
                            self.tempo_text = "Moderato"
                        elif self.tempo_bpm < 168:
                            self.tempo_text = "Allegro"
                        else:
                            self.tempo_text = "Presto"
                    elif msg.type == 'time_signature':
                        self.time_signature = (msg.numerator, msg.denominator)
                    elif msg.type == 'key_signature':
                        # Key signature: number of sharps (positive) or flats (negative)
                        if hasattr(msg, 'key'):
                            # Convert to int if it's a string
                            try:
                                self.key_signature = int(msg.key) if isinstance(msg.key, str) else msg.key
                            except (ValueError, TypeError):
                                self.key_signature = 0
                        else:
                            self.key_signature = 0
                    elif msg.type == 'text' or msg.type == 'copyright':
                        # Try to find composer in copyright or text metadata
                        if hasattr(msg, 'text') and msg.text and not self.composer:
                            text = msg.text.strip()
                            if any(word in text.lower() for word in ['composer', 'by', 'autor', 'music']):
                                self.composer = text
            
            # If no title found, use filename
            if not self.piece_title:
                import os
                self.piece_title = os.path.splitext(os.path.basename(midi_path))[0]
            
            print(f"StaffWidget: '{self.piece_title}' by {self.composer if self.composer else 'Unknown'}")
            print(f"StaffWidget: Tempo = {self.tempo_bpm} BPM ({self.tempo_text}), Time signature = {self.time_signature[0]}/{self.time_signature[1]}")
            
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
            
            # Find the first note_on event to eliminate initial silence
            first_note_time = None
            for event in events:
                if event['type'] == 'note_on' and event['velocity'] > 0:
                    first_note_time = event['time']
                    break
            
            # Offset all events so first note starts at time 0
            time_offset = first_note_time if first_note_time is not None else 0
            if time_offset > 0:
                for event in events:
                    event['time'] -= time_offset
                print(f"StaffWidget: Removed {time_offset:.2f}s of initial silence")
            
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
                        
                        # Calculate position with proportional spacing
                        # Will be recalculated after all notes are loaded
                        x = (start_time + self.preparation_time) * self.pixels_per_second
                        y = self.pitch_to_y(event['note'])
                        
                        note_id = len(self.notes)  # Unique ID for this note
                        
                        # Determine accidental (sharp/flat/natural)
                        accidental = self._get_accidental(event['note'])
                        
                        self.notes.append({
                            'id': note_id,
                            'time': start_time,
                            'pitch': event['note'],
                            'duration': duration,
                            'x': x,
                            'y': y,
                            'accidental': accidental  # 'sharp', 'flat', 'natural', or None
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
            
            # Group notes for beaming (eighth and sixteenth notes that should be connected)
            self._create_beam_groups()
            
            # Apply proportional spacing based on note durations
            if self.use_proportional_spacing:
                self._apply_proportional_spacing()
            
            print(f"StaffWidget: Loaded {len(self.notes)} notes in {len(self.chords)} chords")
            if len(self.notes) > 0:
                print(f"StaffWidget: First note at time {self.notes[0]['time']:.2f}s, pitch {self.notes[0]['pitch']}")
                print(f"StaffWidget: Sample chord sizes: {[len(c['note_ids']) for c in self.chords[:5]]}")
            
            # Note positions are already calculated with FIXED preparation_time
            # No recalculation needed - positions are immutable after loading
            
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
        if self.clef_type == "grand":
            # Grand staff (two staves): split at Middle C (MIDI 60)
            # Treble staff (top): for notes >= B3 (MIDI 59) - slightly lower split for better distribution
            # Bass staff (bottom): for notes < B3 (59)
            
            # Compact grand staff positioning
            staff_gap = 3 * self.staff_spacing  # Gap between staves
            total_staff_height = 8 * self.staff_spacing + staff_gap  # 4 spaces per staff + gap
            
            treble_center_y = (self.height() - total_staff_height) / 2 + 2 * self.staff_spacing
            bass_center_y = treble_center_y + 4 * self.staff_spacing + staff_gap
            
            # Smart distribution: use treble for notes >= B3 (59)
            if midi_note >= 59:  # Use treble staff
                # Treble clef: B4 (MIDI 71) is on middle line
                reference_note = 71
                reference_y = treble_center_y
            else:  # Use bass staff
                # Bass clef: D3 (MIDI 50) is on middle line
                reference_note = 50
                reference_y = bass_center_y
            
            # Each half-step (semitone) moves by staff_spacing/2
            distance = reference_note - midi_note
            y = reference_y + (distance * self.staff_spacing / 2)
            
            return y
        else:
            # Single staff mode
            staff_center_y = self.height() / 2
            
            # Different clefs have different reference notes on the middle line
            if self.clef_type == "treble":
                reference_note = 71  # B4
            elif self.clef_type == "bass":
                reference_note = 50  # D3
            elif self.clef_type == "alto":
                reference_note = 60  # C4
            else:
                reference_note = 71  # Default to treble
            
            reference_y = staff_center_y
            
            # Each half-step (semitone) moves by staff_spacing/2
            distance = reference_note - midi_note
            y = reference_y + (distance * self.staff_spacing / 2)
            
            return y
    
    def resizeEvent(self, event):
        """Handle widget resize - recalculate note Y positions"""
        super().resizeEvent(event)
        
        # Recalculate Y positions for all notes since staff center changed
        if self.notes:
            for note in self.notes:
                note['y'] = self.pitch_to_y(note['pitch'])
            self.update()
    
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
    
    def _get_accidental(self, midi_note):
        """Determine if note needs an accidental (sharp, flat, or natural)"""
        # Get the note within an octave (0-11)
        note_in_octave = midi_note % 12
        
        # Black keys need accidentals
        # C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11
        black_keys = [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
        
        if note_in_octave in black_keys:
            # Display as sharp (could be made configurable to show flats)
            return 'sharp'
        
        return None  # No accidental needed for white keys
    
    def _apply_proportional_spacing(self):
        """Apply proportional spacing to notes based on their durations"""
        if not self.notes or len(self.notes) < 2:
            return
        
        print("StaffWidget: Applying proportional spacing...")
        
        # Calculate spacing multiplier based on note duration
        # Standard: quarter note = 1.0, eighth = 0.7, sixteenth = 0.5, half = 1.5, whole = 2.0
        def get_spacing_multiplier(duration):
            if duration >= 1.8:  # Whole note
                return 2.2
            elif duration >= 0.9:  # Half note
                return 1.6
            elif duration >= 0.4:  # Quarter note
                return 1.0
            elif duration >= 0.2:  # Eighth note
                return 0.7
            else:  # Sixteenth note and faster
                return 0.5
        
        # Recalculate X positions with proportional spacing
        cumulative_x = (self.notes[0]['time'] + self.preparation_time) * self.pixels_per_second
        self.notes[0]['x'] = cumulative_x
        
        # Base spacing (minimum distance between notes)
        base_spacing = self.min_note_spacing * self.visual_zoom_scale
        
        for i in range(1, len(self.notes)):
            prev_note = self.notes[i - 1]
            current_note = self.notes[i]
            
            # Time difference between notes
            time_gap = current_note['time'] - prev_note['time']
            
            # Check if this is part of a chord (notes at same time)
            is_chord = abs(time_gap) < 0.02  # 20ms tolerance
            
            if is_chord:
                # Chord notes: minimal horizontal spacing (stack vertically)
                # Slight offset based on pitch to avoid complete overlap
                pitch_diff = abs(current_note['pitch'] - prev_note['pitch'])
                chord_offset = min(pitch_diff * 0.5, 3) * self.visual_zoom_scale
                cumulative_x = prev_note['x'] + chord_offset
            else:
                # Calculate spacing based on previous note's duration
                prev_duration = prev_note['duration']
                spacing_multiplier = get_spacing_multiplier(prev_duration)
                
                # Additional spacing for time gap (but not too much)
                time_spacing = min(time_gap * self.pixels_per_second * 0.3, base_spacing * 2)
                
                # Total spacing: base + proportional + time gap
                total_spacing = base_spacing * spacing_multiplier + time_spacing
                cumulative_x = prev_note['x'] + total_spacing
            
            current_note['x'] = cumulative_x
        
        print(f"StaffWidget: Proportional spacing applied to {len(self.notes)} notes")
    
    def _create_beam_groups(self):
        """Group consecutive eighth and sixteenth notes for beaming based on metric structure"""
        self.beam_groups = []
        
        if not self.notes:
            return
        
        # Calculate beat duration (quarter note duration)
        beat_duration = 60.0 / self.tempo_bpm
        
        i = 0
        while i < len(self.notes):
            note = self.notes[i]
            duration = note['duration']
            
            # Check if this is an eighth or sixteenth note
            is_beamable = 0.1 <= duration < 0.5  # Eighth (0.2-0.4) and sixteenth (<0.2)
            
            if is_beamable:
                # Start a beam group
                beam_group = [note['id']]
                beam_start_time = note['time']
                j = i + 1
                
                # Determine which beat we're in (for proper grouping)
                current_beat = int(note['time'] / beat_duration) % self.time_signature[0]
                
                # Look for consecutive beamable notes within the same beat
                while j < len(self.notes):
                    next_note = self.notes[j]
                    next_duration = next_note['duration']
                    time_gap = next_note['time'] - beam_start_time
                    
                    # Check which beat the next note is in
                    next_beat = int(next_note['time'] / beat_duration) % self.time_signature[0]
                    
                    # Group notes within the same beat or consecutive beats (max 1 beat duration)
                    if (0.1 <= next_duration < 0.5 and 
                        time_gap < beat_duration and 
                        abs(next_beat - current_beat) <= 1):
                        beam_group.append(next_note['id'])
                        j += 1
                    else:
                        break
                
                # Only create beam group if we have 2+ notes
                if len(beam_group) >= 2:
                    self.beam_groups.append(beam_group)
                    i = j
                else:
                    i += 1
            else:
                i += 1
        
        print(f"StaffWidget: Created {len(self.beam_groups)} beam groups")
    
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
    
    def _check_and_trigger_notes(self, current_time):
        """Check if any notes are crossing the red line and trigger them"""
        if not self.notes:
            return
        
        # CRITICAL FIX: Don't trigger notes during preparation phase (negative time)
        # Notes need to "travel" visually before reaching the red line
        # Only start triggering when current_time >= 0
        if current_time < -0.01:  # Allow small tolerance for floating point
            return
        
        # Visual positions:
        # - Note X position: left_margin + (note_time + preparation_time) * pixels_per_second - scroll_offset
        # - Red line X position: left_margin + 50
        # - Scroll offset: (current_time + preparation_time) * pixels_per_second - 50
        #
        # Substituting:
        # note_x = left_margin + (note_time + preparation_time) * pixels_per_second - [(current_time + preparation_time) * pixels_per_second - 50]
        # note_x = left_margin + 50 + (note_time - current_time) * pixels_per_second
        #
        # For note to be AT red line: note_x = red_line_x
        # left_margin + 50 + (note_time - current_time) * pixels_per_second = left_margin + 50
        # (note_time - current_time) * pixels_per_second = 0
        # note_time = current_time ✓
        
        trigger_tolerance = 0.05  # 50ms tolerance for timing precision
        
        # Check each note
        for note in self.notes:
            note_time = note['time']
            note_id = note['id']
            note_end_time = note_time + note['duration']
            
            # The note should trigger when current playback time reaches the note's musical time
            # Check if note should start (reaches red line)
            if (current_time >= note_time - trigger_tolerance and 
                current_time < note_time + trigger_tolerance and
                note_id not in self.triggered_notes):
                
                # Trigger note ON
                self.triggered_notes.add(note_id)
                velocity = 80  # Default velocity
                self.note_triggered.emit(note['pitch'], velocity)
                
            # Check if note should end
            elif (current_time >= note_end_time - trigger_tolerance and
                  note_id in self.triggered_notes):
                
                # Trigger note OFF
                self.triggered_notes.discard(note_id)
                self.note_ended.emit(note['pitch'])
    
    def reset_triggers(self):
        """Reset all triggered notes (call when stopping/restarting playback)"""
        self.triggered_notes.clear()
        self.last_check_time = -1.0
    
    def go_to_start(self):
        """Reset to start position with preparation time offset"""
        # CRITICAL FIX: Start at negative time so notes have time to "travel"
        # This prevents notes from triggering immediately at time=0
        self.current_time = -self.preparation_time
        
        # Scroll to show beginning with preparation time visible
        # At negative time, notes will be visible but not yet at the red line
        self.scroll_offset = 0
        
        # Reset triggered notes
        self.reset_triggers()
        
        # Clear active notes
        self.active_note_ids.clear()
        
        self.update()
    
    def set_playback_time(self, time_sec):
        """Update current playback time and auto-scroll"""
        self.current_time = time_sec
        
        # Calculate where notes at this time should appear
        # Notes are positioned at: left_margin + (note_time + preparation_time) * pixels_per_second
        target_x = (time_sec + self.preparation_time) * self.pixels_per_second
        playback_line_x = self.left_margin + (50 * self.visual_zoom_scale)  # Position of red line, scaled
        
        # Only scroll when time is meaningful (not at start position)
        # Use 0.1s threshold to keep notes at preparation_time distance during initial frames
        if time_sec > 0.1:  # Don't scroll during first 100ms
            self.scroll_offset = target_x - playback_line_x
            self.scroll_offset = max(0, self.scroll_offset)
        # else: keep scroll_offset at 0 (set by go_to_start) to show preparation time
        
        # Check for notes crossing the red line and trigger them
        self._check_and_trigger_notes(time_sec)
        
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
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Professional cream paper background with subtle gradient
        painter.fillRect(self.rect(), QColor(255, 254, 249))  # #FFFEF9
        
        # If countdown is active, draw it over everything
        if self.countdown_active:
            self.draw_countdown(painter)
        else:
            # Draw header with title and composer
            self.draw_header(painter)
            
            # Draw staff lines
            self.draw_staff(painter)
            
            # Draw bar lines (measures)
            self.draw_barlines(painter)
            
            # Draw beams first (behind notes)
            self.draw_beams(painter)
            
            # Draw notes
            self.draw_notes(painter)
            
            # Draw playback cursor
            self.draw_cursor(painter)
            
            # Draw time labels
            self.draw_time_labels(painter)
    
    def draw_header(self, painter):
        """Draw professional header with title and composer"""
        if not self.piece_title:
            return
        
        header_y = 20 * self.visual_zoom_scale
        center_x = self.width() / 2
        
        # Draw subtle shadow for depth
        shadow_color = QColor(0, 0, 0, 15)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow_color)
        painter.drawRect(0, 0, self.width(), int(60 * self.visual_zoom_scale))
        
        # Draw title (centered, large, bold)
        title_font = QFont("Palatino Linotype", int(20 * self.visual_zoom_scale), QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        painter.setFont(title_font)
        painter.setPen(QColor(25, 25, 25))  # Almost black
        
        title_metrics = painter.fontMetrics()
        title_width = title_metrics.horizontalAdvance(self.piece_title)
        title_x = center_x - (title_width / 2)
        
        painter.drawText(int(title_x), int(header_y + 20 * self.visual_zoom_scale), self.piece_title)
        
        # Draw composer (centered, below title, italic)
        if self.composer:
            composer_font = QFont("Georgia", int(12 * self.visual_zoom_scale))
            composer_font.setItalic(True)
            painter.setFont(composer_font)
            painter.setPen(QColor(80, 80, 80))  # Medium gray
            
            composer_metrics = painter.fontMetrics()
            composer_width = composer_metrics.horizontalAdvance(self.composer)
            composer_x = center_x - (composer_width / 2)
            
            painter.drawText(int(composer_x), int(header_y + 42 * self.visual_zoom_scale), self.composer)
    
    def draw_staff(self, painter):
        """Draw the 5-line staff (or two staves for grand staff)"""
        # Professional staff line thickness with enhanced contrast
        pen = QPen(QColor(25, 25, 25), 1.3 * self.visual_zoom_scale)  # Darker for better contrast
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        
        clef_size = int(85 * self.visual_zoom_scale)  # Slightly larger clefs
        clef_x = 15 * self.visual_zoom_scale  # Better positioning
        
        if self.clef_type == "grand":
            # Draw TWO staves (Grand Staff) - Compact layout
            staff_gap = 3 * self.staff_spacing
            total_staff_height = 8 * self.staff_spacing + staff_gap
            
            treble_center_y = (self.height() - total_staff_height) / 2 + 2 * self.staff_spacing
            bass_center_y = treble_center_y + 4 * self.staff_spacing + staff_gap
            
            # Top staff: Treble clef
            for i in range(5):
                y = treble_center_y - (2 * self.staff_spacing) + (i * self.staff_spacing)
                painter.drawLine(self.left_margin, int(y), self.width(), int(y))
            
            # Draw treble clef with subtle shadow for depth
            painter.setFont(QFont(self.music_font_family, clef_size))
            treble_clef_y = treble_center_y - self.staff_spacing + (40 * self.visual_zoom_scale)
            
            # Shadow
            painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
            painter.drawText(int(clef_x + 1), int(treble_clef_y + 1), "\uE050")
            # Main clef
            painter.setPen(QPen(QColor(15, 15, 15), 1))
            painter.drawText(int(clef_x), int(treble_clef_y), "\uE050")
            
            # Bottom staff: Bass clef
            for i in range(5):
                y = bass_center_y - (2 * self.staff_spacing) + (i * self.staff_spacing)
                painter.drawLine(self.left_margin, int(y), self.width(), int(y))
            
            # Draw bass clef with shadow
            bass_clef_y = bass_center_y + self.staff_spacing + (20 * self.visual_zoom_scale)
            painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
            painter.drawText(int(clef_x + 1), int(bass_clef_y + 1), "\uE062")
            painter.setPen(QPen(QColor(15, 15, 15), 1))
            painter.drawText(int(clef_x), int(bass_clef_y), "\uE062")
            
            # Draw brace connecting the staves
            # Bravura brace: \uE000
            brace_size = int(90 * self.visual_zoom_scale)  # Smaller for compact layout
            painter.setFont(QFont(self.music_font_family, brace_size))
            brace_y = (treble_center_y + bass_center_y) / 2 + (25 * self.visual_zoom_scale)
            painter.drawText(int(5), int(brace_y), "\uE000")
            
            # Draw key signature, time signature, and tempo for both staves
            key_sig_x = clef_x + (70 * self.visual_zoom_scale)
            self.draw_key_signature(painter, key_sig_x, treble_center_y, "treble")
            self.draw_key_signature(painter, key_sig_x, bass_center_y, "bass")
            
            time_sig_x = key_sig_x + (40 * self.visual_zoom_scale)
            self.draw_time_signature(painter, time_sig_x, treble_center_y)
            self.draw_time_signature(painter, time_sig_x, bass_center_y)
            
            # Draw tempo indication above treble staff
            self.draw_tempo_marking(painter, time_sig_x + (50 * self.visual_zoom_scale), treble_center_y - (3 * self.staff_spacing))
            
        else:
            # Single staff mode
            staff_center_y = self.height() / 2
            
            # Draw 5 lines (standard staff)
            for i in range(5):
                y = staff_center_y - (2 * self.staff_spacing) + (i * self.staff_spacing)
                painter.drawLine(self.left_margin, int(y), self.width(), int(y))
            
            # Draw clef symbol
            painter.setFont(QFont(self.music_font_family, clef_size))
            
            if self.clef_type == "treble":
                clef_baseline_y = staff_center_y - self.staff_spacing + (40 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE050")
            elif self.clef_type == "bass":
                clef_baseline_y = staff_center_y + self.staff_spacing + (20 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE062")
            elif self.clef_type == "alto":
                clef_baseline_y = staff_center_y + (40 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE05C")
            
            # Draw key signature, time signature, and tempo
            key_sig_x = clef_x + (70 * self.visual_zoom_scale)
            self.draw_key_signature(painter, key_sig_x, staff_center_y, self.clef_type)
            
            time_sig_x = key_sig_x + (40 * self.visual_zoom_scale)
            self.draw_time_signature(painter, time_sig_x, staff_center_y)
            
            self.draw_tempo_marking(painter, time_sig_x + (50 * self.visual_zoom_scale), staff_center_y - (3 * self.staff_spacing))
    
    def draw_key_signature(self, painter, x, center_y, clef_type):
        """Draw key signature (sharps or flats)"""
        # Ensure key_signature is an integer
        try:
            key_sig = int(self.key_signature)
        except (ValueError, TypeError):
            key_sig = 0
        
        if key_sig == 0:
            return  # No accidentals in C major/A minor
        
        accidental_size = int(26 * self.visual_zoom_scale)  # Larger for better visibility
        painter.setFont(QFont(self.music_font_family, accidental_size))
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        
        # Positions for sharps and flats on treble/bass staff
        if clef_type == "treble":
            sharp_positions = [0, -1.5, 0.5, -1, 1, -0.5, 1.5]  # F C G D A E B (in staff_spacing units)
            flat_positions = [1.5, 0, 2, 0.5, 2.5, 1, 3]  # B E A D G C F
        elif clef_type == "bass":
            sharp_positions = [1, -0.5, 1.5, 0, 2, 0.5, 2.5]
            flat_positions = [2.5, 1, 3, 1.5, 3.5, 2, 4]
        else:  # alto
            sharp_positions = [0.5, -1, 1, -0.5, 1.5, 0, 2]
            flat_positions = [2, 0.5, 2.5, 1, 3, 1.5, 3.5]
        
        if key_sig > 0:
            # Draw sharps
            symbol = "\uE262"
            positions = sharp_positions[:key_sig]
        else:
            # Draw flats
            symbol = "\uE260"
            positions = flat_positions[:abs(key_sig)]
        
        for i, pos in enumerate(positions):
            acc_x = x + (i * 8 * self.visual_zoom_scale)
            acc_y = center_y + (pos * self.staff_spacing) + (5 * self.visual_zoom_scale)
            painter.drawText(int(acc_x), int(acc_y), symbol)
    
    def draw_time_signature(self, painter, x, center_y):
        """Draw time signature (e.g., 4/4, 3/4, 6/8)"""
        painter.setPen(QPen(QColor(20, 20, 20), 1))
        painter.setFont(QFont("Arial", int(26 * self.visual_zoom_scale), QFont.Weight.Bold))
        
        numerator = str(self.time_signature[0])
        denominator = str(self.time_signature[1])
        
        # Position numerator and denominator vertically centered on staff
        num_y = center_y - (self.staff_spacing * 0.7)
        den_y = center_y + (self.staff_spacing * 1.3)
        
        painter.drawText(int(x), int(num_y), numerator)
        painter.drawText(int(x), int(den_y), denominator)
    
    def draw_tempo_marking(self, painter, x, y):
        """Draw tempo indication (e.g., ♩ = 120, Allegro)"""
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        # Draw quarter note symbol and BPM
        painter.setFont(QFont(self.music_font_family, int(22 * self.visual_zoom_scale)))
        painter.drawText(int(x), int(y), "\uE1D5")  # Quarter note symbol
        
        painter.setFont(QFont("Arial", int(13 * self.visual_zoom_scale)))
        painter.drawText(int(x + 25 * self.visual_zoom_scale), int(y), f" = {self.tempo_bpm}")
        
        # Draw tempo text (Allegro, Moderato, etc.)
        painter.setFont(QFont("Arial", int(15 * self.visual_zoom_scale), QFont.Weight.Bold))
        painter.drawText(int(x + 75 * self.visual_zoom_scale), int(y), self.tempo_text)
    
    def draw_barlines(self, painter):
        """Draw vertical bar lines (measure divisions) with professional styling"""
        if self.clef_type == "grand":
            # Draw barlines through both staves
            staff_gap = 3 * self.staff_spacing
            total_staff_height = 8 * self.staff_spacing + staff_gap
            
            treble_center_y = (self.height() - total_staff_height) / 2 + 2 * self.staff_spacing
            bass_center_y = treble_center_y + 4 * self.staff_spacing + staff_gap
            
            treble_top = treble_center_y - (2 * self.staff_spacing)
            treble_bottom = treble_center_y + (2 * self.staff_spacing)
            bass_top = bass_center_y - (2 * self.staff_spacing)
            bass_bottom = bass_center_y + (2 * self.staff_spacing)
            
            # Calculate measure duration based on time signature and tempo
            # Duration = (beats_per_measure / BPM) * 60 seconds
            beats_per_measure = self.time_signature[0]
            measure_duration = (beats_per_measure / self.tempo_bpm) * 60
            
            # Draw initial barline at the start (thicker, professional)
            initial_x = self.left_margin - self.scroll_offset
            if initial_x >= self.left_margin - 10:
                painter.setPen(QPen(QColor(20, 20, 20), 2.5 * self.visual_zoom_scale))
                painter.drawLine(int(initial_x), int(treble_top), int(initial_x), int(bass_bottom))
            
            # Draw regular barlines with subtle shading
            painter.setPen(QPen(QColor(60, 60, 60), 1.3 * self.visual_zoom_scale))
            start_time = measure_duration
            max_time = (self.scroll_offset + self.width() - self.left_margin) / self.pixels_per_second
            
            current_time = measure_duration
            measure_count = 1
            while current_time <= max_time:
                x = self.left_margin + (current_time * self.pixels_per_second) - self.scroll_offset
                
                if x >= self.left_margin and x <= self.width():
                    # Subtle alternating measure shading for better readability
                    if measure_count % 2 == 0:
                        measure_start = self.left_margin + ((current_time - measure_duration) * self.pixels_per_second) - self.scroll_offset
                        measure_width = (current_time - (current_time - measure_duration)) * self.pixels_per_second
                        if measure_start >= self.left_margin:
                            painter.fillRect(int(measure_start), int(treble_top - 5), 
                                           int(measure_width), int(bass_bottom - treble_top + 10),
                                           QColor(245, 245, 242, 30))  # Very subtle gray
                    
                    # Draw barline
                    painter.setPen(QPen(QColor(60, 60, 60), 1.3 * self.visual_zoom_scale))
                    painter.drawLine(int(x), int(treble_top), int(x), int(bass_bottom))
                
                current_time += measure_duration
                measure_count += 1
            
            # Draw final barline if we have notes
            if self.notes:
                last_note_time = max(note['time'] + note['duration'] for note in self.notes)
                final_x = self.left_margin + ((last_note_time + 1) * self.pixels_per_second) - self.scroll_offset
                
                if final_x >= self.left_margin and final_x <= self.width() + 100:
                    # Double barline for end (professional finish)
                    painter.setPen(QPen(QColor(20, 20, 20), 1.5 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x), int(treble_top), int(final_x), int(bass_bottom))
                    painter.setPen(QPen(QColor(20, 20, 20), 5 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x + 6 * self.visual_zoom_scale), int(treble_top), 
                                   int(final_x + 6 * self.visual_zoom_scale), int(bass_bottom))
        else:
            # Single staff barlines
            staff_center_y = self.height() / 2
            top_y = staff_center_y - (2 * self.staff_spacing)
            bottom_y = staff_center_y + (2 * self.staff_spacing)
            
            beats_per_measure = self.time_signature[0]
            measure_duration = (beats_per_measure / self.tempo_bpm) * 60
            
            # Initial barline
            initial_x = self.left_margin - self.scroll_offset
            if initial_x >= self.left_margin - 10:
                painter.setPen(QPen(QColor(0, 0, 0), 2 * self.visual_zoom_scale))
                painter.drawLine(int(initial_x), int(top_y), int(initial_x), int(bottom_y))
            
            # Regular barlines
            painter.setPen(QPen(QColor(0, 0, 0), 1.5 * self.visual_zoom_scale))
            start_time = measure_duration
            max_time = (self.scroll_offset + self.width() - self.left_margin) / self.pixels_per_second
            
            current_time = measure_duration
            while current_time <= max_time:
                x = self.left_margin + (current_time * self.pixels_per_second) - self.scroll_offset
                
                if x >= self.left_margin and x <= self.width():
                    painter.drawLine(int(x), int(top_y), int(x), int(bottom_y))
                
                current_time += measure_duration
            
            # Final barline
            if self.notes:
                last_note_time = max(note['time'] + note['duration'] for note in self.notes)
                final_x = self.left_margin + ((last_note_time + 1) * self.pixels_per_second) - self.scroll_offset
                
                if final_x >= self.left_margin and final_x <= self.width() + 100:
                    painter.setPen(QPen(QColor(0, 0, 0), 1.5 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x), int(top_y), int(final_x), int(bottom_y))
                    painter.setPen(QPen(QColor(0, 0, 0), 4 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x + 5), int(top_y), int(final_x + 5), int(bottom_y))
    
    def draw_beams(self, painter):
        """Draw beams connecting eighth and sixteenth notes with proper slope"""
        for beam_group in self.beam_groups:
            if len(beam_group) < 2:
                continue
            
            # Get notes in this beam group
            beam_notes = [n for n in self.notes if n['id'] in beam_group]
            if not beam_notes:
                continue
            
            # Sort by time to ensure proper order
            beam_notes.sort(key=lambda n: n['time'])
            
            # Filter visible notes
            visible_notes = []
            for note in beam_notes:
                note_x = note['x'] - self.scroll_offset
                if self.left_margin - 50 <= note_x <= self.width() + 50:
                    visible_notes.append(note)
            
            if len(visible_notes) < 2:
                continue
            
            # Determine beam direction (up or down based on average pitch)
            avg_pitch = sum(n['pitch'] for n in visible_notes) / len(visible_notes)
            stem_down = avg_pitch >= 71
            
            # Calculate stem endpoints for all notes
            stem_height = 28 * self.visual_zoom_scale
            note_width = 6 * self.visual_zoom_scale
            
            stem_points = []
            for note in visible_notes:
                note_x = note['x'] - self.scroll_offset
                note_y = note['y']
                
                if stem_down:
                    stem_x = note_x - note_width  # Align to left edge
                    stem_end_y = note_y + stem_height
                else:
                    stem_x = note_x + note_width  # Align to right edge
                    stem_end_y = note_y - stem_height
                
                stem_points.append({
                    'x': stem_x,
                    'y': stem_end_y,
                    'note_y': note_y,
                    'duration': note['duration']
                })
            
            if len(stem_points) < 2:
                continue
            
            # Calculate beam slope intelligently based on melodic contour
            first_point = stem_points[0]
            last_point = stem_points[-1]
            
            # Calculate natural slope following the melody
            dx = last_point['x'] - first_point['x']
            if dx != 0:
                # Use weighted average of note positions for smoother beam
                if len(stem_points) > 2:
                    # Calculate center of gravity for better slope
                    total_weight = 0
                    weighted_y = 0
                    weighted_x = 0
                    
                    for point in stem_points:
                        weight = 1.0
                        total_weight += weight
                        weighted_y += point['y'] * weight
                        weighted_x += point['x'] * weight
                    
                    avg_y = weighted_y / total_weight
                    avg_x = weighted_x / total_weight
                    
                    # Calculate slope towards average
                    dy = last_point['y'] - first_point['y']
                    slope = dy / dx
                    
                    # Smooth the slope
                    slope = slope * 0.7  # Gentler slope
                else:
                    dy = last_point['y'] - first_point['y']
                    slope = dy / dx
                
                # Limit slope to prevent extreme angles (professional standard)
                max_slope = 0.25
                slope = max(-max_slope, min(max_slope, slope))
                
                # Flatten very small slopes (professional aesthetic)
                if abs(slope) < 0.05:
                    slope = 0
            else:
                slope = 0
            
            # Calculate beam Y position for each note based on slope
            beam_positions = []
            for point in stem_points:
                beam_y = first_point['y'] + slope * (point['x'] - first_point['x'])
                beam_positions.append((point['x'], beam_y, point['duration']))
            
            # Draw primary beam (thick line connecting all notes)
            if len(beam_positions) >= 2:
                beam_thickness = 4.5 * self.visual_zoom_scale
                beam_pen = QPen(QColor(30, 30, 30), beam_thickness)
                beam_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                painter.setPen(beam_pen)
                
                # Draw continuous beam
                x1 = beam_positions[0][0]
                y1 = beam_positions[0][1]
                x2 = beam_positions[-1][0]
                y2 = beam_positions[-1][1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                
                # Draw stems from notes to beam with professional thickness
                stem_pen = QPen(QColor(30, 30, 30), 1.4 * self.visual_zoom_scale)
                stem_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                painter.setPen(stem_pen)
                for i, point in enumerate(stem_points):
                    note_y = point['note_y']
                    stem_x = point['x']
                    beam_y = beam_positions[i][1]
                    
                    painter.drawLine(int(stem_x), int(note_y), int(stem_x), int(beam_y))
                
                # Draw secondary beams for sixteenth notes (duration < 0.2)
                # Professional spacing: 1 staff space (1/4 of staff height)
                beam_spacing = self.staff_spacing / 2  # Half a staff space
                secondary_offset = beam_spacing if stem_down else -beam_spacing
                
                i = 0
                while i < len(beam_positions):
                    duration = beam_positions[i][2]
                    
                    if duration < 0.2:  # Sixteenth note
                        # Find consecutive sixteenth notes
                        j = i
                        while j < len(beam_positions) and beam_positions[j][2] < 0.2:
                            j += 1
                        
                        # Draw secondary beam for this group
                        if j > i:
                            sec_x1 = beam_positions[i][0]
                            sec_y1 = beam_positions[i][1] + secondary_offset
                            sec_x2 = beam_positions[j-1][0]
                            sec_y2 = beam_positions[j-1][1] + secondary_offset
                            
                            painter.setPen(QPen(QColor(0, 0, 0), beam_thickness))
                            painter.drawLine(int(sec_x1), int(sec_y1), int(sec_x2), int(sec_y2))
                        
                        i = j
                    else:
                        i += 1
    
    def draw_time_divisions(self, painter):
        """Draw vertical time division lines"""
        center_y = self.height() / 2
        top_y = center_y - (2 * self.staff_spacing)
        bottom_y = center_y + (2 * self.staff_spacing)
        
        # Draw time markers every 5 seconds
        marker_interval = 5  # seconds
        
        # Calculate which markers are visible
        start_time = max(0, int(self.scroll_offset / self.pixels_per_second / marker_interval) * marker_interval)
        end_time = int((self.scroll_offset + self.width()) / self.pixels_per_second) + marker_interval
        
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setFont(QFont("Arial", 9))
        
        for time_sec in range(start_time, end_time, marker_interval):
            x = self.left_margin + (time_sec * self.pixels_per_second) - self.scroll_offset
            
            if x >= self.left_margin and x <= self.width():
                # Draw vertical line through staff
                painter.drawLine(int(x), int(top_y), int(x), int(bottom_y))
                
                # Draw time label below staff
                minutes = int(time_sec // 60)
                seconds = int(time_sec % 60)
                time_text = f"{minutes}:{seconds:02d}"
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawText(int(x - 15), int(bottom_y + 20), time_text)
                painter.setPen(QPen(QColor(200, 200, 200), 1))
    
    def draw_notes(self, painter):
        """Draw all notes as ellipses"""
        drawn_count = 0
        remaining_count = 0  # Notes that haven't been played yet
        playback_line_x = self.left_margin + (50 * self.visual_zoom_scale)  # Position of red line, scaled
        
        for note in self.notes:
            note_x = note['x'] - self.scroll_offset
            
            # Count notes that haven't passed the red line yet
            if note_x >= playback_line_x:
                remaining_count += 1
            
            # Only draw notes that are visible on screen
            if note_x >= self.left_margin and note_x <= self.width() + 50:
                note_y = note['y']
                note_id = note['id']
                
                # Get finger assignment for this note
                finger = self.get_finger_for_note(note_id)
                finger_color = self.finger_colors.get(finger, QColor(128, 128, 128))
                
                # Choose color based on settings and state
                if note_id in self.active_note_ids:
                    # Use configured played note color when active (bright and visible)
                    color = self.played_note_color
                    # Add glow effect for active notes
                    glow_color = QColor(self.played_note_color.red(), 
                                      self.played_note_color.green(), 
                                      self.played_note_color.blue(), 50)
                    painter.setPen(QPen(glow_color, 8 * self.visual_zoom_scale))
                    painter.drawEllipse(QPointF(note_x, note_y), 
                                      12 * self.visual_zoom_scale, 
                                      9 * self.visual_zoom_scale)
                elif self.show_note_colors:
                    # Use finger colors when not playing
                    color = finger_color
                else:
                    # Use professional black for all notes
                    color = QColor(30, 30, 30)
                
                # Draw ledger lines first (if needed)
                # Adjust ledger width for chord notes
                chord_id = note.get('chord_id')
                chord = next((c for c in self.chords if c['id'] == chord_id), None) if chord_id is not None else None
                is_in_chord = chord and len(chord['note_ids']) > 1
                
                ledger_width = (18 if is_in_chord else 15) * self.visual_zoom_scale
                self.draw_ledger_lines(painter, note_x, note_y, ledger_width)
                
                # Draw accidental (sharp/flat) if needed
                accidental = note.get('accidental')
                if accidental:
                    self.draw_accidental(painter, note_x, note_y, accidental, color)
                
                # Check if note is in a beam group
                in_beam_group = any(note_id in group for group in self.beam_groups)
                
                # For chords, slightly adjust X position for visual clarity
                adjusted_x = note_x
                if is_in_chord and chord:
                    # Find position in chord
                    note_index = chord['note_ids'].index(note_id)
                    if note_index > 0:
                        # Alternate positioning for readability
                        if note_index % 2 == 1:
                            adjusted_x = note_x + (1 * self.visual_zoom_scale)
                
                # Draw note based on duration
                self.draw_note_shape(painter, adjusted_x, note_y, note['duration'], note['pitch'], color, note_id, in_beam_group)
                
                drawn_count += 1
        
        # Show progress in a more professional way
        played_count = len(self.notes) - remaining_count
        progress_percent = int((played_count / len(self.notes) * 100)) if len(self.notes) > 0 else 0
        
        # Draw subtle progress bar
        bar_width = 150
        bar_height = 6
        bar_x = self.width() - bar_width - 15
        bar_y = self.height() - 25
        
        # Background bar
        painter.fillRect(int(bar_x), int(bar_y), bar_width, bar_height, QColor(220, 220, 220))
        # Progress bar
        painter.fillRect(int(bar_x), int(bar_y), int(bar_width * progress_percent / 100), bar_height, QColor(100, 180, 100))
        
        # Progress text
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(int(bar_x), int(bar_y - 5), f"{played_count}/{len(self.notes)} notes ({progress_percent}%)")
    
    def draw_accidental(self, painter, x, y, accidental_type, color):
        """Draw sharp, flat, or natural symbol before the note"""
        # Bravura/SMuFL Unicode codes:
        # Sharp: \uE262
        # Flat: \uE260
        # Natural: \uE261
        
        accidental_size = int(22 * self.visual_zoom_scale)  # Slightly larger
        painter.setFont(QFont(self.music_font_family, accidental_size))
        # Use slightly darker color for better contrast
        acc_color = QColor(min(color.red() + 20, 255), 
                          min(color.green() + 20, 255), 
                          min(color.blue() + 20, 255)) if color != QColor(30, 30, 30) else QColor(30, 30, 30)
        painter.setPen(QPen(acc_color, 1))
        
        # Position accidental to the left of note
        accidental_x = x - (12 * self.visual_zoom_scale)
        accidental_y = y + (5 * self.visual_zoom_scale)
        
        if accidental_type == 'sharp':
            painter.drawText(int(accidental_x), int(accidental_y), "\uE262")
        elif accidental_type == 'flat':
            painter.drawText(int(accidental_x), int(accidental_y), "\uE260")
        elif accidental_type == 'natural':
            painter.drawText(int(accidental_x), int(accidental_y), "\uE261")
    
    def draw_note_shape(self, painter, x, y, duration, pitch, color, note_id=None, in_beam_group=False):
        """Draw note with appropriate shape based on duration"""
        # Note dimensions (scaled by zoom) - professional proportions
        note_width = 6.5 * self.visual_zoom_scale  # Slightly wider for better visibility
        note_height = 5 * self.visual_zoom_scale  # Better proportion
        stem_height = 30 * self.visual_zoom_scale  # Standard 3.5 staff spaces
        
        # Determine note type based on duration (in seconds)
        # Assuming 120 BPM (quarter note = 0.5s) as reference
        # Whole note: 2.0s, Half: 1.0s, Quarter: 0.5s, Eighth: 0.25s, Sixteenth: 0.125s
        
        is_whole = duration >= 1.8  # Whole note (redonda)
        is_half = 0.9 <= duration < 1.8  # Half note (blanca)
        is_quarter = 0.4 <= duration < 0.9  # Quarter note (negra)
        is_eighth = 0.2 <= duration < 0.4  # Eighth note (corchea)
        is_sixteenth = duration < 0.2  # Sixteenth note (semicorchea)
        
        # Whole note - hollow oval, no stem (professional proportions)
        if is_whole:
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            painter.setPen(QPen(color, 2.2 * self.visual_zoom_scale))
            # Professional whole note proportions: wider and more oval
            whole_width = note_width * 1.4
            whole_height = note_height * 1.2
            painter.drawEllipse(QPointF(x, y), whole_width, whole_height)
            return
        
        # Half note - hollow head with stem (crisp outline)
        if is_half:
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            painter.setPen(QPen(color, 2.0 * self.visual_zoom_scale))
            painter.drawEllipse(QPointF(x, y), note_width, note_height)
        else:
            # Quarter, eighth, sixteenth - filled head with smooth edges
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1.2 * self.visual_zoom_scale))
            painter.drawEllipse(QPointF(x, y), note_width, note_height)
        
        # Draw stem (for all except whole notes) with proper alignment
        stem_pen = QPen(color, 1.5 * self.visual_zoom_scale)  # Slightly thicker
        stem_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(stem_pen)
        
        stem_down = pitch >= 71  # Stem down for notes on or above middle line (B4)
        
        if stem_down:
            # Stem on left side, pointing down
            # Position at the left edge of the note head for proper alignment
            stem_x = x - note_width
            stem_top_y = y  # Start exactly at note center
            stem_bottom_y = y + stem_height
            painter.drawLine(int(stem_x), int(stem_top_y), int(stem_x), int(stem_bottom_y))
            
            # Add flag(s) for eighth and sixteenth notes (only if not in beam group)
            if (is_eighth or is_sixteenth) and not in_beam_group:
                flag_start_x = stem_x
                flag_start_y = stem_bottom_y
                
                # Professional flag curvature using bezier-like curve
                painter.setPen(QPen(color, 2.2 * self.visual_zoom_scale))
                
                # First flag (eighth note)
                flag_points = []
                flag_points.append(QPointF(flag_start_x, flag_start_y))
                flag_points.append(QPointF(flag_start_x + 3 * self.visual_zoom_scale, flag_start_y - 2 * self.visual_zoom_scale))
                flag_points.append(QPointF(flag_start_x + 6 * self.visual_zoom_scale, flag_start_y - 4 * self.visual_zoom_scale))
                flag_points.append(QPointF(flag_start_x + 9 * self.visual_zoom_scale, flag_start_y - 6 * self.visual_zoom_scale))
                
                for i in range(len(flag_points) - 1):
                    painter.drawLine(flag_points[i], flag_points[i + 1])
                
                if is_sixteenth:
                    # Second flag for sixteenth (parallel but slightly offset)
                    flag2_start_y = flag_start_y - (5.5 * self.visual_zoom_scale)
                    flag2_points = []
                    flag2_points.append(QPointF(flag_start_x, flag2_start_y))
                    flag2_points.append(QPointF(flag_start_x + 3 * self.visual_zoom_scale, flag2_start_y - 2 * self.visual_zoom_scale))
                    flag2_points.append(QPointF(flag_start_x + 6 * self.visual_zoom_scale, flag2_start_y - 4 * self.visual_zoom_scale))
                    flag2_points.append(QPointF(flag_start_x + 9 * self.visual_zoom_scale, flag2_start_y - 6 * self.visual_zoom_scale))
                    
                    for i in range(len(flag2_points) - 1):
                        painter.drawLine(flag2_points[i], flag2_points[i + 1])
        else:
            # Stem on right side, pointing up
            # Position at the right edge of the note head for proper alignment
            stem_x = x + note_width
            stem_top_y = y - stem_height
            stem_bottom_y = y  # End exactly at note center
            painter.drawLine(int(stem_x), int(stem_top_y), int(stem_x), int(stem_bottom_y))
            
            # Add flag(s) for eighth and sixteenth notes (only if not in beam group)
            if (is_eighth or is_sixteenth) and not in_beam_group:
                flag_start_x = stem_x
                flag_start_y = stem_top_y
                
                # Professional flag curvature pointing downward (for stems up)
                painter.setPen(QPen(color, 2.2 * self.visual_zoom_scale))
                
                # First flag (eighth note)
                flag_points = []
                flag_points.append(QPointF(flag_start_x, flag_start_y))
                flag_points.append(QPointF(flag_start_x + 3 * self.visual_zoom_scale, flag_start_y + 2 * self.visual_zoom_scale))
                flag_points.append(QPointF(flag_start_x + 6 * self.visual_zoom_scale, flag_start_y + 4 * self.visual_zoom_scale))
                flag_points.append(QPointF(flag_start_x + 9 * self.visual_zoom_scale, flag_start_y + 6 * self.visual_zoom_scale))
                
                for i in range(len(flag_points) - 1):
                    painter.drawLine(flag_points[i], flag_points[i + 1])
                
                if is_sixteenth:
                    # Second flag for sixteenth (parallel but slightly offset)
                    flag2_start_y = flag_start_y + (5.5 * self.visual_zoom_scale)
                    flag2_points = []
                    flag2_points.append(QPointF(flag_start_x, flag2_start_y))
                    flag2_points.append(QPointF(flag_start_x + 3 * self.visual_zoom_scale, flag2_start_y + 2 * self.visual_zoom_scale))
                    flag2_points.append(QPointF(flag_start_x + 6 * self.visual_zoom_scale, flag2_start_y + 4 * self.visual_zoom_scale))
                    flag2_points.append(QPointF(flag_start_x + 9 * self.visual_zoom_scale, flag2_start_y + 6 * self.visual_zoom_scale))
                    
                    for i in range(len(flag2_points) - 1):
                        painter.drawLine(flag2_points[i], flag2_points[i + 1])
    
    def draw_ledger_lines(self, painter, x, y, width):
        """Draw ledger lines for notes outside the staff"""
        ledger_pen = QPen(QColor(40, 40, 40), 1.3 * self.visual_zoom_scale)
        ledger_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(ledger_pen)
        
        if self.clef_type == "grand":
            # For grand staff, determine which staff this note belongs to
            staff_gap = 3 * self.staff_spacing
            total_staff_height = 8 * self.staff_spacing + staff_gap
            
            treble_center_y = (self.height() - total_staff_height) / 2 + 2 * self.staff_spacing
            bass_center_y = treble_center_y + 4 * self.staff_spacing + staff_gap
            
            # Determine if note is in treble or bass range based on position
            middle_point = (treble_center_y + bass_center_y) / 2
            if y < middle_point:  # Treble staff area
                staff_center_y = treble_center_y
            else:  # Bass staff area
                staff_center_y = bass_center_y
            
            staff_top = staff_center_y - (2 * self.staff_spacing)
            staff_bottom = staff_center_y + (2 * self.staff_spacing)
        else:
            # Single staff
            staff_center_y = self.height() / 2
            staff_top = staff_center_y - (2 * self.staff_spacing)
            staff_bottom = staff_center_y + (2 * self.staff_spacing)
        
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
        """Draw vertical line showing current playback position with current measure highlight"""
        cursor_x = self.left_margin + (50 * self.visual_zoom_scale)
        
        # Highlight current measure
        if self.clef_type == "grand":
            staff_gap = 3 * self.staff_spacing
            total_staff_height = 8 * self.staff_spacing + staff_gap
            treble_center_y = (self.height() - total_staff_height) / 2 + 2 * self.staff_spacing
            bass_center_y = treble_center_y + 4 * self.staff_spacing + staff_gap
            treble_top = treble_center_y - (2 * self.staff_spacing)
            bass_bottom = bass_center_y + (2 * self.staff_spacing)
        else:
            staff_center_y = self.height() / 2
            treble_top = staff_center_y - (2 * self.staff_spacing)
            bass_bottom = staff_center_y + (2 * self.staff_spacing)
        
        # Calculate current measure boundaries
        beats_per_measure = self.time_signature[0]
        measure_duration = (beats_per_measure / self.tempo_bpm) * 60
        current_measure = int(self.current_time / measure_duration)
        measure_start_time = current_measure * measure_duration
        measure_end_time = (current_measure + 1) * measure_duration
        
        # Draw subtle highlight for current measure
        measure_start_x = self.left_margin + (measure_start_time * self.pixels_per_second) - self.scroll_offset
        measure_end_x = self.left_margin + (measure_end_time * self.pixels_per_second) - self.scroll_offset
        
        if measure_start_x < self.width() and measure_end_x > self.left_margin:
            painter.fillRect(int(max(measure_start_x, self.left_margin)), int(treble_top - 10),
                           int(measure_end_x - max(measure_start_x, self.left_margin)), 
                           int(bass_bottom - treble_top + 20),
                           QColor(100, 150, 200, 35))  # Subtle blue-gray with better contrast
        
        # Draw playback cursor with glow effect for better visibility
        # Outer glow
        glow_pen = QPen(QColor(220, 60, 80, 60), 6 * self.visual_zoom_scale)
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawLine(int(cursor_x), int(treble_top - self.staff_spacing), 
                        int(cursor_x), int(bass_bottom + self.staff_spacing))
        
        # Main cursor line
        cursor_pen = QPen(QColor(200, 30, 50), 2.5 * self.visual_zoom_scale)  # Deep crimson
        cursor_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(cursor_pen)
        painter.drawLine(int(cursor_x), int(treble_top - self.staff_spacing), 
                        int(cursor_x), int(bass_bottom + self.staff_spacing))
    
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
