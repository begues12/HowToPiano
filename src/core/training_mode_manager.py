"""
Training Mode Manager
Handles switching between different training modes and routing signals
"""

from PyQt6.QtCore import QObject, pyqtSignal
from src.core.training_modes import PlayMode, MasterMode, StudentMode, PracticeMode, CorrectorMode


class TrainingModeManager(QObject):
    """Manages different training modes and routes signals between them"""
    
    # Signals forwarded from active mode
    playback_update = pyqtSignal(float)
    note_highlight = pyqtSignal(int, object)
    note_unhighlight = pyqtSignal(int)
    staff_note_on = pyqtSignal(int)
    staff_note_off = pyqtSignal(int)
    play_audio = pyqtSignal(int, int)
    stop_audio = pyqtSignal(int)
    mode_message = pyqtSignal(str)
    mode_changed = pyqtSignal(str)
    song_finished = pyqtSignal()  # Emitted when song ends
    
    def __init__(self, midi_engine, staff_widget, piano_widget):
        super().__init__()
        
        self.midi_engine = midi_engine
        self.staff_widget = staff_widget
        self.piano_widget = piano_widget
        
        # Create all mode instances
        self.modes = {
            "Play": PlayMode(midi_engine, staff_widget, piano_widget),
            "Master": MasterMode(midi_engine, staff_widget, piano_widget),
            "Student": StudentMode(midi_engine, staff_widget, piano_widget),
            "Practice": PracticeMode(midi_engine, staff_widget, piano_widget),
            "Corrector": CorrectorMode(midi_engine, staff_widget, piano_widget)
        }
        
        # Connect signals from all modes to forward them
        for mode in self.modes.values():
            mode.playback_update.connect(self.playback_update.emit)
            mode.note_highlight.connect(self.note_highlight.emit)
            mode.note_unhighlight.connect(self.note_unhighlight.emit)
            mode.staff_note_on.connect(self.staff_note_on.emit)
            mode.staff_note_off.connect(self.staff_note_off.emit)
            mode.play_audio.connect(self.play_audio.emit)
            mode.stop_audio.connect(self.stop_audio.emit)
            mode.mode_message.connect(self.mode_message.emit)
            mode.finished.connect(self.song_finished.emit)
        
        # Start with Play mode (default)
        self.current_mode_name = "Play"
        self.current_mode = self.modes["Play"]
        
    def set_mode(self, mode_name):
        """Switch to a different training mode"""
        if mode_name not in self.modes:
            print(f"Warning: Unknown mode '{mode_name}', defaulting to Play")
            mode_name = "Play"
        
        # Stop current mode if active
        if self.current_mode and self.current_mode.is_active:
            self.current_mode.stop()
        
        # Switch to new mode
        self.current_mode_name = mode_name
        self.current_mode = self.modes[mode_name]
        
        # Notify UI
        self.mode_changed.emit(mode_name)
        print(f"TrainingModeManager: Switched to {mode_name} mode")
        
    def get_current_mode_name(self):
        """Get name of currently active mode"""
        return self.current_mode_name
    
    def start(self):
        """Start the current training mode"""
        if self.current_mode:
            self.current_mode.start()
    
    def stop(self):
        """Stop the current training mode"""
        if self.current_mode:
            self.current_mode.stop()
    
    def tick(self):
        """Forward tick to current mode"""
        if self.current_mode:
            self.current_mode.tick()
    
    def on_user_note_press(self, note, velocity):
        """Forward user input to current mode"""
        if self.current_mode:
            self.current_mode.on_user_note_press(note, velocity)
    
    def on_user_note_release(self, note):
        """Forward user input to current mode"""
        if self.current_mode:
            self.current_mode.on_user_note_release(note)
