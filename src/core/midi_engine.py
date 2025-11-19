import mido
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import time
import numpy as np

# Try to import audio libraries
FLUIDSYNTH_AVAILABLE = False
PYGAME_AVAILABLE = False

try:
    import fluidsynth
    FLUIDSYNTH_AVAILABLE = True
    print("FluidSynth module loaded successfully")
except (ImportError, FileNotFoundError, OSError) as e:
    print(f"FluidSynth not available ({e})")

try:
    import pygame.mixer
    PYGAME_AVAILABLE = True
    print("Pygame audio available")
except ImportError:
    print("Pygame not available")

class MidiEngine(QObject):
    playback_update = pyqtSignal(float) # current time in seconds
    note_on_signal = pyqtSignal(int, int) # note, velocity
    note_off_signal = pyqtSignal(int) # note
    waiting_for_notes = pyqtSignal(list) # Signal when waiting for user input (list of notes)
    practice_finished = pyqtSignal(dict) # Signal when practice finishes with evaluation results
    
    def __init__(self, synth):
        super().__init__()
        self.synth = synth
        self.events = [] # List of {'time': float, 'msg': Message}
        self.current_event_index = 0
        self.start_time = 0
        self.paused_at = 0
        self.is_playing = False
        self.is_paused = False
        
        self.timer = QTimer()
        self.timer.setInterval(10) # 10ms
        self.timer.timeout.connect(self.tick)
        
        # Audio synth
        self.audio_synth = None
        self.sfid = None
        self.audio_type = None  # 'fluidsynth', 'pygame', or None
        if FLUIDSYNTH_AVAILABLE:
            self._init_audio()
        elif PYGAME_AVAILABLE:
            self._init_pygame_audio()
        
        # Teaching modes
        self.mode = "Master"  # Master, Student, Practice, Corrector
        self.waiting_for = set()  # Notes we're waiting for in Practice mode
        self.active_notes = set()  # Notes currently held down by user
        
        # Performance evaluation
        from src.core.performance_evaluator import PerformanceEvaluator
        self.evaluator = PerformanceEvaluator()
        
        # Student mode (call and response)
        self.student_chord_groups = []  # Groups of 4 chords
        self.student_current_group = 0
        self.student_is_teacher_turn = True  # True = teacher plays, False = student repeats
        self.student_chords_played = 0
        self.student_waiting_for_chords = []  # List of chords student needs to play
        
        # Corrector mode (error tracking)
        self.mistakes = []  # List of {note, time, expected} mistakes
        self.corrector_index = 0
    
    def _init_audio(self):
        """Initialize FluidSynth for audio playback"""
        try:
            self.audio_synth = fluidsynth.Synth()
            self.audio_synth.start(driver="dsound")  # DirectSound on Windows
            
            # Try to load a soundfont
            import os
            soundfont_paths = [
                "C:\\soundfonts\\FluidR3_GM.sf2",
                "C:\\soundfonts\\piano.sf2",
                os.path.join(os.path.expanduser("~"), "soundfonts", "piano.sf2"),
            ]
            
            for sf_path in soundfont_paths:
                if os.path.exists(sf_path):
                    self.sfid = self.audio_synth.sfload(sf_path)
                    self.audio_synth.program_select(0, self.sfid, 0, 0)  # Piano
                    print(f"Audio: Loaded soundfont {sf_path}")
                    return
            
            print("Warning: No soundfont found. Download a .sf2 file to C:\\soundfonts\\")
        except Exception as e:
            print(f"Audio init failed: {e}")
            self.audio_synth = None

    def load_midi(self, filename):
        try:
            mid = mido.MidiFile(filename)
            self.events = []
            current_time = 0
            for msg in mid:
                current_time += msg.time
                if msg.type in ['note_on', 'note_off']:
                    self.events.append({'time': current_time, 'msg': msg})
            
            print(f"Loaded {len(self.events)} events. Total time: {current_time:.2f}s")
            
            # Load expected notes for evaluation
            self.evaluator.load_expected_notes(self.events)
            
            # Prepare chord groups for Student mode
            self._prepare_student_mode_chords()
            
            self.stop()
            return True
        except Exception as e:
            print(f"Error loading MIDI: {e}")
            return False

    def play(self):
        if not self.events: return
        if self.is_playing: return
        
        self.is_playing = True
        self.is_paused = False
        self.start_time = time.time() - self.paused_at
        
        # Start recording for practice mode
        if self.mode == "Practice":
            self.evaluator.start_recording()
        
        # Reset student mode
        if self.mode == "Student":
            self.student_current_group = 0
            self.student_is_teacher_turn = True
            self.student_chords_played = 0
            self.student_waiting_for_chords = []
        
        self.timer.start()

    def pause(self):
        if not self.is_playing: return
        self.is_playing = False
        self.is_paused = True
        self.paused_at = time.time() - self.start_time
        self.timer.stop()
        # Stop all sounds
        # self.synth.all_notes_off() # If implemented

    def stop(self):
        self.is_playing = False
        self.is_paused = False
        self.timer.stop()
        self.current_event_index = 0
        self.paused_at = 0
        self.waiting_for = set()
        self.playback_update.emit(0)

    def tick(self):
        if not self.is_playing: return
        
        # PRACTICE MODE: Wait for user to press lit keys
        if self.mode == "Practice" and self.waiting_for:
            # Freeze time while waiting
            self.start_time = time.time() - self.events[self.current_event_index]['time']
            return
        
        # STUDENT MODE: Handled separately (call and response)
        if self.mode == "Student":
            self._handle_student_mode()
            return
        
        # CORRECTOR MODE: Review mistakes
        if self.mode == "Corrector":
            self._handle_corrector_mode()
            return
        
        # MASTER MODE or normal playback
        now = time.time() - self.start_time
        
        while self.current_event_index < len(self.events):
            evt = self.events[self.current_event_index]
            if evt['time'] <= now:
                msg = evt['msg']
                
                # PRACTICE MODE: Light up keys and wait
                if self.mode == "Practice" and msg.type == 'note_on' and msg.velocity > 0:
                    # Show the note (light it up)
                    self.note_on_signal.emit(msg.note, msg.velocity)
                    
                    # Add to waiting list if not already pressed
                    if msg.note not in self.active_notes:
                        self.waiting_for.add(msg.note)
                        self.waiting_for_notes.emit(list(self.waiting_for))
                        break  # Stop and wait
                
                # Normal playback (MASTER mode and others)
                if self.mode != "Practice":  # Practice mode handles notes differently
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.synth.note_on(msg.note, msg.velocity)
                        self.note_on_signal.emit(msg.note, msg.velocity)
                        # Play audio
                        if self.audio_synth:
                            self.audio_synth.noteon(0, msg.note, msg.velocity)
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        self.synth.note_off(msg.note)
                        self.note_off_signal.emit(msg.note)
                        # Stop audio
                        if self.audio_synth:
                            self.audio_synth.noteoff(0, msg.note)
                
                self.current_event_index += 1
            else:
                break
        
        # Check if song is finished
        if self.current_event_index >= len(self.events):
            self.song_finished()
        
        self.playback_update.emit(now)
    
    def song_finished(self):
        """Called when song playback finishes"""
        self.stop()
        
        # If in practice mode, evaluate and show results
        if self.mode == "Practice":
            self.evaluator.stop_recording()
            evaluation = self.evaluator.evaluate()
            print(f"Practice finished! Stars: {evaluation['overall_stars']}/5")
            self.practice_finished.emit(evaluation)
        
        # If in student mode, evaluate and show results
        if self.mode == "Practice":
            self.evaluator.stop_recording()
            evaluation = self.evaluator.evaluate()
            
            # Emit signal to show results (will be connected to MainWindow)
            from PyQt6.QtCore import pyqtSignal
            if hasattr(self, 'practice_finished'):
                self.practice_finished.emit(evaluation)
    
    def _prepare_student_mode_chords(self):
        """Group events into chords for Student mode"""
        if not self.events:
            return
        
        # Group note_on events into chords (notes starting at same time)
        chords = []
        i = 0
        tolerance = 0.02  # 20ms tolerance for simultaneous notes
        
        while i < len(self.events):
            evt = self.events[i]
            if evt['msg'].type == 'note_on' and evt['msg'].velocity > 0:
                chord_time = evt['time']
                chord_notes = [{'note': evt['msg'].note, 'velocity': evt['msg'].velocity}]
                
                # Find all notes starting at approximately the same time
                j = i + 1
                while j < len(self.events):
                    next_evt = self.events[j]
                    if (next_evt['msg'].type == 'note_on' and 
                        next_evt['msg'].velocity > 0 and 
                        abs(next_evt['time'] - chord_time) < tolerance):
                        chord_notes.append({'note': next_evt['msg'].note, 'velocity': next_evt['msg'].velocity})
                        j += 1
                    else:
                        break
                
                chords.append({
                    'time': chord_time,
                    'notes': chord_notes,
                    'event_indices': list(range(i, j))
                })
                i = j
            else:
                i += 1
        
        # Group chords into sets of 4
        self.student_chord_groups = []
        for i in range(0, len(chords), 4):
            group = chords[i:i+4]
            self.student_chord_groups.append(group)
        
        print(f"Student mode: Created {len(self.student_chord_groups)} groups of chords")
        if self.student_chord_groups:
            print(f"First group has {len(self.student_chord_groups[0])} chords")
    
    def _handle_student_mode(self):
        """Student mode: Teacher plays 4 chords, student repeats"""
        if not self.student_chord_groups or self.student_current_group >= len(self.student_chord_groups):
            # Finished all groups
            self.song_finished()
            return
        
        current_group = self.student_chord_groups[self.student_current_group]
        
        if self.student_is_teacher_turn:
            # Teacher's turn: play the 4 chords
            now = time.time() - self.start_time
            
            # Play chords with timing
            for chord_idx, chord in enumerate(current_group):
                if chord_idx < len(current_group):
                    # Check if it's time to play this chord
                    play_time = self.student_current_group * 8.0 + chord_idx * 1.0  # 1 second between chords
                    
                    if now >= play_time and now < play_time + 0.1:
                        # Play all notes in chord
                        for note_info in chord['notes']:
                            self.synth.note_on(note_info['note'], note_info['velocity'])
                            self.note_on_signal.emit(note_info['note'], note_info['velocity'])
                        
                        # Schedule note off after 0.8 seconds
                        if chord_idx == len(current_group) - 1:
                            # Last chord of teacher's turn, switch to student
                            pass
            
            # Check if teacher finished playing all 4 chords
            finish_time = self.student_current_group * 8.0 + len(current_group) * 1.0
            if now >= finish_time:
                # Switch to student's turn
                self.student_is_teacher_turn = False
                self.student_chords_played = 0
                self.student_waiting_for_chords = [chord['notes'] for chord in current_group]
                self.waiting_for = set(note['note'] for note in current_group[0]['notes'])
                self.waiting_for_notes.emit(list(self.waiting_for))
                print(f"Student's turn! Waiting for {len(self.student_waiting_for_chords)} chords")
        
        else:
            # Student's turn: wait for them to play the chords
            if not self.waiting_for and self.student_chords_played < len(current_group):
                # Student finished current chord, move to next
                self.student_chords_played += 1
                
                if self.student_chords_played < len(current_group):
                    # Set up next chord
                    next_chord = current_group[self.student_chords_played]
                    self.waiting_for = set(note['note'] for note in next_chord['notes'])
                    self.waiting_for_notes.emit(list(self.waiting_for))
                    print(f"Chord {self.student_chords_played + 1}/{len(current_group)}")
                else:
                    # Student finished all 4 chords, move to next group
                    print("Student completed group! Moving to next...")
                    self.student_current_group += 1
                    self.student_is_teacher_turn = True
                    self.start_time = time.time()  # Reset timer for next group
        
        self.playback_update.emit(time.time() - self.start_time)
    
    def _handle_corrector_mode(self):
        """Corrector mode: Review and correct previous mistakes"""
        # TODO: Implement mistake review
        # 1. Show note that was played incorrectly
        # 2. Wait for correct note
        # 3. Move to next mistake
        pass

    def on_user_note_on(self, note, velocity):
        """Called when user presses a key"""
        self.active_notes.add(note)
        self.synth.note_on(note, velocity)  # User feedback sound
        
        # Play audio for user input
        if self.audio_synth:
            self.audio_synth.noteon(0, note, velocity)
        
        # PRACTICE MODE: Check if this is the note we're waiting for
        if self.mode == "Practice" and note in self.waiting_for:
            self.waiting_for.discard(note)
            
            # If all notes pressed, advance to next event
            if not self.waiting_for:
                self.current_event_index += 1
                self.start_time = time.time() - self.events[self.current_event_index]['time'] if self.current_event_index < len(self.events) else 0
        
        # STUDENT MODE: Track if student is playing correct notes
        if self.mode == "Student" and not self.student_is_teacher_turn:
            # Check if this note is in the waiting set
            if note in self.waiting_for:
                self.waiting_for.discard(note)
                print(f"Correct note! {len(self.waiting_for)} notes remaining")
        
        # CORRECTOR MODE: Check if correcting mistake properly
        if self.mode == "Corrector":
            # Verify correct note
            pass

    def on_user_note_off(self, note):
        """Called when user releases a key"""
        if note in self.active_notes:
            self.active_notes.remove(note)
        self.synth.note_off(note)
        
        # Stop audio for user input
        if self.audio_synth:
            self.audio_synth.noteoff(0, note)
    
    def record_mistake(self, note, expected_note, time_occurred):
        """Record a mistake for Corrector mode"""
        self.mistakes.append({
            'played': note,
            'expected': expected_note,
            'time': time_occurred
        })
        print(f"Mistake recorded: played {note}, expected {expected_note}")
