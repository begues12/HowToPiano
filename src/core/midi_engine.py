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

# Try to import Maestro Sampler (real piano samples)
MAESTRO_AVAILABLE = False
try:
    from maestro_sampler import MaestroSampler
    MAESTRO_AVAILABLE = True
    print("Maestro Concert Grand Piano samples available")
except ImportError as e:
    print(f"Maestro sampler not available ({e})")

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
        
        # Training mode manager (set by MainWindow after initialization)
        self.training_manager = None
        
        # Audio synth
        self.audio_synth = None
        self.sfid = None
        self.maestro_sampler = None
        self.audio_type = None  # 'maestro', 'fluidsynth', 'pygame', or None
        
        # Priority: Maestro samples > FluidSynth > Pygame synthesis
        if MAESTRO_AVAILABLE:
            self._init_maestro_sampler()
        elif FLUIDSYNTH_AVAILABLE:
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
        
        # Preparation time (seconds notes appear before they should be played)
        self.preparation_time = 3.0  # Default - will be set by MainWindow
    
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
    
    def _init_maestro_sampler(self):
        """Initialize Maestro Concert Grand Piano sampler"""
        try:
            # Initialize pygame.mixer first (needed for sample playback)
            # Increase channels to 128 for more simultaneous notes and reduce buffer for lower latency
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)
            pygame.mixer.set_num_channels(128)
            # Reserve some channels to prevent critical notes from being cut
            pygame.mixer.set_reserved(16)
            
            # Load Maestro samples
            self.maestro_sampler = MaestroSampler()
            self.audio_type = 'maestro'
            print("Audio: Using Maestro Concert Grand Piano samples")
        except Exception as e:
            print(f"Maestro sampler init failed: {e}")
            self.audio_type = None
            self.maestro_sampler = None
    
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
        """Play note using pygame or Maestro sampler"""
        # Use Maestro sampler if available
        if self.audio_type == 'maestro' and self.maestro_sampler:
            try:
                self.maestro_sampler.play_note(note, velocity)
                return
            except Exception as e:
                print(f"Error playing Maestro sample {note}: {e}")
        
        # Fallback to pygame synthesis
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
        """Stop note using pygame or Maestro sampler"""
        # Use Maestro sampler if available
        if self.audio_type == 'maestro' and self.maestro_sampler:
            try:
                self.maestro_sampler.stop_note(note)
                return
            except Exception as e:
                print(f"Error stopping Maestro sample {note}: {e}")
        
        # Fallback to pygame synthesis
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
            
            # Find first note_on to eliminate initial silence
            first_note_time = None
            for event in self.events:
                if event['msg'].type == 'note_on' and event['msg'].velocity > 0:
                    first_note_time = event['time']
                    break
            
            # Offset all events so first note starts at time 0
            if first_note_time is not None and first_note_time > 0:
                for event in self.events:
                    event['time'] -= first_note_time
                current_time -= first_note_time
                print(f"MidiEngine: Removed {first_note_time:.2f}s of initial silence")
            
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
        
        # Note: In Master mode, training_manager controls timing
        # In Practice/Student modes, this timing is used
        # Start time at -preparation_time so clock reaches 0 when first note plays
        self.start_time = time.time() - self.paused_at + self.preparation_time
        
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
        self.paused_at = -self.preparation_time  # Reset to negative time so play() starts from -preparation_time
        self.waiting_for = set()
        self.playback_update.emit(-self.preparation_time)  # Emit negative time to show preparation phase
    
    def seek(self, position):
        """Jump to specific position in seconds"""
        if not self.events:
            return
        
        # Stop all currently playing notes
        for note in range(128):
            self.synth.note_off(note)
            self.note_off_signal.emit(note)
            if self.audio_type == 'pygame' and note in self.active_sounds:
                self.active_sounds[note].stop()
        
        # Find the event index closest to the target position
        target_index = 0
        for i, event in enumerate(self.events):
            if event['time'] <= position:
                target_index = i
            else:
                break
        
        self.current_event_index = target_index
        
        # If playing, adjust start_time to continue from new position
        if self.is_playing:
            self.start_time = time.time() - position + self.preparation_time
        else:
            # If paused, update paused_at
            self.paused_at = position
        
        # Update visual playback position immediately
        self.playback_update.emit(position)
        print(f"Seeked to {position:.2f}s (event {target_index}/{len(self.events)})")

    def tick(self):
        """Called every 10ms - delegates to training manager"""
        if not self.timer.isActive():
            return
        
        # Delegate to training manager if available
        if self.training_manager:
            self.training_manager.tick()
            return
        
        # Fallback: old behavior (shouldn't happen in normal operation)
        if not self.is_playing: return
        
        # MASTER MODE or normal playback
        now = time.time() - self.start_time
        
        # Update visual position to current playback time
        self.playback_update.emit(now)
        
        # CRITICAL FIX: Don't process MIDI events during preparation time (negative time)
        # Events should only start when now >= 0
        if now < 0:
            return  # Still in preparation phase, don't process any events
        
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
                # NOTE: In MASTER mode, the staff widget controls note playback via red line triggers
                # Only emit signals for visual feedback, don't play audio here
                if self.mode != "Practice":  # Practice mode handles notes differently
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Only emit signal for visual highlighting (staff will handle audio)
                        # self.note_on_signal.emit(msg.note, msg.velocity)
                        pass  # Staff triggers handle everything in Master mode
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        # Only emit signal for visual feedback (staff will handle audio)
                        # self.note_off_signal.emit(msg.note)
                        pass  # Staff triggers handle everything in Master mode
                
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
        elif self.audio_type in ['maestro', 'pygame']:
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
        elif self.audio_type in ['maestro', 'pygame']:
            self._stop_note_pygame(note)
        
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
