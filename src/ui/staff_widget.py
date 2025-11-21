from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QFontDatabase
from src.ui.note_widget import NoteWidget, SongWidget, NoteType
from src.core.timing_sync import TimingSyncManager
import mido
import os
import time

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
        self.current_time = -3  # Current playback time in seconds (will be set to -preparation_time on load)
        self.scroll_offset = 0  # DEPRECATED: No longer used in new coordinate system
        
        # Staff parameters
        self.base_staff_spacing = 15  # Base pixels between staff lines (at 100% zoom)
        self.staff_spacing = 15  # Current pixels between staff lines (scaled by zoom)
        self.visual_zoom_scale = 1.0  # Visual zoom multiplier (1.0 = 100%)
        self.top_margin = 100  # Professional spacing for tempo marking
        self.bottom_margin = 60  # Balanced bottom margin
        self.base_left_margin = 160  # Space for clef + key signature + time signature
        self.left_margin = 160  # Current space for fixed clef (scaled by zoom)
        self.base_pixels_per_second = 100  # Base scrolling speed at 120 BPM
        self.pixels_per_second = 100  # Actual scrolling speed (adjusted by tempo)
        
        # Preparation time - controlled by settings.json (default 3 seconds)
        # This determines how far ahead of the red line the first note appears
        # distance = preparation_time * pixels_per_second (e.g., 3s * 100px/s = 300px)
        self.preparation_time = 3.0  # Default - will be overridden by settings
        
        # Audio latency compensation with automatic sync management
        # This ensures notes visually arrive at the red line EXACTLY when they sound
        self.audio_latency_ms = 12  # Initial milliseconds
        self.audio_latency_sec = self.audio_latency_ms / 1000.0  # Convert to seconds
        
        # NEW: Automatic timing synchronization system
        self.timing_sync = TimingSyncManager(initial_latency=self.audio_latency_sec)
        self.sync_check_interval = 60  # Check every 60 frames (~1 second at 60fps)
        self.sync_check_counter = 0
        
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
        
        # Real-time playback logging
        self.playback_log_file = None
        self.playback_logging_enabled = False
        
        # Red line triggering system
        self.triggered_notes = set()  # IDs of notes that have already been triggered
        self.last_check_time = -1.0  # Last time we checked for note triggers
        
        # Visual options
        self.show_note_colors = True  # Toggle for colored notes
        
        # Clef type
        self.clef_type = "grand"  # Options: "treble", "bass", "alto", "tenor", "soprano", "mezzosoprano", "baritone", "grand" (both staves)
        
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
        self.min_note_spacing = 60  # Base horizontal space between notes (will be scaled)
        self.use_proportional_spacing = True  # Use duration-based spacing
        self.chord_stack_offset = 2  # Minimal offset for chord notes (scaled by zoom)
        
        # NEW: SongWidget for advanced note management
        self.song_widget = SongWidget(tempo=self.tempo_bpm, time_signature=self.time_signature)
        self.song_widget.note_triggered.connect(self._on_note_triggered)
        self.song_widget.note_ended.connect(self._on_note_ended)
        
    def export_midi_notes_to_txt(self, midi_path, output_path):
        """Export all notes from MIDI to TXT file with T and pitch"""
        try:
            mid = mido.MidiFile(midi_path)
            tempo = 500000  # Default tempo (120 BPM)
            
            # Extract tempo
            for track in mid.tracks:
                for msg in track:
                    if hasattr(msg, 'type') and msg.type == 'set_tempo':
                        tempo = msg.tempo
                        break
            
            # Collect all notes
            all_notes = []
            for track_idx, track in enumerate(mid.tracks):
                current_tick = 0
                current_tempo = tempo
                
                for msg in track:
                    # Get delta safely (some messages might not have it)
                    delta = getattr(msg, 'delta', 0)
                    current_tick += delta
                    time_sec = mido.tick2second(current_tick, mid.ticks_per_beat, current_tempo)
                    
                    if hasattr(msg, 'type'):
                        if msg.type == 'set_tempo':
                            current_tempo = msg.tempo
                        elif msg.type == 'note_on' and hasattr(msg, 'velocity') and msg.velocity > 0:
                            all_notes.append({
                                'time': time_sec,
                                'pitch': msg.note,
                                'velocity': msg.velocity
                            })
            
            # Sort by time
            all_notes.sort(key=lambda x: x['time'])
            
            # Write to TXT file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# MIDI Notes Export\n")
                f.write("# Format: T (seconds) | Pitch (MIDI note number) | Velocity\n")
                f.write("# " + "="*60 + "\n\n")
                
                for note in all_notes:
                    f.write(f"T={note['time']:.4f}s | Pitch={note['pitch']} | Vel={note['velocity']}\n")
            
            print(f"Exported {len(all_notes)} notes to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting MIDI notes: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_midi_notes(self, midi_path):
        """Load notes from MIDI file"""
        try:
            # Export notes to TXT automatically
            
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
            
            # CRITICAL: Adjust scroll speed based on tempo AND zoom
            # Base speed is 100 px/s at 120 BPM and 100% zoom (reference)
            # Formula: pixels_per_second = base * (tempo / 120) * zoom_scale
            # Fast tempo (180 BPM) -> 150 px/s (faster scroll)
            # Slow tempo (60 BPM) -> 50 px/s (slower scroll)
            tempo_factor = self.tempo_bpm / 120.0
            self.pixels_per_second = self.base_pixels_per_second * tempo_factor * self.visual_zoom_scale
            print(f"StaffWidget: Scroll speed adjusted to {self.pixels_per_second:.1f} px/s (tempo={self.tempo_bpm}, zoom={self.visual_zoom_scale*100:.0f}%)")
            
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
            
            # Log notes loaded (X positions not needed for time-based triggering)
            print(f"StaffWidget: Loaded {len(self.notes)} notes in {len(self.chords)} chords")
            # if self.notes:
            #     print(f"[STAFF] First note: time={self.notes[0]['time']:.3f}s, pitch={self.notes[0]['pitch']}, x={self.notes[0]['x']:.1f}")
            #     if len(self.notes) > 1:
            #         print(f"[STAFF] Second note: time={self.notes[1]['time']:.3f}s, pitch={self.notes[1]['pitch']}, x={self.notes[1]['x']:.1f}")
            if len(self.notes) > 0:
                print(f"StaffWidget: First note at time {self.notes[0]['time']:.2f}s, pitch {self.notes[0]['pitch']}")
                print(f"StaffWidget: Sample chord sizes: {[len(c['note_ids']) for c in self.chords[:5]]}")
            
            # Note positions are already calculated with FIXED preparation_time
            # No recalculation needed - positions are immutable after loading
            
            # Assign fingers based on note positions
            self._assign_fingers_to_notes()
            
            # NEW: Convert to NoteWidget system
            self._convert_notes_to_widgets()
            
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
                reference_note = 71  # B4 (middle line)
            elif self.clef_type == "bass":
                reference_note = 50  # D3 (middle line)
            elif self.clef_type == "alto":
                reference_note = 60  # C4 (middle line) - Alto/Viola clef
            elif self.clef_type == "tenor":
                reference_note = 57  # A3 (middle line) - Tenor clef
            elif self.clef_type == "soprano":
                reference_note = 60  # C4 (1st line) - Soprano clef
            elif self.clef_type == "mezzosoprano":
                reference_note = 57  # A3 (2nd line) - Mezzosoprano clef
            elif self.clef_type == "baritone":
                reference_note = 53  # F3 (middle line) - Baritone clef
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
    
    # Proportional spacing removed - using pure time-based triggering
    
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
    
    def _convert_notes_to_widgets(self):
        """
        Convert old-style dict notes to new NoteWidget system.
        Called after load_midi_notes() to populate song_widget.
        """
        self.song_widget.clear_notes()
        
        for note_dict in self.notes:
            # Determine note type based on duration
            duration = note_dict['duration']
            
            # Calculate beats (assuming 4/4 time and 120 BPM as base)
            beats = duration * (self.tempo_bpm / 60.0)
            
            # Map duration to note type
            if beats >= 3.5:
                note_type = NoteType.WHOLE
            elif beats >= 1.75:
                note_type = NoteType.HALF
            elif beats >= 0.875:
                note_type = NoteType.QUARTER
            elif beats >= 0.4375:
                note_type = NoteType.EIGHTH
            elif beats >= 0.21875:
                note_type = NoteType.SIXTEENTH
            else:
                note_type = NoteType.THIRTYSECOND
            
            # Create NoteWidget
            note_widget = NoteWidget(
                pitch=note_dict['pitch'],
                start_time=note_dict['time'],
                duration=duration,
                velocity=80,  # Default velocity
                note_type=note_type
            )
            
            # Copy finger assignment if exists
            # DISABLED: User doesn't want finger numbers displayed
            # if note_dict['id'] in self.note_fingers:
            #     note_widget.finger = self.note_fingers[note_dict['id']]
            
            # Store original note_id for tracking
            note_widget._old_id = note_dict['id']
            
            self.song_widget.add_note(note_widget)
        
        print(f"StaffWidget: Converted {len(self.notes)} notes to NoteWidget system")
    
    def _on_note_triggered(self, pitch, velocity):
        """Callback when a note should start playing (from SongWidget)"""
        # Find the note that was triggered for timing measurement
        for note_widget in self.song_widget.notes:
            if note_widget.pitch == pitch and note_widget.is_played:
                # Record timing for synchronization
                self.timing_sync.record_note_timing(
                    scheduled_time=note_widget.start_time,
                    actual_time=time.time(),
                    visual_time=self.current_time
                )
                break
        
        self.note_triggered.emit(pitch, velocity)
    
    def _on_note_ended(self, pitch):
        """Callback when a note should stop playing (from SongWidget)"""
        self.note_ended.emit(pitch)
    
    def _check_and_trigger_notes(self, current_time):
        """
        TIME-BASED NOTE TRIGGER SYSTEM
        
        Uses ONLY musical time from MIDI file to trigger notes.
        No visual position calculations - pure time synchronization.
        
        Formula: Trigger when current_time >= note_time
        
        IMPORTANT: Compensates for audio buffer latency (~12ms) so notes
        are triggered slightly EARLY to arrive at speakers precisely on beat.
        """
        if not self.notes:
            return
        
        # Tolerance for timing (50ms window to catch notes)
        trigger_tolerance = 0.050
        
        # CRITICAL: Pre-trigger notes by audio latency amount
        # This ensures sound arrives at speakers EXACTLY when note crosses red line
        trigger_time = current_time + self.audio_latency_sec
        
        for note in self.notes:
            note_id = note['id']
            note_time = note['time']
            note_duration = note['duration']
            note_end_time = note_time + note_duration
            
            # Skip notes far in the past (beyond their end time + 1 second buffer)
            if note_end_time < current_time - 1.0:
                continue
            
            # Skip notes far in the future that haven't started yet
            # BUT: Don't skip if note is already triggered (needs to check for end)
            if note_time > current_time + trigger_tolerance and note_id not in self.triggered_notes:
                continue
            
            # === NOTE ON LOGIC ===
            # Trigger when current time + latency reaches note time
            # This pre-triggers the note so it sounds EXACTLY when crossing red line
            if (note_time <= trigger_time <= note_time + trigger_tolerance and
                note_id not in self.triggered_notes):
                
                # Mark as triggered
                self.triggered_notes.add(note_id)
                
                # Play sound (will reach speakers in ~12ms, perfectly synced with visual)
                velocity = 80
                self.note_triggered.emit(note['pitch'], velocity)
                
                # Log to real-time playback file if enabled
                if self.playback_logging_enabled and self.playback_log_file:
                    try:
                        self.playback_log_file.write(f"NOTE_ON | T={current_time:.4f}s | Pitch={note['pitch']} | Scheduled={note_time:.4f}s | PreTrigger={self.audio_latency_ms}ms | Diff={(trigger_time-note_time)*1000:.1f}ms\n")
                        self.playback_log_file.flush()
                    except:
                        pass
            
            # === NOTE OFF LOGIC ===
            # End note when duration expires (also pre-trigger by latency)
            # Changed from elif to if to allow both ON and OFF in same iteration
            if (trigger_time >= note_end_time and
                note_id in self.triggered_notes):
                
                # Stop sound
                self.triggered_notes.discard(note_id)
                self.note_ended.emit(note['pitch'])
                
                # Log to real-time playback file if enabled
                if self.playback_logging_enabled and self.playback_log_file:
                    try:
                        self.playback_log_file.write(f"NOTE_OFF | T={current_time:.4f}s | Pitch={note['pitch']} | Scheduled={note_end_time:.4f}s\n")
                        self.playback_log_file.flush()
                    except:
                        pass
    
    def start_playback_logging(self, output_path):
        """Start logging notes as they play in real-time"""
        try:
            self.playback_log_file = open(output_path, 'w', encoding='utf-8')
            self.playback_log_file.write("# Real-Time Playback Log\n")
            self.playback_log_file.write("# Format: NOTE_ON/OFF | T (actual time) | Pitch | Scheduled time | Diff\n")
            self.playback_log_file.write("# " + "="*70 + "\n\n")
            self.playback_logging_enabled = True
            print(f"Started playback logging to {output_path}")
        except Exception as e:
            print(f"Error starting playback logging: {e}")
            self.playback_logging_enabled = False
    
    def stop_playback_logging(self):
        """Stop logging playback"""
        self.playback_logging_enabled = False
        if self.playback_log_file:
            try:
                self.playback_log_file.close()
                print("Playback logging stopped")
            except:
                pass
            self.playback_log_file = None
    
    def reset_triggers(self):
        """Reset all triggered notes (call when stopping/restarting playback)"""
        self.triggered_notes.clear()
        self.last_check_time = -1.0
        if hasattr(self, '_last_trigger_time'):
            self._last_trigger_time = -999.0
    
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
        """
        Update current playback time.
        
        NEW SYSTEM: Línea roja = T₀ (fixed position)
        - Notes are positioned relative to current_time
        - No scroll_offset needed, everything is time-relative
        """
        old_time = self.current_time
        self.current_time = time_sec
        
        # Apply automatic timing adjustments periodically
        self.sync_check_counter += 1
        if self.sync_check_counter >= self.sync_check_interval:
            self.sync_check_counter = 0
            adjustment_stats = self.timing_sync.apply_adjustment()
            if adjustment_stats:
                # Update our latency with the new synchronized value
                self.audio_latency_sec = self.timing_sync.get_current_latency()
                self.audio_latency_ms = self.audio_latency_sec * 1000.0
        
        # Trigger notes that should play now
        # Use slightly ahead time for audio compensation
        trigger_time = time_sec + self.audio_latency_sec
        self._check_and_trigger_notes(time_sec)
        
        # Update display if time changed significantly
        if abs(time_sec - old_time) > 0.01:
            self.update()
    
    def note_on(self, pitch):
        """Highlight specific note(s) with this pitch that are currently triggered"""
        # Find and activate notes with this pitch that are in triggered_notes
        for note in self.notes:
            if note['pitch'] == pitch and note['id'] in self.triggered_notes:
                self.active_note_ids.add(note['id'])
                
                # Also mark corresponding NoteWidget as played for color change
                if hasattr(self, 'song_widget') and self.song_widget.notes:
                    # Find the matching NoteWidget by time and pitch
                    for note_widget in self.song_widget.notes:
                        if (note_widget.pitch == pitch and 
                            abs(note_widget.start_time - note['time']) < 0.001):
                            note_widget.is_played = True
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
            
            # Also unmark corresponding NoteWidget as played to restore original color
            if hasattr(self, 'song_widget') and self.song_widget.notes:
                # Find the matching NoteWidget by time and pitch
                for note_widget in self.song_widget.notes:
                    if (note_widget.pitch == pitch and 
                        abs(note_widget.start_time - note['time']) < 0.001):
                        note_widget.is_played = False
                        break
            
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
            
            # NEW: Draw notes using NoteWidget system
            self.draw_notes(painter)
            
            # Draw playback cursor
            self.draw_cursor(painter)
    
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
        
        clef_size = int(40 * self.visual_zoom_scale)  # Appropriately sized clefs
        clef_x = 50 * self.visual_zoom_scale  # Better positioning
        
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
            bass_clef_y = bass_center_y + (5 * self.visual_zoom_scale)
            painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
            painter.drawText(int(clef_x + 1), int(bass_clef_y + 1), "\uE062")
            painter.setPen(QPen(QColor(15, 15, 15), 1))
            painter.drawText(int(clef_x), int(bass_clef_y), "\uE062")
            
            # Draw brace connecting the staves
            # Bravura brace: \uE000 - Positioned at screen center and scaled to exact staff height
            # Calculate exact height from top of treble staff to bottom of bass staff
            treble_top = treble_center_y - (2 * self.staff_spacing)
            bass_bottom = bass_center_y + (2.5 * self.staff_spacing)
            total_height = bass_bottom - treble_top
            
            # Scale brace size to match the exact vertical span needed
            brace_size = int(total_height * 1.2)  # 1.5 multiplier for proper glyph scaling
            painter.setFont(QFont(self.music_font_family, brace_size))
            
            # Position brace: left-aligned, vertically centered on screen
            brace_x = 1  # Left edge
            brace_y = self.height() / 2 + (brace_size * 0.70)  # Vertical center of screen
            painter.drawText(int(brace_x), int(brace_y), "\uE000")
            
            # Draw key signature, time signature, and tempo for both staves
            key_sig_x = clef_x + (55 * self.visual_zoom_scale)  # Closer to clef
            self.draw_key_signature(painter, key_sig_x, treble_center_y, "treble")
            self.draw_key_signature(painter, key_sig_x, bass_center_y, "bass")
            
            time_sig_x = key_sig_x + (35 * self.visual_zoom_scale)  # Closer to key sig
            self.draw_time_signature(painter, time_sig_x, treble_center_y)
            self.draw_time_signature(painter, time_sig_x, bass_center_y)
            
            # Draw tempo indication well above treble staff (doesn't interfere with notes)
            self.draw_tempo_marking(painter, time_sig_x + (50 * self.visual_zoom_scale), treble_center_y - (5.5 * self.staff_spacing))
            
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
                # Alto/Viola clef (C clef on 3rd line)
                clef_baseline_y = staff_center_y + (40 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE05C")
            elif self.clef_type == "tenor":
                # Tenor clef (C clef on 4th line)
                clef_baseline_y = staff_center_y + self.staff_spacing + (30 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE05C")
            elif self.clef_type == "soprano":
                # Soprano clef (C clef on 1st line)
                clef_baseline_y = staff_center_y - (2 * self.staff_spacing) + (50 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE05C")
            elif self.clef_type == "mezzosoprano":
                # Mezzosoprano clef (C clef on 2nd line)
                clef_baseline_y = staff_center_y - self.staff_spacing + (45 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE05C")
            elif self.clef_type == "baritone":
                # Baritone clef (F clef on 3rd line) - less common variant
                clef_baseline_y = staff_center_y + (10 * self.visual_zoom_scale)
                painter.drawText(int(clef_x), int(clef_baseline_y), "\uE062")
            
            # Draw key signature, time signature, and tempo
            key_sig_x = clef_x + (70 * self.visual_zoom_scale)
            self.draw_key_signature(painter, key_sig_x, staff_center_y, self.clef_type)
            
            time_sig_x = key_sig_x + (40 * self.visual_zoom_scale)
            self.draw_time_signature(painter, time_sig_x, staff_center_y)
            
            self.draw_tempo_marking(painter, time_sig_x + (50 * self.visual_zoom_scale), staff_center_y - (7 * self.staff_spacing))
    
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
            
            # NEW SYSTEM: Use time-relative positioning
            red_line_x = self.left_margin + (50 * self.visual_zoom_scale)
            
            # Draw initial barline at T=0 (thicker, professional)
            initial_time = 0.0
            initial_x = red_line_x + (initial_time - self.current_time) * self.pixels_per_second
            if initial_x >= self.left_margin - 10 and initial_x <= self.width():
                painter.setPen(QPen(QColor(20, 20, 20), 2.5 * self.visual_zoom_scale))
                painter.drawLine(int(initial_x), int(treble_top), int(initial_x), int(bass_bottom))
            
            # Draw regular barlines with subtle shading
            painter.setPen(QPen(QColor(60, 60, 60), 1.3 * self.visual_zoom_scale))
            
            # Calculate visible time range
            time_range_left = self.current_time - (red_line_x / self.pixels_per_second)
            time_range_right = self.current_time + ((self.width() - red_line_x) / self.pixels_per_second)
            
            # Start from first measure before visible area
            start_measure = max(1, int(time_range_left / measure_duration))
            current_time = start_measure * measure_duration
            measure_count = start_measure
            
            while current_time <= time_range_right + measure_duration:
                x = red_line_x + (current_time - self.current_time) * self.pixels_per_second
                
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
            
            # Draw final barline if we have notes (using new coordinate system)
            if self.notes:
                last_note_time = max(note['time'] + note['duration'] for note in self.notes)
                final_time = last_note_time + 1
                final_x = red_line_x + (final_time - self.current_time) * self.pixels_per_second
                
                if final_x >= self.left_margin and final_x <= self.width() + 100:
                    # Double barline for end (professional finish)
                    painter.setPen(QPen(QColor(20, 20, 20), 1.5 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x), int(treble_top), int(final_x), int(bass_bottom))
                    painter.setPen(QPen(QColor(20, 20, 20), 5 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x + 6 * self.visual_zoom_scale), int(treble_top), 
                                   int(final_x + 6 * self.visual_zoom_scale), int(bass_bottom))
        else:
            # Single staff barlines (NEW COORDINATE SYSTEM)
            staff_center_y = self.height() / 2
            top_y = staff_center_y - (2 * self.staff_spacing)
            bottom_y = staff_center_y + (2 * self.staff_spacing)
            
            beats_per_measure = self.time_signature[0]
            measure_duration = (beats_per_measure / self.tempo_bpm) * 60
            
            red_line_x = self.left_margin + (50 * self.visual_zoom_scale)
            
            # Initial barline at T=0
            initial_time = 0.0
            initial_x = red_line_x + (initial_time - self.current_time) * self.pixels_per_second
            if initial_x >= self.left_margin - 10 and initial_x <= self.width():
                painter.setPen(QPen(QColor(0, 0, 0), 2 * self.visual_zoom_scale))
                painter.drawLine(int(initial_x), int(top_y), int(initial_x), int(bottom_y))
            
            # Regular barlines
            painter.setPen(QPen(QColor(0, 0, 0), 1.5 * self.visual_zoom_scale))
            
            # Calculate visible time range
            time_range_left = self.current_time - (red_line_x / self.pixels_per_second)
            time_range_right = self.current_time + ((self.width() - red_line_x) / self.pixels_per_second)
            
            start_measure = max(1, int(time_range_left / measure_duration))
            current_time = start_measure * measure_duration
            
            while current_time <= time_range_right + measure_duration:
                x = red_line_x + (current_time - self.current_time) * self.pixels_per_second
                
                if x >= self.left_margin and x <= self.width():
                    painter.drawLine(int(x), int(top_y), int(x), int(bottom_y))
                
                current_time += measure_duration
            
            # Final barline
            if self.notes:
                last_note_time = max(note['time'] + note['duration'] for note in self.notes)
                final_time = last_note_time + 1
                final_x = red_line_x + (final_time - self.current_time) * self.pixels_per_second
                
                if final_x >= self.left_margin and final_x <= self.width() + 100:
                    painter.setPen(QPen(QColor(0, 0, 0), 1.5 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x), int(top_y), int(final_x), int(bottom_y))
                    painter.setPen(QPen(QColor(0, 0, 0), 4 * self.visual_zoom_scale))
                    painter.drawLine(int(final_x + 5), int(top_y), int(final_x + 5), int(bottom_y))
    
    def draw_notes(self, painter):
        """
        Draw all notes using the NoteWidget system.
        Each NoteWidget handles its own rendering logic.
        """
        if not self.song_widget.notes:
            return
        
        # Calculate viewport bounds for culling
        viewport_left = self.left_margin
        viewport_right = self.width()
        
        # Get staff center positions for grand staff
        if self.clef_type == "grand":
            staff_gap = 3 * self.staff_spacing
            total_staff_height = 8 * self.staff_spacing + staff_gap
            treble_center_y = (self.height() - total_staff_height) / 2 + 2 * self.staff_spacing
            bass_center_y = treble_center_y + 4 * self.staff_spacing + staff_gap
        else:
            staff_center_y = self.height() / 2
        
        # Red line position (fixed)
        red_line_x = self.left_margin + (50 * self.visual_zoom_scale)
        
        # OPTIMIZACIÓN: Calcular rango de tiempo visible
        time_range_left = self.current_time - (red_line_x / self.pixels_per_second) - 1.0
        time_range_right = self.current_time + ((viewport_right - red_line_x) / self.pixels_per_second) + 1.0
        
        # Contadores para debug
        total_notes = len(self.song_widget.notes)
        rendered_count = 0
        
        # Draw each note (OPTIMIZADO: solo revisar notas en rango visible)
        for note_widget in self.song_widget.notes:
            # EARLY CULLING: Saltar notas fuera del rango temporal visible
            if note_widget.start_time < time_range_left or note_widget.start_time > time_range_right:
                continue
            
            # Calculate X position relative to current time
            # Formula: red_line + (note_time - current_time) * pixels_per_second
            time_offset = note_widget.start_time - self.current_time
            note_x = red_line_x + (time_offset * self.pixels_per_second)
            
            # Calculate Y position (vertical, based on pitch)
            note_y = self.pitch_to_y(note_widget.pitch)
            
            # Check if note is visible (spatial culling)
            if not note_widget.is_visible(note_x, viewport_left, viewport_right):
                continue
            
            rendered_count += 1
            
            # Determine color based on state
            if note_widget.is_played:
                note_color = self.played_note_color  # Blue for played notes
            elif note_widget.is_correct is True:
                note_color = QColor(0, 255, 0, 180)  # Green for correct
            elif note_widget.is_correct is False:
                note_color = QColor(255, 0, 0, 180)  # Red for incorrect
            else:
                note_color = QColor(138, 43, 226, 200)  # Purple (default)
            
            # Render the note
            note_widget.render(painter, note_x, note_y, note_color)
    
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
    
    def draw_simple_notes(self, painter):
        """Draw simple note heads (black circles) without stems or beams"""
        if not self.notes:
            return
        
        # Pre-calculate values for optimization
        scroll = self.scroll_offset
        left_margin = self.left_margin
        screen_width = self.width() + 50
        
        # Note head size
        note_head_width = 8 * self.visual_zoom_scale
        note_head_height = 6 * self.visual_zoom_scale
        
        # Set up painter for note heads
        painter.setBrush(QColor(0, 0, 0))  # Black fill
        painter.setPen(Qt.PenStyle.NoPen)  # No outline
        
        for note in self.notes:
            # Calculate X position based on time
            note_x = left_margin + (note['time'] + self.preparation_time) * self.pixels_per_second - scroll
            
            # Skip notes outside visible area (optimization)
            if note_x < left_margin - 100:
                continue
            if note_x > screen_width + 100:
                break
            
            # Only draw notes visible on screen
            if note_x >= left_margin and note_x <= screen_width:
                note_y = note['y']
                
                # Draw ledger lines if note is outside staff
                self.draw_ledger_lines_for_note(painter, note_x, note['pitch'])
                
                # Draw note head as filled ellipse (slightly tilted for traditional look)
                painter.save()
                painter.translate(note_x, note_y)
                painter.rotate(-20)  # Slight rotation for traditional note head appearance
                painter.drawEllipse(QPointF(0, 0), note_head_width, note_head_height)
                painter.restore()
    
    def draw_ledger_lines_for_note(self, painter, x, pitch):
        """Draw ledger lines for notes outside the staff"""
        ledger_width = 12 * self.visual_zoom_scale
        ledger_pen = QPen(QColor(25, 25, 25), 1.3 * self.visual_zoom_scale)
        painter.setPen(ledger_pen)
        
        if self.clef_type == "grand":
            # Grand staff ledger lines
            staff_gap = 3 * self.staff_spacing
            total_staff_height = 8 * self.staff_spacing + staff_gap
            treble_center_y = (self.height() - total_staff_height) / 2 + 2 * self.staff_spacing
            bass_center_y = treble_center_y + 4 * self.staff_spacing + staff_gap
            
            # Treble staff (top): C4 (middle C) = line 0, goes up
            # Ledger lines above treble staff (A5+ or 81+)
            if pitch >= 81:  # A5 and above
                lines_needed = (pitch - 81) // 2 + 1
                for i in range(lines_needed):
                    ledger_y = treble_center_y - (2 * self.staff_spacing) - ((i + 1) * self.staff_spacing)
                    painter.drawLine(int(x - ledger_width), int(ledger_y), 
                                   int(x + ledger_width), int(ledger_y))
            
            # Ledger lines below treble staff / Middle C area (B4 or 71)
            if 69 <= pitch <= 71:  # A4, A#4, B4 (around middle C)
                ledger_y = treble_center_y + (2 * self.staff_spacing) + self.staff_spacing
                painter.drawLine(int(x - ledger_width), int(ledger_y), 
                               int(x + ledger_width), int(ledger_y))
            
            # Ledger lines below bass staff (E2- or 52-)
            if pitch <= 52:  # E2 and below
                lines_needed = (52 - pitch) // 2 + 1
                for i in range(lines_needed):
                    ledger_y = bass_center_y + (2 * self.staff_spacing) + ((i + 1) * self.staff_spacing)
                    painter.drawLine(int(x - ledger_width), int(ledger_y), 
                                   int(x + ledger_width), int(ledger_y))
            
            # Ledger lines above bass staff / Middle C area
            if 67 <= pitch <= 69:  # G4, G#4, A4
                ledger_y = bass_center_y - (2 * self.staff_spacing) - self.staff_spacing
                painter.drawLine(int(x - ledger_width), int(ledger_y), 
                               int(x + ledger_width), int(ledger_y))
        else:
            # Single treble staff
            staff_center_y = self.height() / 2
            
            # Ledger lines above staff (A5+ or 81+)
            if pitch >= 81:
                lines_needed = (pitch - 81) // 2 + 1
                for i in range(lines_needed):
                    ledger_y = staff_center_y - (2 * self.staff_spacing) - ((i + 1) * self.staff_spacing)
                    painter.drawLine(int(x - ledger_width), int(ledger_y), 
                                   int(x + ledger_width), int(ledger_y))
            
            # Ledger lines below staff (C4- or 60-)
            if pitch <= 60:
                lines_needed = (60 - pitch) // 2 + 1
                for i in range(lines_needed):
                    ledger_y = staff_center_y + (2 * self.staff_spacing) + ((i + 1) * self.staff_spacing)
                    painter.drawLine(int(x - ledger_width), int(ledger_y), 
                                   int(x + ledger_width), int(ledger_y))
    
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
        current_measure = int(self.current_time / measure_duration) if self.current_time >= 0 else -1
        measure_start_time = current_measure * measure_duration
        measure_end_time = (current_measure + 1) * measure_duration
        
        # Draw subtle highlight for current measure (using new coordinate system)
        red_line_x = self.left_margin + (50 * self.visual_zoom_scale)
        measure_start_x = red_line_x + (measure_start_time - self.current_time) * self.pixels_per_second
        measure_end_x = red_line_x + (measure_end_time - self.current_time) * self.pixels_per_second
        
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
        
        # DEBUG: Draw small markers on notes that SHOULD be at red line right now
        # This helps verify visual-audio sync
        debug_visual_sync = False  # Set to True to enable visual debugging
        if debug_visual_sync:
            tolerance = 0.03  # 30ms
            for note in self.notes:
                if abs(note['time'] - self.current_time) < tolerance:
                    # This note should be right at the red line
                    note_visual_x = self.left_margin + note['x'] - self.scroll_offset
                    note_y = note['y']
                    # Draw a small indicator
                    painter.setPen(QPen(QColor(0, 255, 0), 3))
                    painter.drawEllipse(int(note_visual_x - 3), int(note_y - 3), 6, 6)
    
    def draw_time_labels(self, painter):
        """Draw time markers (NEW COORDINATE SYSTEM)"""
        painter.setPen(QPen(QColor("gray"), 1))
        painter.setFont(QFont("Arial", 10))
        
        red_line_x = self.left_margin + (50 * self.visual_zoom_scale)
        
        # Calculate visible time range
        time_range_left = self.current_time - (red_line_x / self.pixels_per_second)
        time_range_right = self.current_time + ((self.width() - red_line_x) / self.pixels_per_second)
        
        # Draw time markers every second
        start_second = int(time_range_left) - 1
        end_second = int(time_range_right) + 1
        
        for i in range(start_second, end_second + 1):
            x = red_line_x + (i - self.current_time) * self.pixels_per_second
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
    
    # ========== TIMING SYNCHRONIZATION METHODS ==========
    
    def get_sync_statistics(self) -> dict:
        """
        Retorna estadísticas del sistema de sincronización.
        
        Returns:
            Diccionario con estadísticas de sincronización
        """
        return self.timing_sync.get_statistics()
    
    def print_sync_stats(self):
        """Imprime estadísticas de sincronización en consola"""
        stats = self.get_sync_statistics()
        print("\n" + "="*60)
        print("🎵 TIMING SYNCHRONIZATION STATISTICS")
        print("="*60)
        print(f"Status: {'✅ Enabled' if stats['enabled'] else '❌ Disabled'}")
        print(f"Current Latency: {stats['current_latency_ms']:.2f}ms")
        print(f"Total Notes Measured: {stats['total_notes']}")
        print(f"Adjustments Made: {stats['adjustments']}")
        
        if stats['samples'] > 0:
            print(f"\nRecent Samples: {stats['samples']}")
            print(f"Mean Offset: {stats['mean_offset_ms']:.2f}ms")
            print(f"Median Offset: {stats['median_offset_ms']:.2f}ms")
            print(f"Std Deviation: {stats['stdev_offset_ms']:.2f}ms")
            print(f"Min Offset: {stats['min_offset_ms']:.2f}ms")
            print(f"Max Offset: {stats['max_offset_ms']:.2f}ms")
        print("="*60 + "\n")
    
    def reset_sync_system(self):
        """Reinicia el sistema de sincronización"""
        self.timing_sync.reset()
    
    def enable_sync_system(self):
        """Activa el sistema de sincronización automática"""
        self.timing_sync.enable()
    
    def disable_sync_system(self):
        """Desactiva el sistema de sincronización automática"""
        self.timing_sync.disable()
    
    def set_manual_latency(self, latency_ms: float):
        """
        Establece manualmente la latencia de audio.
        
        Args:
            latency_ms: Latencia en milisegundos
        """
        self.timing_sync.set_latency(latency_ms / 1000.0)
        self.audio_latency_sec = self.timing_sync.get_current_latency()
        self.audio_latency_ms = self.audio_latency_sec * 1000.0
