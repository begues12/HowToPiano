from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

class InstrumentController(QObject):
    """
    Interface to interconnect Arduino, Piano, Audio, and Visuals.
    Acts as a central hub for instrument control.
    """
    
    # Unified Input Signals (from any source)
    note_on_input = pyqtSignal(int, int)  # pitch, velocity
    note_off_input = pyqtSignal(int)      # pitch
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Components
        self.arduino = None
        self.piano_widget = None
        self.score_view = None
        self.synth = None
        
        # State
        self.active_notes = set()
        
    def connect_components(self, arduino=None, piano_widget=None, score_view=None, synth=None):
        """Register components to be controlled"""
        self.arduino = arduino
        self.piano_widget = piano_widget
        self.score_view = score_view
        self.synth = synth
        
        # Connect Inputs
        if self.arduino:
            # Disconnect previous if any to avoid double connection
            try:
                self.arduino.note_on.disconnect(self._handle_arduino_note_on)
                self.arduino.note_off.disconnect(self._handle_arduino_note_off)
            except: pass
            
            self.arduino.note_on.connect(self._handle_arduino_note_on)
            self.arduino.note_off.connect(self._handle_arduino_note_off)
            
        if self.piano_widget:
            try:
                self.piano_widget.note_pressed.disconnect(self._handle_mouse_note_on)
                self.piano_widget.note_released.disconnect(self._handle_mouse_note_off)
            except: pass
            
            self.piano_widget.note_pressed.connect(self._handle_mouse_note_on)
            self.piano_widget.note_released.connect(self._handle_mouse_note_off)
            
    def activate_note(self, pitch, velocity=80, color=None, audio=True, visual=True, arduino=True):
        """
        Central method to activate a note on all outputs.
        """
        self.active_notes.add(pitch)
        
        # 1. Audio
        if audio and self.synth:
            self.synth.note_on(pitch, velocity)
            
        # 2. Visual (Piano)
        if visual and self.piano_widget:
            if color is None:
                color = QColor("red")
            self.piano_widget.note_on(pitch, color)
            
        # 3. Visual (Score)
        if visual and self.score_view:
            if hasattr(self.score_view, 'note_on'):
                self.score_view.note_on(pitch)
            # Also support highlighting for training modes
            if hasattr(self.score_view, 'highlight_note_by_pitch'):
                # Map color to string if needed, or just use default
                self.score_view.highlight_note_by_pitch(pitch, "red")
                
        # 4. Arduino (LEDs)
        if arduino and self.arduino:
            # Assuming ArduinoWorker has this method, or we add it
            if hasattr(self.arduino, 'send_note_on'):
                self.arduino.send_note_on(pitch, velocity)
            elif hasattr(self.arduino, 'serial') and self.arduino.serial:
                try:
                    cmd = f"ON:{pitch}:{velocity}\n"
                    self.arduino.serial.write(cmd.encode())
                except Exception as e:
                    print(f"Arduino send error: {e}")

    def deactivate_note(self, pitch, audio=True, visual=True, arduino=True):
        """
        Central method to deactivate a note on all outputs.
        """
        self.active_notes.discard(pitch)
        
        # 1. Audio
        if audio and self.synth:
            self.synth.note_off(pitch)
            
        # 2. Visual (Piano)
        if visual and self.piano_widget:
            self.piano_widget.note_off(pitch)
            
        # 3. Visual (Score)
        if visual and self.score_view:
            if hasattr(self.score_view, 'note_off'):
                self.score_view.note_off(pitch)
            if hasattr(self.score_view, 'unhighlight_note_by_pitch'):
                self.score_view.unhighlight_note_by_pitch(pitch)
                
        # 4. Arduino (LEDs)
        if arduino and self.arduino:
            if hasattr(self.arduino, 'send_note_off'):
                self.arduino.send_note_off(pitch)
            elif hasattr(self.arduino, 'serial') and self.arduino.serial:
                try:
                    cmd = f"OFF:{pitch}\n"
                    self.arduino.serial.write(cmd.encode())
                except Exception as e:
                    print(f"Arduino send error: {e}")

    # --- Input Handlers ---
    
    def _handle_arduino_note_on(self, pitch, velocity):
        """Handle input from Arduino (Physical Piano)"""
        self.note_on_input.emit(pitch, velocity)
        # Feedback: Visual only (audio usually comes from physical piano, but we can enable it)
        self.activate_note(pitch, velocity, color=QColor("orange"), audio=False, visual=True, arduino=False)
        
    def _handle_arduino_note_off(self, pitch):
        self.note_off_input.emit(pitch)
        self.deactivate_note(pitch, audio=False, visual=True, arduino=False)
        
    def _handle_mouse_note_on(self, pitch):
        """Handle input from Mouse (Virtual Piano)"""
        velocity = 100
        self.note_on_input.emit(pitch, velocity)
        # Feedback: Audio + Visual + Arduino LEDs
        self.activate_note(pitch, velocity, color=QColor("orange"), audio=True, visual=True, arduino=True)
        
    def _handle_mouse_note_off(self, pitch):
        self.note_off_input.emit(pitch)
        self.deactivate_note(pitch, audio=True, visual=True, arduino=True)
