from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer, QMutex
import serial
import time

class ArduinoWorker(QObject):
    """
    Text protocol Arduino worker with RGB color support
    
    Protocol: Text commands (newline terminated)
    - "ON:note:brightness\n" - Default green with brightness (0-100)
    - "LED:note,r,g,b\n" - RGB color (0-255 each)
    - "OFF:note\n" - Turn off LED
    - "BATCH:note1,r,g,b;note2,r,g,b\n" - Multiple LEDs at once
    - "CLEAR\n" - Turn off all
    - "BRIGHTNESS:value\n" - Global brightness (0-255)
    """
    note_on = pyqtSignal(int, int) # note, velocity (for physical piano input)
    note_off = pyqtSignal(int)     # note (for physical piano input)
    connection_status = pyqtSignal(bool, str)

    def __init__(self, port="COM3", baudrate=115200, mock=False):
        super().__init__()
        self.port = port
        self.baudrate = baudrate  # 115200 baud (standard fast USB)
        self.mock = mock
        self.running = False
        self.serial = None
        self.write_mutex = QMutex()  # Thread-safe writing

    def run(self):
        self.running = True
        if not self.mock:
            try:
                print(f"🔌 Connecting to Arduino on {self.port} at {self.baudrate} baud...")
                self.serial = serial.Serial(
                    self.port, 
                    self.baudrate, 
                    timeout=0.1,
                    write_timeout=0.1
                )
                print(f"⏳ Waiting for Arduino initialization...")
                time.sleep(1.5)  # Wait for Arduino startup
                
                # Wait for "READY" message
                start_time = time.time()
                ready = False
                
                while time.time() - start_time < 3:  # 3 second timeout
                    if self.serial.in_waiting > 0:
                        line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                        if line == "READY":
                            ready = True
                            print(f"✅ Arduino READY on {self.port} (text protocol)")
                            break
                    time.sleep(0.1)
                
                if ready:
                    self.connection_status.emit(True, f"Connected to {self.port}")
                else:
                    print(f"⚠️ Connected to {self.port} but no READY signal (continuing anyway)")
                    self.connection_status.emit(True, f"Connected to {self.port}")
                    
            except Exception as e:
                print(f"❌ Error connecting to Arduino: {e}")
                self.connection_status.emit(False, str(e))
                self.running = False
                return
        else:
            self.connection_status.emit(True, "Mock Mode")

        # Main loop - minimal overhead
        while self.running:
            QThread.msleep(100)

    def _write_text(self, command):
        """Internal method to write text command - thread-safe, immediate flush"""
        if not self.serial or not self.serial.is_open or self.mock:
            return
        
        self.write_mutex.lock()
        try:
            self.serial.write(command.encode('utf-8'))
            self.serial.flush()  # Force immediate send
        except Exception as e:
            print(f"Arduino write error: {e}")
        finally:
            self.write_mutex.unlock()

    def send_note_on(self, note, brightness=100, r=None, g=None, b=None):
        """Send LED ON command with optional RGB color
        
        Args:
            note: MIDI note number (21-108)
            brightness: Brightness 0-100 (used if RGB not specified)
            r, g, b: Optional RGB color (0-255). If specified, uses LED: command
        
        Examples:
            send_note_on(60, 100) -> "ON:60:100\n" (green at full brightness)
            send_note_on(60, r=255, g=0, b=0) -> "LED:60,255,0,0\n" (red)
        """
        if 21 <= note <= 108:
            if r is not None and g is not None and b is not None:
                # RGB color specified - use LED: command
                command = f"LED:{note},{r},{g},{b}\n"
            else:
                # Use default green with brightness
                command = f"ON:{note}:{brightness}\n"
            self._write_text(command)

    def send_note_off(self, note):
        """Send LED OFF command
        
        Args:
            note: MIDI note number (21-108)
        """
        if 21 <= note <= 108:
            command = f"OFF:{note}\n"
            self._write_text(command)

    def send_led_rgb(self, note, r, g, b):
        """Send LED with specific RGB color
        
        Args:
            note: MIDI note number (21-108)
            r, g, b: RGB values (0-255)
        """
        if 21 <= note <= 108:
            command = f"LED:{note},{r},{g},{b}\n"
            self._write_text(command)

    def send_batch_leds(self, led_data):
        """Send multiple LEDs in ONE command - MAXIMUM SPEED
        
        Args:
            led_data: List of tuples (note, r, g, b)
        
        Example:
            send_batch_leds([(60, 255, 0, 0), (62, 0, 255, 0), (64, 0, 0, 255)])
            -> "BATCH:60,255,0,0;62,0,255,0;64,0,0,255\n"
        """
        if not led_data:
            return
        
        # Build batch command
        parts = []
        for item in led_data:
            if len(item) == 4:
                note, r, g, b = item
                if 21 <= note <= 108:
                    parts.append(f"{note},{r},{g},{b}")
        
        if parts:
            command = "BATCH:" + ";".join(parts) + "\n"
            self._write_text(command)

    def clear_all_leds(self):
        """Turn off all LEDs"""
        command = "CLEAR\n"
        self._write_text(command)

    def set_brightness(self, brightness):
        """Set global LED brightness
        
        Args:
            brightness: 0-255
        """
        brightness = max(0, min(255, brightness))
        command = f"BRIGHTNESS:{brightness}\n"
        self._write_text(command)

    def test_leds(self):
        """Run test animation"""
        command = "TEST\n"
        self._write_text(command)
    
    def ping(self):
        """Test connection - Arduino responds with PONG"""
        command = "PING\n"
        self._write_text(command)

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
