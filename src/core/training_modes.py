"""
Training Mode Strategy Pattern
Each mode controls how the staff, piano, and notes behave during playback
"""

from abc import ABCMeta, abstractmethod
from PyQt6.QtCore import QObject, pyqtSignal
import time
import json
import os
from pathlib import Path


# Combined metaclass to resolve ABC + QObject conflict
class ABCQObjectMeta(type(QObject), ABCMeta):
    pass


class TrainingMode(QObject, metaclass=ABCQObjectMeta):
    """Base class for all training modes"""
    
    # Signals for UI updates
    playback_update = pyqtSignal(float)  # Current time in seconds
    note_highlight = pyqtSignal(int, object)  # (pitch, color) - highlight piano key
    note_unhighlight = pyqtSignal(int)  # (pitch) - remove highlight
    staff_note_on = pyqtSignal(int)  # (pitch) - highlight on staff
    staff_note_off = pyqtSignal(int)  # (pitch) - remove staff highlight
    play_audio = pyqtSignal(int, int)  # (pitch, velocity) - play sound
    stop_audio = pyqtSignal(int)  # (pitch) - stop sound
    mode_message = pyqtSignal(str)  # Status message for UI
    finished = pyqtSignal()  # Emitted when song/mode finishes naturally
    
    def __init__(self, midi_engine, staff_widget, piano_widget):
        super().__init__()
        self.midi_engine = midi_engine
        self.staff_widget = staff_widget
        self.piano_widget = piano_widget
        self.is_active = False
        self.tempo_multiplier = 1.0  # Default 100% tempo
        
    @abstractmethod
    def start(self):
        """Start this training mode"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop this training mode"""
        pass
    
    @abstractmethod
    def tick(self):
        """Called every 10ms during playback - core logic here"""
        pass
    
    @abstractmethod
    def on_user_note_press(self, note, velocity):
        """Handle user pressing a key (Arduino/Mouse)"""
        pass
    
    @abstractmethod
    def on_user_note_release(self, note):
        """Handle user releasing a key"""
        pass
    
    def get_mode_name(self):
        """Return human-readable mode name"""
        return self.__class__.__name__.replace("Mode", "")


class PlayMode(TrainingMode):
    """
    PLAY MODE - Simple playback
    - Just plays the song
    - Notes scroll and play automatically
    - Default mode when opening the app
    """
    
    def __init__(self, midi_engine, staff_widget, piano_widget):
        super().__init__(midi_engine, staff_widget, piano_widget)
        self.start_time = 0
        self.paused_adjusted_time = 0  # Store where we paused
        
    def start(self):
        """Start simple playback"""
        self.is_active = True
        # Resume from paused position instead of restarting
        self.start_time = time.time() - (self.paused_adjusted_time / self.tempo_multiplier)
        self.mode_message.emit("▶ Playing")
        
    def stop(self):
        """Stop playback"""
        self.is_active = False
        # Save current position for resume
        if self.start_time > 0:
            real_elapsed = time.time() - self.start_time
            self.paused_adjusted_time = real_elapsed * self.tempo_multiplier
        self.mode_message.emit("⏹ Stopped")
        
    def tick(self):
        """Update playback position"""
        if not self.is_active:
            return
            
        # Calculate current playback time with tempo multiplier
        real_elapsed = time.time() - self.start_time
        adjusted_time = real_elapsed * self.tempo_multiplier
        
        # Update staff position (staff will trigger notes when they cross red line)
        self.playback_update.emit(adjusted_time)
        
        # Check if song finished (add 3 seconds delay to allow last note to fade)
        if self.midi_engine.events:
            total_duration = max(evt['time'] for evt in self.midi_engine.events) if self.midi_engine.events else 0
            if adjusted_time >= total_duration + 3.0:  # Add 3 second delay
                self.is_active = False
                self.mode_message.emit("✓ Song finished")
                self.finished.emit()
    
    def on_user_note_press(self, note, velocity):
        """User can play along"""
        self.play_audio.emit(note, velocity)
        
    def on_user_note_release(self, note):
        """User releases key"""
        self.stop_audio.emit(note)


class MasterMode(TrainingMode):
    """
    MASTER MODE - Normal playback
    - Song plays automatically
    - Notes scroll and cross red line
    - Audio plays when notes cross the line
    - No user interaction required
    """
    
    def __init__(self, midi_engine, staff_widget, piano_widget):
        super().__init__(midi_engine, staff_widget, piano_widget)
        self.start_time = 0
        self.current_event_index = 0
        self.paused_adjusted_time = 0  # Store where we paused
        
    def start(self):
        """Start automatic playback"""
        self.is_active = True
        # Resume from paused position instead of restarting
        # start_time adjusted so that elapsed time continues from paused position
        self.start_time = time.time() - (self.paused_adjusted_time / self.tempo_multiplier)
        # Don't reset event index - let it continue from where it was
        # self.current_event_index stays as it was
        
        # Staff widget will handle note triggering via red line crossings
        self.mode_message.emit("▶ Playing - Master Mode")
        
    def stop(self):
        """Stop playback"""
        self.is_active = False
        # Save current position for resume
        if self.start_time > 0:
            real_elapsed = time.time() - self.start_time
            adjusted_time = real_elapsed * self.tempo_multiplier
            preparation_time = getattr(self.staff_widget, 'preparation_time', 3.0)
            self.paused_adjusted_time = adjusted_time - preparation_time
        self.mode_message.emit("⏹ Stopped - Master Mode")
        
    def tick(self):
        """Update playback position - staff handles note triggering"""
        if not self.is_active:
            return
            
        # Calculate current playback time with tempo multiplier
        real_elapsed = time.time() - self.start_time
        adjusted_time = real_elapsed * self.tempo_multiplier
        
        # CRITICAL: Subtract preparation time so time starts at negative value
        # At t=0s real: adjusted_time = 0 - 3 = -3
        # At t=3s real: adjusted_time = 3 - 3 = 0 (notes start playing)
        preparation_time = getattr(self.staff_widget, 'preparation_time', 3.0)
        adjusted_time -= preparation_time
        
        # Log every second to track timing (disabled for production)
        # if not hasattr(self, '_last_tick_log'):
        #     self._last_tick_log = -999
        # if abs(adjusted_time - self._last_tick_log) >= 1.0:
        #     print(f"[MASTER] tick: real_elapsed={real_elapsed:.3f}s, adjusted_time={adjusted_time:.3f}s, prep={preparation_time}s")
        #     self._last_tick_log = adjusted_time
        
        # Update staff position (staff will trigger notes when they cross red line)
        self.playback_update.emit(adjusted_time)
        
        # Check if song finished - check against total song duration (add 3 seconds delay to allow last note to fade)
        if self.midi_engine.events:
            total_duration = max(evt['time'] for evt in self.midi_engine.events) if self.midi_engine.events else 0
            if adjusted_time >= total_duration + 3.0:  # Add 3 second delay
                self.is_active = False
                self.mode_message.emit("✓ Song finished")
                self.finished.emit()  # Notify that song finished
    
    def on_user_note_press(self, note, velocity):
        """In Master mode, user can play along (not required)"""
        # Just play the sound, doesn't affect playback
        self.play_audio.emit(note, velocity)
        
    def on_user_note_release(self, note):
        """User releases key"""
        self.stop_audio.emit(note)


class StudentMode(TrainingMode):
    """
    STUDENT MODE - Call and Response
    - Program plays 4 chords
    - Student repeats them
    - Continues through the song in chunks
    """
    
    def __init__(self, midi_engine, staff_widget, piano_widget):
        super().__init__(midi_engine, staff_widget, piano_widget)
        self.chord_groups = []  # Groups of 4 chords: [{time, notes: [{note, velocity}]}]
        self.current_group = 0
        self.is_teacher_turn = True
        self.teacher_chord_index = 0
        self.teacher_last_play_time = 0
        self.student_chords_played = 0
        self.waiting_for = set()  # Notes student needs to press
        self.active_teacher_notes = set()  # Notes currently playing by teacher
        
    def start(self):
        """Start call and response mode"""
        self.is_active = True
        self.current_group = 0
        self.is_teacher_turn = True
        self.teacher_chord_index = 0
        self.teacher_last_play_time = time.time()
        self.student_chords_played = 0
        self.waiting_for.clear()
        self.active_teacher_notes.clear()
        
        self._prepare_chord_groups()
        
        if not self.chord_groups:
            self.mode_message.emit("❌ No chords found in song")
            self.stop()
            return
            
        self.mode_message.emit(f"👨‍🏫 Teacher plays {len(self.chord_groups[0])} chords...")
        
    def stop(self):
        """Stop student mode and clean up"""
        self.is_active = False
        
        # Stop all teacher notes that are still playing
        for note in list(self.active_teacher_notes):
            self.stop_audio.emit(note)
            self.note_unhighlight.emit(note)
        self.active_teacher_notes.clear()
        
        # Clear waiting notes
        for note in list(self.waiting_for):
            self.note_unhighlight.emit(note)
        self.waiting_for.clear()
        
        self.mode_message.emit("⏹ Stopped - Student Mode")
        
    def tick(self):
        """Handle call and response logic"""
        if not self.is_active:
            return
        
        # Check if finished all groups
        if self.current_group >= len(self.chord_groups):
            self.is_active = False
            self.mode_message.emit("✓ All groups completed!")
            self.finished.emit()  # Notify that song finished
            return
            
        current_group = self.chord_groups[self.current_group]
        
        if self.is_teacher_turn:
            self._play_teacher_chords(current_group)
        else:
            self._wait_for_student(current_group)
    
    def _prepare_chord_groups(self):
        """Split song into groups of 4 chords from MIDI events"""
        if not self.midi_engine.events:
            return
        
        # Use the existing method from midi_engine
        if hasattr(self.midi_engine, '_prepare_student_mode_chords'):
            self.midi_engine._prepare_student_mode_chords()
            self.chord_groups = self.midi_engine.student_chord_groups
            print(f"StudentMode: Loaded {len(self.chord_groups)} chord groups")
    
    def _play_teacher_chords(self, current_group):
        """Play 4 chords for student to learn"""
        now = time.time()
        
        # Play next chord if enough time passed (adjusted for tempo)
        chord_interval = 1.0 / self.tempo_multiplier  # Slower tempo = longer interval
        if self.teacher_chord_index < len(current_group):
            if now - self.teacher_last_play_time >= chord_interval:
                # Stop previous chord notes
                for note in list(self.active_teacher_notes):
                    self.stop_audio.emit(note)
                    self.note_unhighlight.emit(note)
                self.active_teacher_notes.clear()
                
                chord = current_group[self.teacher_chord_index]
                
                # Play all notes in chord
                for note_info in chord['notes']:
                    note = note_info['note']
                    velocity = note_info['velocity']
                    
                    self.play_audio.emit(note, velocity)
                    self.note_highlight.emit(note, None)
                    self.active_teacher_notes.add(note)
                
                # Update score position
                if 'time' in chord:
                    self.playback_update.emit(chord['time'])
                
                self.teacher_chord_index += 1
                self.teacher_last_play_time = now
                
                self.mode_message.emit(f"👨‍🏫 Teacher playing chord {self.teacher_chord_index}/{len(current_group)}")
        
        # Check if teacher finished and enough time passed to switch
        switch_delay = 1.0 / self.tempo_multiplier
        if self.teacher_chord_index >= len(current_group) and now - self.teacher_last_play_time >= switch_delay:
            # Stop all teacher notes before switching
            for note in list(self.active_teacher_notes):
                self.stop_audio.emit(note)
                self.note_unhighlight.emit(note)
            self.active_teacher_notes.clear()
            
            # Switch to student's turn
            self.is_teacher_turn = False
            self.student_chords_played = 0
            
            # Light up first chord for student
            first_chord = current_group[0]
            self.waiting_for = set(note_info['note'] for note_info in first_chord['notes'])
            
            for note in self.waiting_for:
                self.note_highlight.emit(note, None)
            
            if 'time' in first_chord:
                self.playback_update.emit(first_chord['time'])
            
            self.mode_message.emit(f"🎓 Your turn! Play chord 1/{len(current_group)}")
    
    def _wait_for_student(self, current_group):
        """Wait for student to play the correct chords"""
        # Check if student finished current chord
        if not self.waiting_for and self.student_chords_played < len(current_group):
            self.student_chords_played += 1
            
            if self.student_chords_played < len(current_group):
                # Set up next chord
                next_chord = current_group[self.student_chords_played]
                self.waiting_for = set(note_info['note'] for note_info in next_chord['notes'])
                
                # Light up next chord keys
                for note in self.waiting_for:
                    self.note_highlight.emit(note, None)
                
                # Update score position
                if 'time' in next_chord:
                    self.playback_update.emit(next_chord['time'])
                
                self.mode_message.emit(f"✓ Correct! Now chord {self.student_chords_played + 1}/{len(current_group)}")
            else:
                # Student finished all chords in group
                self.mode_message.emit("✓ Excellent! Moving to next group...")
                self.current_group += 1
                self.is_teacher_turn = True
                self.teacher_chord_index = 0
                self.teacher_last_play_time = time.time()
    
    def on_user_note_press(self, note, velocity):
        """Student presses a key"""
        # Always play audio for feedback
        self.play_audio.emit(note, velocity)
        
        if not self.is_teacher_turn:
            # Check if this is a required note
            if note in self.waiting_for:
                self.waiting_for.discard(note)
                self.note_highlight.emit(note, None)
                
                # If all notes pressed, waiting_for will be empty
                # and _wait_for_student will advance on next tick
    
    def on_user_note_release(self, note):
        """Student releases key"""
        self.stop_audio.emit(note)
        
        # Only unhighlight if not waiting for this note
        if note not in self.waiting_for:
            self.note_unhighlight.emit(note)


class PracticeMode(TrainingMode):
    """
    PRACTICE MODE - Wait for User
    - Notes light up when they should be played
    - Playback pauses until user plays the correct notes
    - Evaluates performance at the end
    """
    
    def __init__(self, midi_engine, staff_widget, piano_widget):
        super().__init__(midi_engine, staff_widget, piano_widget)
        self.waiting_for = set()  # Notes user needs to press
        self.active_notes = set()  # Notes currently pressed by user
        self.current_event_index = 0
        self.start_time = 0
        self.frozen_time = 0
        self.paused_adjusted_time = 0  # Store where we paused
        
        # Statistics tracking
        self.song_uuid = None  # Set when song is loaded
        self.mistakes = []  # List of {time, expected, played, timestamp}
        self.correct_notes = 0
        self.total_notes = 0
        self.session_start_time = None  # Track session duration
        self.completed = False  # Track if song was completed
        
        # Error highlight tracking
        self.error_highlights = set()  # Notes currently highlighted in red
        self.error_highlight_time = 0  # When error highlighting started
        
    def start(self):
        """Start practice mode with evaluation"""
        self.is_active = True
        self.waiting_for.clear()
        self.active_notes.clear()
        # Don't reset event index - continue from where we were
        # self.current_event_index stays as it was
        # Resume from paused position
        self.start_time = time.time() - (self.paused_adjusted_time / self.tempo_multiplier)
        # Clear any previous frozen state
        if hasattr(self, 'frozen_adjusted_time'):
            delattr(self, 'frozen_adjusted_time')
        
        # Reset statistics only if starting from beginning
        if self.current_event_index == 0:
            self.mistakes.clear()
            self.correct_notes = 0
            self.total_notes = 0
            self.session_start_time = time.time()
            self.completed = False
        
        self.mode_message.emit("📝 Practice Mode - Play the notes!")
        
    def stop(self):
        """Stop practice mode and clean up"""
        self.is_active = False
        
        # Clear error highlights
        for note in list(self.error_highlights):
            self.note_unhighlight.emit(note)
        self.error_highlights.clear()
        
        # Clear all highlighted notes
        for note in list(self.waiting_for):
            self.note_unhighlight.emit(note)
        self.waiting_for.clear()
        
        # Stop any active notes
        for note in list(self.active_notes):
            self.stop_audio.emit(note)
            self.note_unhighlight.emit(note)
        self.active_notes.clear()
        
        # Save statistics and show results if we have played any notes
        # Only show dialog if stopped manually (not if completed naturally)
        if self.total_notes > 0 and not self.completed:
            self._save_statistics()
            self._show_results_dialog()
        elif self.total_notes == 0:
            # If stopped without playing, just reset to beginning
            self.current_event_index = 0
            self.paused_adjusted_time = 0
            self.playback_update.emit(-3.0)  # Reset to preparation time
        
        self.mode_message.emit("⏹ Stopped - Practice Mode")
        
    def tick(self):
        """Wait for user input before advancing"""
        if not self.is_active:
            print(f"[PRACTICE TICK] NOT ACTIVE - returning")
            return
        
        # Calculate current time with tempo multiplier
        real_elapsed = time.time() - self.start_time
        adjusted_time = real_elapsed * self.tempo_multiplier
        
        # CRITICAL: Subtract preparation time (same as Master Mode)
        # This ensures notes start off-screen and scroll to the red line
        preparation_time = getattr(self.staff_widget, 'preparation_time', 3.0)
        adjusted_time -= preparation_time
        

        
        # Clean up error highlights after 500ms
        if self.error_highlights and time.time() - self.error_highlight_time > 0.5:
            for note in list(self.error_highlights):
                self.note_unhighlight.emit(note)
            self.error_highlights.clear()
        
        # If waiting for notes, freeze everything - don't update time
        if self.waiting_for:
            self.mode_message.emit(f"⏸ Waiting for {len(self.waiting_for)} note(s)...")
            # Store the frozen time to resume later (only once)
            if not hasattr(self, 'frozen_adjusted_time'):
                self.frozen_adjusted_time = adjusted_time
                self.playback_update.emit(adjusted_time)  # Update once at freeze point
                print(f"[PRACTICE] ⏸ FROZEN at time {adjusted_time:.2f}s, waiting for {len(self.waiting_for)} notes: {list(self.waiting_for)}")
            # Keep resetting start_time to maintain frozen position
            # Add preparation_time back when calculating start_time
            self.start_time = time.time() - ((self.frozen_adjusted_time + preparation_time) / self.tempo_multiplier)
            return
        
        # If we just resumed from waiting, clean up
        if hasattr(self, 'frozen_adjusted_time'):
            print(f"[PRACTICE] ▶ RESUMED from frozen state, continuing from time {adjusted_time:.2f}s")
            delattr(self, 'frozen_adjusted_time')
            self.mode_message.emit("▶ Resuming...")
        
        # Update staff position first (always update when not frozen)
        self.playback_update.emit(adjusted_time)
        
        # Then process events to check if we need to freeze on next tick
        self._process_events(adjusted_time)
        
    def _process_events(self, current_time):
        """Process MIDI events and light up notes (including chords)"""
        events = self.midi_engine.events
        chord_time_tolerance = 0.05  # 50ms tolerance for chord detection
        trigger_tolerance = 0.05  # 50ms window - same as StaffWidget
        
        # Don't process new events if we're already waiting for notes
        if self.waiting_for:
            return
        
        # Find the next note(s) to play - same logic as StaffWidget
        first_note_time = None
        notes_found = False
        
        while self.current_event_index < len(events):
            evt = events[self.current_event_index]
            note_time = evt['time']
            msg = evt['msg']
            
            # Skip notes far in the past (already passed)
            if note_time < current_time - trigger_tolerance:
                self.current_event_index += 1
                continue
            
            # Stop if we reach notes far in the future
            if note_time > current_time + trigger_tolerance:
                break
            
            # === NOTE AT RED LINE ===
            # At this point, note is within trigger window (passed both checks above)
            
            if msg.type == 'note_on' and msg.velocity > 0:
                # First note found - record its time
                if first_note_time is None:
                    first_note_time = note_time
                
                # Check if this note is part of the same chord (within tolerance)
                if abs(note_time - first_note_time) <= chord_time_tolerance:
                    # Add to waiting set
                    self.waiting_for.add(msg.note)
                    self.note_highlight.emit(msg.note, None)
                    self.staff_note_on.emit(msg.note)
                    notes_found = True
                    self.total_notes += 1  # Count expected notes
                    self.current_event_index += 1
                else:
                    # This note is later (different chord) - don't process it yet
                    break
            else:
                # Skip non-note-on events (note_off, etc.)
                self.current_event_index += 1
        
        # Check if song finished
        if self.current_event_index >= len(events) and not self.waiting_for:
            self.is_active = False
            self.completed = True  # Mark as completed
            self._save_statistics()  # Save stats before finishing
            self.mode_message.emit("✓ Practice finished! Evaluating...")
            self._show_results_dialog()  # Show results dialog once
            self.finished.emit()  # Notify that song finished
    
    def on_user_note_press(self, note, velocity):
        """User presses a key"""
        self.active_notes.add(note)
        self.play_audio.emit(note, velocity)
        
        # Check if this is a required note
        if note in self.waiting_for:
            # Correct note - highlight in green (default)
            self.note_highlight.emit(note, None)
            self.correct_notes += 1
            print(f"[PRACTICE] ✓ Correct note {note}! Remaining: {len(self.waiting_for) - 1}")
            self.waiting_for.discard(note)
            
            # If all required notes played, resume playback
            if not self.waiting_for:
                print(f"[PRACTICE] ✅ All notes played! Resuming...")
                self.mode_message.emit("✓ Correct! Continue...")
                # The tick() method will handle resuming from frozen_adjusted_time
        else:
            # Wrong note - highlight the wrong note AND all expected notes in red
            from PyQt6.QtGui import QColor
            red_color = QColor(255, 0, 0)
            
            # Clear previous error highlights first
            for old_note in list(self.error_highlights):
                self.note_unhighlight.emit(old_note)
            self.error_highlights.clear()
            
            # Highlight the wrong note played in red
            self.note_highlight.emit(note, red_color)
            self.error_highlights.add(note)
            
            # Highlight all expected notes (the chord) in red too
            for expected_note in self.waiting_for:
                self.note_highlight.emit(expected_note, red_color)
                self.error_highlights.add(expected_note)
            
            # Record when error highlighting started
            self.error_highlight_time = time.time()
            
            print(f"[PRACTICE] ❌ Wrong note {note} (expected chord: {list(self.waiting_for)})")
            
            # Record the mistake
            if self.start_time > 0:
                real_elapsed = time.time() - self.start_time
                adjusted_time = real_elapsed * self.tempo_multiplier
                preparation_time = getattr(self.staff_widget, 'preparation_time', 3.0)
                current_time = adjusted_time - preparation_time
                
                self.mistakes.append({
                    'time': current_time,
                    'expected': list(self.waiting_for),
                    'played': note,
                    'timestamp': time.time()
                })
            
            # Skip the entire chord (all notes in waiting_for) and continue
            print(f"[PRACTICE] ⏭ Skipping entire chord: {list(self.waiting_for)}")
            self.waiting_for.clear()
            self.mode_message.emit("❌ Wrong! Skipping chord...")
    
    def on_user_note_release(self, note):
        """User releases key"""
        self.active_notes.discard(note)
        self.stop_audio.emit(note)
        
        # Only unhighlight if not waiting for this note
        if note not in self.waiting_for:
            self.note_unhighlight.emit(note)
    
    def _save_statistics(self):
        """Save practice statistics to JSON file"""
        if not self.song_uuid or self.total_notes == 0:
            return
        
        # Create stats directory if it doesn't exist
        stats_dir = Path('library/stats')
        stats_dir.mkdir(parents=True, exist_ok=True)
        
        stats_file = stats_dir / f"{self.song_uuid}.json"
        
        # Load existing stats or create new
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        else:
            stats = {
                'song_uuid': self.song_uuid,
                'sessions': []
            }
        
        # Calculate accuracy
        accuracy = (self.correct_notes / self.total_notes * 100) if self.total_notes > 0 else 0
        
        # Add new session
        session = {
            'timestamp': time.time(),
            'total_notes': self.total_notes,
            'correct_notes': self.correct_notes,
            'mistakes': self.mistakes,
            'accuracy': round(accuracy, 2)
        }
        stats['sessions'].append(session)
        
        # Save to file
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"[PRACTICE] 💾 Stats saved: {self.correct_notes}/{self.total_notes} correct ({accuracy:.1f}%), {len(self.mistakes)} mistakes")
    
    def _show_results_dialog(self):
        """Show practice results dialog"""
        from src.ui.practice_results_dialog import PracticeResultsDialog
        
        # Calculate duration
        duration = 0
        if self.session_start_time:
            duration = time.time() - self.session_start_time
        
        # Calculate accuracy
        accuracy = (self.correct_notes / self.total_notes * 100) if self.total_notes > 0 else 0
        
        # Prepare session stats
        session_stats = {
            'total_notes': self.total_notes,
            'correct_notes': self.correct_notes,
            'mistakes': self.mistakes,
            'accuracy': round(accuracy, 2),
            'duration': round(duration, 1),
            'completed': self.completed
        }
        
        # Create and show dialog
        dialog = PracticeResultsDialog(session_stats)
        dialog.retry_clicked.connect(self._on_retry)
        dialog.continue_clicked.connect(self._on_continue)
        dialog.exec()
    
    def _on_retry(self):
        """Restart practice mode from beginning"""
        print("[PRACTICE] 🔄 Retry requested")
        # Reset to beginning
        self.current_event_index = 0
        self.paused_adjusted_time = 0
        # Reset staff position to start
        self.playback_update.emit(-3.0)  # Reset to preparation time
        # Restart immediately
        self.start()
        
    def _on_continue(self):
        """Continue to next song or normal mode"""
        print("[PRACTICE] ➡️ Continue requested")
        # Reset to beginning
        self.current_event_index = 0
        self.paused_adjusted_time = 0
        # Reset staff position to start
        self.playback_update.emit(-3.0)  # Reset to preparation time


class CorrectorMode(TrainingMode):
    """
    CORRECTOR MODE - Review Mistakes
    - Shows only the notes that were played incorrectly in Practice mode
    - Slower tempo for correction
    - Repeats until perfect
    """
    
    def __init__(self, midi_engine, staff_widget, piano_widget):
        super().__init__(midi_engine, staff_widget, piano_widget)
        self.mistakes = []  # List of {note, time, type}
        self.current_mistake_index = 0
        
    def start(self):
        """Start corrector mode"""
        self.is_active = True
        self.current_mistake_index = 0
        # TODO: Load mistakes from previous practice session
        self.mode_message.emit("✏️ Corrector Mode - Review mistakes")
        
    def stop(self):
        """Stop corrector mode"""
        self.is_active = False
        self.mode_message.emit("⏹ Stopped - Corrector Mode")
        
    def tick(self):
        """Show and correct mistakes one by one"""
        if not self.is_active:
            return
            
        # TODO: Implement mistake correction logic
        pass
    
    def on_user_note_press(self, note, velocity):
        """User tries to correct a mistake"""
        self.play_audio.emit(note, velocity)
        # TODO: Verify if correction is correct
        
    def on_user_note_release(self, note):
        """User releases key"""
        self.stop_audio.emit(note)
