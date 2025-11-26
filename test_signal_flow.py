"""
Test específico para verificar el flujo de señales note_ended
"""
import sys
from PyQt6.QtWidgets import QApplication

# Quick test to verify signal flow
def test_note_ended_signals():
    """Test if multiple notes with same pitch emit correctly"""
    
    print("=== Testing note_ended Signal Flow ===\n")
    
    # Simulate what happens in staff_widget when multiple notes end
    from PyQt6.QtCore import QObject, pyqtSignal
    
    class TestStaff(QObject):
        note_ended = pyqtSignal(int)
        
        def __init__(self):
            super().__init__()
            self.notes = [
                {'id': 1, 'pitch': 60, 'time': 0.0, 'duration': 1.0},
                {'id': 2, 'pitch': 64, 'time': 0.0, 'duration': 1.0},
                {'id': 3, 'pitch': 67, 'time': 0.0, 'duration': 1.0},
                {'id': 4, 'pitch': 60, 'time': 0.5, 'duration': 1.0},  # Duplicate pitch!
            ]
            self.triggered_notes = set()
            
        def trigger_all_notes(self):
            """Simulate all notes being triggered"""
            for note in self.notes:
                self.triggered_notes.add(note['id'])
                print(f"Triggered: id={note['id']}, pitch={note['pitch']}")
        
        def end_notes_at_time(self, current_time):
            """Simulate notes ending at a specific time"""
            print(f"\nChecking notes to end at time={current_time}s")
            for note in self.notes:
                note_id = note['id']
                note_end_time = note['time'] + note['duration']
                
                if current_time >= note_end_time and note_id in self.triggered_notes:
                    self.triggered_notes.discard(note_id)
                    print(f"  Emitting note_ended for id={note_id}, pitch={note['pitch']}")
                    self.note_ended.emit(note['pitch'])
    
    class TestMainWindow(QObject):
        def __init__(self):
            super().__init__()
            self.led_off_calls = []
            
        def on_staff_note_ended(self, pitch):
            print(f"  -> MainWindow received note_ended: pitch={pitch}")
            self.send_arduino_led_off(pitch)
        
        def send_arduino_led_off(self, pitch):
            self.led_off_calls.append(pitch)
            print(f"     -> LED OFF sent for pitch={pitch}")
    
    # Create test objects
    staff = TestStaff()
    main_window = TestMainWindow()
    
    # Connect signal
    staff.note_ended.connect(main_window.on_staff_note_ended)
    
    # Run test
    print("\n1. Triggering all notes...")
    staff.trigger_all_notes()
    
    print("\n2. Ending notes at time=1.0s (chord of 3 notes ends)")
    staff.end_notes_at_time(1.0)
    
    print("\n3. Ending notes at time=1.5s (duplicate pitch ends)")
    staff.end_notes_at_time(1.5)
    
    print("\n=== RESULTS ===")
    print(f"Total note_ended emissions: {len(main_window.led_off_calls)}")
    print(f"LED OFF calls: {main_window.led_off_calls}")
    print(f"Unique pitches: {set(main_window.led_off_calls)}")
    
    # Check if there's a problem
    if len(main_window.led_off_calls) == 4:
        print("\n✅ CORRECTO: Se emitieron 4 señales (una por cada nota)")
        print("   Pitch 60 se apagó 2 veces (correcto, hay 2 notas con ese pitch)")
    else:
        print("\n❌ ERROR: No se emitieron todas las señales esperadas")
    
    return main_window.led_off_calls

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_note_ended_signals()
    print("\n✅ Test completado")
