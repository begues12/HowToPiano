from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import serial
import time
import random

class ArduinoWorker(QObject):
    note_on = pyqtSignal(int, int) # note, velocity
    note_off = pyqtSignal(int)
    connection_status = pyqtSignal(bool, str)
    response_received = pyqtSignal(str) # Arduino responses

    def __init__(self, port="COM3", baudrate=115200, mock=False):
        super().__init__()
        self.port = port
        self.baudrate = baudrate  # Changed to 115200 to match Arduino
        self.mock = mock
        self.running = False
        self.serial = None

    def run(self):
        self.running = True
        if not self.mock:
            try:
                print(f"🔌 Connecting to Arduino on {self.port} at {self.baudrate} baud...")
                self.serial = serial.Serial(self.port, self.baudrate, timeout=0.5)
                print(f"⏳ Waiting for Arduino initialization (3 seconds)...")
                time.sleep(3)  # Wait for Arduino to reset and run startup animation
                
                # Flush any startup messages and look for "READY"
                start_time = time.time()
                ready = False
                startup_messages = []
                
                while time.time() - start_time < 5:  # 5 second timeout
                    if self.serial.in_waiting:
                        line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            startup_messages.append(line)
                            print(f"  Arduino: {line}")
                            if "READY" in line:
                                ready = True
                                break
                    time.sleep(0.1)
                
                if ready:
                    print(f"✅ Arduino READY on {self.port}")
                    self.connection_status.emit(True, f"Connected to {self.port}")
                else:
                    # Try PING as fallback
                    print(f"  No READY signal, trying PING...")
                    self.serial.write(b"PING\n")
                    time.sleep(0.2)
                    
                    if self.serial.in_waiting:
                        response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                        print(f"  Response: {response}")
                        if "PONG" in response:
                            ready = True
                            print(f"✅ Arduino responding on {self.port}")
                            self.connection_status.emit(True, f"Connected to {self.port}")
                    
                    if not ready:
                        print(f"⚠️ Connected to {self.port} but no handshake received")
                        self.connection_status.emit(True, f"Connected to {self.port} (no handshake)")
                    
            except Exception as e:
                print(f"❌ Error connecting to Arduino: {e}")
                self.connection_status.emit(False, str(e))
                self.running = False
                return
        else:
            self.connection_status.emit(True, "Mock Mode")

        while self.running:
            if self.mock:
                # Mock mode - no automatic notes, only responds to real input
                # (Notes will come from mouse/MIDI controller instead)
                QThread.msleep(100)
            else:
                if self.serial and self.serial.in_waiting:
                    try:
                        line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self.parse_line(line)
                            self.response_received.emit(line)
                    except Exception as e:
                        print(f"Serial read error: {e}")
                QThread.msleep(10)

    def parse_line(self, line):
        # Expected Protocol examples: 
        # "ON:60:100" -> Note On 60, velocity 100
        # "OFF:60"    -> Note Off 60
        # Also receives feedback from Arduino like "LED ON: C4 (MIDI 60, LED index 39)"
        try:
            parts = line.split(':')
            cmd = parts[0].upper()
            if cmd == "ON" and len(parts) >= 3:
                self.note_on.emit(int(parts[1]), int(parts[2]))
            elif cmd == "OFF" and len(parts) >= 2:
                self.note_off.emit(int(parts[1]))
        except (ValueError, IndexError):
            pass

    def send_note_on(self, note, brightness=100):
        """Send LED ON command to Arduino
        
        Args:
            note: MIDI note number (21-108 for piano)
            brightness: LED brightness (0-100)
        """
        if self.serial and self.serial.is_open:
            try:
                cmd = f"ON:{note}:{brightness}\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino send error: {e}")

    def send_note_off(self, note):
        """Send LED OFF command to Arduino
        
        Args:
            note: MIDI note number (21-108 for piano)
        """
        if self.serial and self.serial.is_open:
            try:
                cmd = f"OFF:{note}\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino send error: {e}")

    def send_led_rgb(self, note, r, g, b):
        """Send LED RGB command to Arduino
        
        Args:
            note: MIDI note number
            r, g, b: RGB color values (0-255)
        """
        if self.serial and self.serial.is_open:
            try:
                cmd = f"LED:{note},{r},{g},{b}\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino send error: {e}")

    def send_batch_leds(self, led_data):
        """Send multiple LED updates in one command for better performance
        
        Args:
            led_data: List of tuples (note, r, g, b)
        """
        if self.serial and self.serial.is_open:
            try:
                # Format: BATCH:note1,r,g,b;note2,r,g,b;note3,r,g,b
                batch_str = ";".join([f"{note},{r},{g},{b}" for note, r, g, b in led_data])
                cmd = f"BATCH:{batch_str}\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino batch send error: {e}")

    def clear_all_leds(self):
        """Turn off all LEDs"""
        if self.serial and self.serial.is_open:
            try:
                cmd = "CLEAR\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino clear error: {e}")

    def set_brightness(self, brightness):
        """Set global LED brightness
        
        Args:
            brightness: 0-255
        """
        if self.serial and self.serial.is_open:
            try:
                cmd = f"BRIGHTNESS:{brightness}\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino brightness error: {e}")

    def test_leds(self):
        """Run Arduino test animation"""
        if self.serial and self.serial.is_open:
            try:
                cmd = "TEST\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino test error: {e}")

    def ping(self):
        """Send ping to check Arduino responsiveness"""
        if self.serial and self.serial.is_open:
            try:
                cmd = "PING\n"
                self.serial.write(cmd.encode())
            except Exception as e:
                print(f"Arduino ping error: {e}")

    def stop(self):
        self.running = False
        if self.serial:
            try:
                self.clear_all_leds()  # Turn off all LEDs before closing
                time.sleep(0.1)
            except:
                pass
            self.serial.close()
