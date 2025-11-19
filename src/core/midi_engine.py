import mido
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import time

class MidiEngine(QObject):
    playback_update = pyqtSignal(float) # current time in seconds
    note_on_signal = pyqtSignal(int, int) # note, velocity
    note_off_signal = pyqtSignal(int) # note
    waiting_for_notes = pyqtSignal(list) # Signal when waiting for user input (list of notes)
    
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
        
        # Corrector mode (error tracking)
        self.mistakes = []  # List of {note, time, expected} mistakes
        self.corrector_index = 0

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
                
                # Normal playback (MASTER mode)
                if msg.type == 'note_on' and msg.velocity > 0:
                    self.synth.note_on(msg.note, msg.velocity)
                    self.note_on_signal.emit(msg.note, msg.velocity)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    self.synth.note_off(msg.note)
                    self.note_off_signal.emit(msg.note)
                
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
            
            # Emit signal to show results (will be connected to MainWindow)
            from PyQt6.QtCore import pyqtSignal
            if hasattr(self, 'practice_finished'):
                self.practice_finished.emit(evaluation)
    
    def _handle_student_mode(self):
        """Student mode: Teacher plays 4 chords, student repeats"""
        # TODO: Implement call and response logic
        # 1. Group notes into chords (notes starting at same time)
        # 2. Play 4 chords (teacher)
        # 3. Wait for student to repeat those 4 chords
        # 4. Move to next group of 4
        pass
    
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
        
        # PRACTICE MODE: Check if this is the note we're waiting for
        if self.mode == "Practice" and note in self.waiting_for:
            self.waiting_for.discard(note)
            
            # If all notes pressed, advance to next event
            if not self.waiting_for:
                self.current_event_index += 1
                self.start_time = time.time() - self.events[self.current_event_index]['time'] if self.current_event_index < len(self.events) else 0
        
        # STUDENT MODE: Track if student is playing correct notes
        if self.mode == "Student" and not self.student_is_teacher_turn:
            # Check if correct note for current chord
            pass
        
        # CORRECTOR MODE: Check if correcting mistake properly
        if self.mode == "Corrector":
            # Verify correct note
            pass

    def on_user_note_off(self, note):
        """Called when user releases a key"""
        if note in self.active_notes:
            self.active_notes.remove(note)
        self.synth.note_off(note)
    
    def record_mistake(self, note, expected_note, time_occurred):
        """Record a mistake for Corrector mode"""
        self.mistakes.append({
            'played': note,
            'expected': expected_note,
            'time': time_occurred
        })
        print(f"Mistake recorded: played {note}, expected {expected_note}")
