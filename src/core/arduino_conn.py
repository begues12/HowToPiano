from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer, QMutex
import serial
import time
import struct

class ArduinoWorker(QObject):
    """
    Binary protocol Arduino worker - NO RESPONSES, MAXIMUM SPEED
    
    Protocol: 5 bytes per LED command
    [note_number][state][R][G][B]
    
    Multiple LEDs can be sent in one packet for batch updates
    """
    note_on = pyqtSignal(int, int) # note, velocity (for physical piano input)
    note_off = pyqtSignal(int)     # note (for physical piano input)
    connection_status = pyqtSignal(bool, str)

    def __init__(self, port="COM3", baudrate=500000, mock=False):
        super().__init__()
        self.port = port
        self.baudrate = baudrate  # 500000 baud for maximum speed
        self.mock = mock
        self.running = False
        self.serial = None
        self.write_mutex = QMutex()  # Thread-safe writing
        self.command_buffer = []     # Buffer for batch commands

    def run(self):
        self.running = True
        if not self.mock:
            try:
                print(f"🔌 Connecting to Arduino on {self.port} at {self.baudrate} baud...")
                self.serial = serial.Serial(
                    self.port, 
                    self.baudrate, 
                    timeout=0.1,
                    write_timeout=0.1  # Non-blocking writes
                )
                print(f"⏳ Waiting for Arduino initialization (1 second)...")
                time.sleep(1)  # Quick startup
                
                # Wait for ready byte (0xFF)
                start_time = time.time()
                ready = False
                
                while time.time() - start_time < 3:  # 3 second timeout
                    if self.serial.in_waiting > 0:
                        byte = self.serial.read(1)
                        if byte == b'\xFF':
                            ready = True
                            print(f"✅ Arduino READY on {self.port} (binary protocol)")
                            break
                    time.sleep(0.1)
                
                if ready:
                    self.connection_status.emit(True, f"Connected to {self.port}")
                else:
                    print(f"⚠️ Connected to {self.port} but no ready signal (continuing anyway)")
                    self.connection_status.emit(True, f"Connected to {self.port}")
                    
            except Exception as e:
                print(f"❌ Error connecting to Arduino: {e}")
                self.connection_status.emit(False, str(e))
                self.running = False
                return
        else:
            self.connection_status.emit(True, "Mock Mode")

        # Main loop - NO READING, only for keep-alive
        while self.running:
            QThread.msleep(100)

    def _write_binary(self, data):
        """Internal method to write binary data - thread-safe, immediate flush"""
        if not self.serial or not self.serial.is_open or self.mock:
            return
        
        self.write_mutex.lock()
        try:
            self.serial.write(data)
            self.serial.flush()  # Force immediate send for real-time response
        except Exception as e:
            print(f"Arduino write error: {e}")
        finally:
            self.write_mutex.unlock()

    def send_note_on(self, note, r=0, g=255, b=0):
        """Send LED ON command - BINARY, NO RESPONSE
        
        Args:
            note: MIDI note number (21-108)
            r, g, b: RGB color (0-255)
        """
        led_index = note - 21  # Convert MIDI to LED index
        if 0 <= led_index < 88:
            packet = bytes([led_index, 1, r, g, b])  # state=1 (ON)
            self._write_binary(packet)

    def send_note_off(self, note):
        """Send LED OFF command - BINARY, NO RESPONSE
        
        Args:
            note: MIDI note number (21-108)
        """
        led_index = note - 21
        if 0 <= led_index < 88:
            packet = bytes([led_index, 0, 0, 0, 0])  # state=0 (OFF)
            self._write_binary(packet)

    def send_led_rgb(self, note, r, g, b):
        """Send LED with specific RGB color - BINARY, NO RESPONSE
        
        Args:
            note: MIDI note number (21-108)
            r, g, b: RGB values (0-255)
        """
        led_index = note - 21
        if 0 <= led_index < 88:
            packet = bytes([led_index, 1, r, g, b])
            self._write_binary(packet)

    def send_batch_leds(self, led_data):
        """Send multiple LEDs in ONE packet - MAXIMUM SPEED
        
        Args:
            led_data: List of tuples (note, r, g, b) or (note, state, r, g, b)
        """
        if not led_data:
            return
        
        # Build multi-LED packet
        packet = bytearray()
        for item in led_data:
            if len(item) == 4:
                note, r, g, b = item
                state = 1  # ON
            elif len(item) == 5:
                note, state, r, g, b = item
            else:
                continue
            
            led_index = note - 21
            if 0 <= led_index < 88:
                packet.extend([led_index, state, r, g, b])
        
        if packet:
            self._write_binary(bytes(packet))

    def clear_all_leds(self):
        """Turn off all LEDs - BINARY COMMAND"""
        packet = bytes([255, 0, 0, 0, 0])  # Special command: CLEAR
        self._write_binary(packet)

    def set_brightness(self, brightness):
        """Set global LED brightness - BINARY COMMAND
        
        Args:
            brightness: 0-255
        """
        brightness = max(0, min(255, brightness))
        packet = bytes([255, 1, brightness, 0, 0])  # Special command: BRIGHTNESS
        self._write_binary(packet)

    def test_leds(self):
        """Run test animation - BINARY COMMAND"""
        packet = bytes([255, 2, 0, 0, 0])  # Special command: TEST
        self._write_binary(packet)

    def stop(self):
        self.running = False
        if self.serial:
            try:
                self.clear_all_leds()  # Turn off all LEDs before closing
                time.sleep(0.05)  # Brief wait for clear command
            except:
                pass
            try:
                self.serial.close()
            except:
                pass
