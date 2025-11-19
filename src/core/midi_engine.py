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
                    self.audio_type = 'fluidsynth'
                    print(f"Audio: Loaded soundfont {sf_path}")
                    return
            
            print("Warning: No soundfont found. Download a .sf2 file to C:\\soundfonts\\")
        except Exception as e:
            print(f"Audio init failed: {e}")
            self.audio_synth = None
    
    def _init_pygame_audio(self):
        """Initialize pygame for high-quality audio synthesis"""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.audio_type = 'pygame'
            self.active_sounds = {}  # {note: Sound object}
            print("Audio: Using pygame synthesizer (44.1kHz)")
        except Exception as e:
            print(f"Pygame audio init failed: {e}")
            self.audio_type = None
    
    def _generate_piano_tone(self, note, duration=2.0):
        """Generate a realistic piano-like tone using pygame"""
        if not PYGAME_AVAILABLE:
            return None
        
        frequency = 440 * (2 ** ((note - 69) / 12))  # A4 = 69 = 440Hz
        sample_rate = 44100  # Higher quality
        samples = int(sample_rate * duration)
        
        # Generate wave with rich harmonics for realistic piano sound
        t = np.linspace(0, duration, samples, False)
        
        # Fundamental frequency
        wave = np.sin(2 * np.pi * frequency * t)
        
        # Add harmonics with decreasing amplitude (realistic piano spectrum)
        wave += 0.6 * np.sin(2 * 2 * np.pi * frequency * t)   # 2nd harmonic
        wave += 0.4 * np.sin(3 * 2 * np.pi * frequency * t)   # 3rd harmonic
        wave += 0.25 * np.sin(4 * 2 * np.pi * frequency * t)  # 4th harmonic
        wave += 0.15 * np.sin(5 * 2 * np.pi * frequency * t)  # 5th harmonic
        wave += 0.1 * np.sin(6 * 2 * np.pi * frequency * t)   # 6th harmonic
        wave += 0.08 * np.sin(7 * 2 * np.pi * frequency * t)  # 7th harmonic
        wave += 0.05 * np.sin(8 * 2 * np.pi * frequency * t)  # 8th harmonic
        
        # Inharmonicity (piano strings are not perfectly harmonic)
        inharmonicity = 0.0001 * (note - 40) ** 2
        wave += 0.03 * np.sin(2 * np.pi * frequency * (1 + inharmonicity) * t)
        
        # Apply realistic ADSR envelope
        envelope = np.ones_like(t)
        attack_time = 0.002  # Very fast attack (2ms)
        decay_time = 0.3     # Decay (300ms)
        sustain_level = 0.6  # Sustain level
        release_time = 0.8   # Release (800ms)
        
        attack_samples = int(attack_time * sample_rate)
        decay_samples = int(decay_time * sample_rate)
        release_samples = int(release_time * sample_rate)
        
        # Attack phase
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay phase
        decay_end = attack_samples + decay_samples
        if decay_end < len(envelope):
            envelope[attack_samples:decay_end] = np.linspace(1, sustain_level, decay_samples)
            # Sustain phase
            envelope[decay_end:-release_samples] = sustain_level
        
        # Release phase (exponential decay for natural sound)
        if release_samples > 0:
            envelope[-release_samples:] = sustain_level * np.exp(-5 * np.linspace(0, 1, release_samples))
        
        # Apply envelope and normalize
        wave = wave * envelope
        
        # Add slight random noise for realism (sympathetic resonance)
        noise = np.random.normal(0, 0.005, len(wave))
        wave = wave + noise
        
        # Dynamic range compression for consistent volume
        wave = np.tanh(wave * 1.5) * 0.4
        
        # Convert to 16-bit integer
        wave = (wave * 32767).astype(np.int16)
        
        # Stereo with slight panning based on pitch
        pan = (note - 60) / 88  # Center around middle C
        left_gain = 1.0 - (pan * 0.3 if pan > 0 else 0)
        right_gain = 1.0 + (pan * 0.3 if pan < 0 else 0)
        
        left_channel = (wave * left_gain).astype(np.int16)
        right_channel = (wave * right_gain).astype(np.int16)
        stereo_wave = np.column_stack((left_channel, right_channel))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _play_note_pygame(self, note, velocity):
        """Play note using pygame"""
        if self.audio_type != 'pygame':
            return
        
        try:
            if note not in self.active_sounds:
                sound = self._generate_piano_tone(note)
                if sound:
                    self.active_sounds[note] = sound
            
            if note in self.active_sounds:
                volume = velocity / 127.0
                self.active_sounds[note].set_volume(volume)
                self.active_sounds[note].play()
        except Exception as e:
            print(f"Error playing note {note}: {e}")
    
    def _stop_note_pygame(self, note):
        """Stop note using pygame"""
        if self.audio_type != 'pygame':
            return
        
        try:
            if note in self.active_sounds:
                self.active_sounds[note].stop()
        except Exception as e:
            print(f"Error stopping note {note}: {e}")

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
        
        # Update visual position FIRST (before playing notes)
        self.playback_update.emit(now)
        
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
                        if self.audio_type == 'fluidsynth' and self.audio_synth:
                            self.audio_synth.noteon(0, msg.note, msg.velocity)
                        elif self.audio_type == 'pygame':
                            self._play_note_pygame(msg.note, msg.velocity)
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        self.synth.note_off(msg.note)
                        self.note_off_signal.emit(msg.note)
                        # Stop audio
                        if self.audio_type == 'fluidsynth' and self.audio_synth:
                            self.audio_synth.noteoff(0, msg.note)
                        elif self.audio_type == 'pygame':
                            self._stop_note_pygame(msg.note)
                
                self.current_event_index += 1
            else:
                break
        
        # Check if song is finished
        if self.current_event_index >= len(self.events):
            self.song_finished()
    
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
        
        # Update playback position to first chord of current group for score display
        if current_group and 'time' in current_group[0]:
            self.playback_update.emit(current_group[0]['time'])
        
        if self.student_is_teacher_turn:
            # Teacher's turn: play the 4 chords (only if not already played)
            if not hasattr(self, 'teacher_chord_index'):
                self.teacher_chord_index = 0
                self.teacher_last_play_time = time.time()
            
            now = time.time()
            
            # Play next chord if enough time passed (1 second between chords)
            if self.teacher_chord_index < len(current_group):
                if now - self.teacher_last_play_time >= 1.0:
                    chord = current_group[self.teacher_chord_index]
                    
                    # Play all notes in chord
                    for note_info in chord['notes']:
                        self.synth.note_on(note_info['note'], note_info['velocity'])
                        self.note_on_signal.emit(note_info['note'], note_info['velocity'])
                    
                    # Update score to show this chord's position
                    if 'time' in chord:
                        self.playback_update.emit(chord['time'])
                    
                    print(f"Teacher playing chord {self.teacher_chord_index + 1}/{len(current_group)}")
                    
                    self.teacher_chord_index += 1
                    self.teacher_last_play_time = now
                    
                    # If last chord, prepare to switch to student
                    if self.teacher_chord_index >= len(current_group):
                        print("Teacher finished! Now student's turn...")
                        # Wait 1 second before switching
            
            # Check if teacher finished and enough time passed
            if self.teacher_chord_index >= len(current_group) and now - self.teacher_last_play_time >= 1.0:
                # Switch to student's turn
                self.student_is_teacher_turn = False
                self.student_chords_played = 0
                self.student_waiting_for_chords = [chord['notes'] for chord in current_group]
                self.waiting_for = set(note['note'] for note in current_group[0]['notes'])
                self.waiting_for_notes.emit(list(self.waiting_for))
                
                # Light up the keys the student needs to press
                for note in self.waiting_for:
                    self.note_on_signal.emit(note, 80)
                
                print(f"Student's turn! Play chord 1/{len(current_group)}")
                print(f"Waiting for notes: {sorted(list(self.waiting_for))}")
                del self.teacher_chord_index  # Clean up for next round
            
            # Keep updating during teacher's turn
            return
        
        else:
            # Student's turn: WAIT for them to play the chords (no automatic advance)
            # Keep showing the current chord position on the score
            if self.student_chords_played < len(current_group):
                current_chord = current_group[self.student_chords_played]
                if 'time' in current_chord:
                    self.playback_update.emit(current_chord['time'])
            
            if not self.waiting_for and self.student_chords_played < len(current_group):
                # Student finished current chord, move to next
                self.student_chords_played += 1
                
                if self.student_chords_played < len(current_group):
                    # Set up next chord
                    next_chord = current_group[self.student_chords_played]
                    self.waiting_for = set(note['note'] for note in next_chord['notes'])
                    self.waiting_for_notes.emit(list(self.waiting_for))
                    
                    # Light up the next keys the student needs to press
                    for note in self.waiting_for:
                        self.note_on_signal.emit(note, 80)
                    
                    # Update score to show next chord position
                    if 'time' in next_chord:
                        self.playback_update.emit(next_chord['time'])
                    
                    print(f"Correct! Now play chord {self.student_chords_played + 1}/{len(current_group)}")
                    print(f"Waiting for notes: {sorted(list(self.waiting_for))}")
                else:
                    # Student finished all 4 chords, move to next group
                    print("Excellent! Student completed all 4 chords! Moving to next group...")
                    self.student_current_group += 1
                    self.student_is_teacher_turn = True
                    self.start_time = time.time()  # Reset timer for next group
    
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
        if self.audio_type == 'fluidsynth' and self.audio_synth:
            self.audio_synth.noteon(0, note, velocity)
        elif self.audio_type == 'pygame':
            self._play_note_pygame(note, velocity)
        
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
        if self.audio_type == 'fluidsynth' and self.audio_synth:
            self.audio_synth.noteoff(0, note)
        elif self.audio_type == 'pygame':
            self._stop_note_pygame(note)
    
    def record_mistake(self, note, expected_note, time_occurred):
        """Record a mistake for Corrector mode"""
        self.mistakes.append({
            'played': note,
            'expected': expected_note,
            'time': time_occurred
        })
        print(f"Mistake recorded: played {note}, expected {expected_note}")
