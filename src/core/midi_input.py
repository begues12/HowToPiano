"""
MIDI Input Worker - Handles real-time MIDI input in a separate thread
"""
import time
from PyQt6.QtCore import QObject, pyqtSignal
import mido

class MidiInputWorker(QObject):
    """Worker for handling MIDI input in a separate thread"""
    
    note_on = pyqtSignal(int, int)  # note, velocity
    note_off = pyqtSignal(int)  # note
    connected = pyqtSignal(str)  # device_name
    disconnected = pyqtSignal()
    error = pyqtSignal(str)  # error_message
    
    def __init__(self, device_name=None):
        super().__init__()
        self.device_name = device_name
        self.port = None
        self.running = False
        
    def run(self):
        """Main loop for MIDI input (runs in separate thread)"""
        self.running = True
        
        try:
            # Auto-detect MIDI device if not specified
            if not self.device_name:
                available_ports = mido.get_input_names()
                if available_ports:
                    # Try to find a keyboard (filter out common MIDI Through ports)
                    for port_name in available_ports:
                        if "Through" not in port_name and "Midi Through" not in port_name:
                            self.device_name = port_name
                            break
                    
                    # If only MIDI Through available, use first port
                    if not self.device_name and available_ports:
                        self.device_name = available_ports[0]
            
            if not self.device_name:
                self.error.emit("No MIDI input devices found")
                return
            
            # Open MIDI input port
            self.port = mido.open_input(self.device_name)
            self.connected.emit(self.device_name)
            print(f"✅ MIDI Input connected: {self.device_name}")
            
            # Main MIDI input loop
            while self.running:
                for msg in self.port.iter_pending():
                    if not self.running:
                        break
                    
                    if msg.type == 'note_on':
                        if msg.velocity > 0:
                            # Real note on
                            self.note_on.emit(msg.note, msg.velocity)
                        else:
                            # Note on with velocity 0 = note off
                            self.note_off.emit(msg.note)
                    
                    elif msg.type == 'note_off':
                        self.note_off.emit(msg.note)
                
                # Small sleep to avoid CPU spinning
                time.sleep(0.001)  # 1ms
        
        except Exception as e:
            error_msg = f"MIDI Input error: {str(e)}"
            print(f"❌ {error_msg}")
            self.error.emit(error_msg)
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up MIDI connection"""
        if self.port:
            try:
                self.port.close()
                print(f"🔌 MIDI Input disconnected: {self.device_name}")
            except:
                pass
            self.port = None
        self.disconnected.emit()
    
    def stop(self):
        """Stop the MIDI input worker"""
        self.running = False
