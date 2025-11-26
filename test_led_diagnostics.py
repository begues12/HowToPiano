"""
LED System Diagnostic Test
Tests all aspects of the LED system to find bugs
"""

import serial
import time
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
import sys

class LEDTester(QObject):
    log_signal = pyqtSignal(str)
    
    def __init__(self, port='COM19', baud=115200):
        super().__init__()
        self.port = port
        self.baud = baud
        self.arduino = None
        
    def connect(self):
        """Connect to Arduino"""
        try:
            self.arduino = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            self.log(f"✅ Connected to {self.port} @ {self.baud} baud")
            
            # Read READY signal
            while self.arduino.in_waiting > 0:
                response = self.arduino.readline().decode('utf-8').strip()
                self.log(f"← {response}")
            
            return True
        except Exception as e:
            self.log(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.arduino:
            self.arduino.close()
            self.log("🔌 Disconnected")
    
    def send_command(self, command, wait_ms=100):
        """Send command and wait for processing"""
        if not self.arduino:
            self.log("❌ Not connected")
            return False
        
        try:
            self.arduino.write(f"{command}\n".encode('utf-8'))
            self.arduino.flush()
            self.log(f"→ {command}")
            time.sleep(wait_ms / 1000.0)
            return True
        except Exception as e:
            self.log(f"❌ Send error: {e}")
            return False
    
    def log(self, message):
        """Log message to UI"""
        print(message)
        self.log_signal.emit(message)
    
    # ==================== TESTS ====================
    
    def test_single_on_off(self):
        """Test 1: Single LED ON then OFF"""
        self.log("\n=== TEST 1: Single LED ON/OFF ===")
        self.send_command("CLEAR", 200)
        
        self.log("Turning ON LED 60 (C4) in RED...")
        self.send_command("LED:60,255,0,0", 200)
        time.sleep(1)
        
        self.log("Turning OFF LED 60...")
        self.send_command("OFF:60", 200)
        time.sleep(1)
        
        self.log("✅ Test 1 complete\n")
    
    def test_multiple_on_single_off(self):
        """Test 2: Multiple LEDs ON, then OFF one by one"""
        self.log("\n=== TEST 2: Multiple ON, Single OFF ===")
        self.send_command("CLEAR", 200)
        
        notes = [60, 64, 67]  # C-E-G chord
        self.log(f"Turning ON chord: {notes}")
        for note in notes:
            self.send_command(f"LED:{note},0,255,0", 100)
        
        time.sleep(2)
        
        self.log("Turning OFF one by one...")
        for note in notes:
            self.log(f"  OFF: {note}")
            self.send_command(f"OFF:{note}", 200)
            time.sleep(0.5)
        
        time.sleep(1)
        self.log("✅ Test 2 complete\n")
    
    def test_multiple_off_simultaneous(self):
        """Test 3: Multiple LEDs OFF sent rapidly (simulates chord end)"""
        self.log("\n=== TEST 3: Multiple OFF Simultaneous (CRITICAL) ===")
        self.send_command("CLEAR", 200)
        
        notes = [60, 62, 64, 65, 67]  # 5-note chord
        self.log(f"Turning ON 5 notes: {notes}")
        for note in notes:
            self.send_command(f"LED:{note},255,100,0", 50)
        
        time.sleep(2)
        
        self.log("Sending 5 OFF commands rapidly (no delay)...")
        for note in notes:
            self.send_command(f"OFF:{note}", 0)  # NO DELAY - simulates real scenario
        
        time.sleep(1)
        self.log("Checking if all LEDs are OFF...")
        time.sleep(1)
        self.log("✅ Test 3 complete - Did all LEDs turn off?\n")
    
    def test_multiple_off_with_delay(self):
        """Test 4: Multiple OFF with small delay between commands"""
        self.log("\n=== TEST 4: Multiple OFF with 50ms delay ===")
        self.send_command("CLEAR", 200)
        
        notes = [60, 62, 64, 65, 67]
        self.log(f"Turning ON 5 notes: {notes}")
        for note in notes:
            self.send_command(f"LED:{note},0,200,255", 50)
        
        time.sleep(2)
        
        self.log("Sending OFF commands with 50ms delay...")
        for note in notes:
            self.send_command(f"OFF:{note}", 50)  # 50ms delay
        
        time.sleep(1)
        self.log("✅ Test 4 complete\n")
    
    def test_buffer_overflow(self):
        """Test 5: Send 10 OFF commands without delay (buffer test)"""
        self.log("\n=== TEST 5: Buffer Overflow Test (10 notes) ===")
        self.send_command("CLEAR", 200)
        
        notes = list(range(60, 70))  # 10 notes
        self.log(f"Turning ON 10 notes: {notes}")
        for note in notes:
            self.send_command(f"LED:{note},255,0,255", 30)
        
        time.sleep(2)
        
        self.log("Sending 10 OFF commands instantly...")
        start = time.time()
        for note in notes:
            self.arduino.write(f"OFF:{note}\n".encode('utf-8'))
        self.arduino.flush()
        elapsed = (time.time() - start) * 1000
        
        self.log(f"Sent in {elapsed:.1f}ms")
        time.sleep(1)
        self.log("✅ Test 5 complete - Check if any LEDs stuck\n")
    
    def test_batch_vs_individual(self):
        """Test 6: BATCH command vs individual commands"""
        self.log("\n=== TEST 6: BATCH vs Individual ===")
        self.send_command("CLEAR", 200)
        
        self.log("Method 1: Individual LED commands")
        notes = [60, 64, 67, 72]
        for i, note in enumerate(notes):
            self.send_command(f"LED:{note},{i*60},{255-i*60},100", 50)
        time.sleep(2)
        self.send_command("CLEAR", 200)
        
        self.log("Method 2: BATCH command")
        batch = "BATCH:"
        batch += ";".join([f"{note},{i*60},{255-i*60},100" for i, note in enumerate(notes)])
        self.send_command(batch, 100)
        time.sleep(2)
        
        self.log("✅ Test 6 complete\n")
    
    def test_rapid_on_off_cycles(self):
        """Test 7: Rapid ON/OFF cycles (stress test)"""
        self.log("\n=== TEST 7: Rapid ON/OFF Stress Test ===")
        self.send_command("CLEAR", 200)
        
        note = 60
        self.log("Blinking LED 60 rapidly 10 times...")
        for i in range(10):
            self.send_command(f"LED:{note},255,0,0", 50)
            self.send_command(f"OFF:{note}", 50)
        
        time.sleep(1)
        self.log("✅ Test 7 complete\n")
    
    def test_clear_vs_multiple_off(self):
        """Test 8: CLEAR command vs multiple OFF commands"""
        self.log("\n=== TEST 8: CLEAR vs Multiple OFF ===")
        
        notes = [60, 64, 67, 71, 76]
        
        self.log("Test A: Using CLEAR command")
        for note in notes:
            self.send_command(f"LED:{note},255,255,0", 50)
        time.sleep(1)
        self.send_command("CLEAR", 200)
        time.sleep(1)
        
        self.log("Test B: Using multiple OFF commands")
        for note in notes:
            self.send_command(f"LED:{note},255,255,0", 50)
        time.sleep(1)
        for note in notes:
            self.send_command(f"OFF:{note}", 20)
        time.sleep(1)
        
        self.log("✅ Test 8 complete\n")
    
    def test_python_buffer_simulation(self):
        """Test 9: Simulate Python's LED buffer flush"""
        self.log("\n=== TEST 9: Python Buffer Simulation ===")
        self.send_command("CLEAR", 200)
        
        # Simulate buffer with mixed ON and OFF commands
        buffer = [
            ('ON', 60, 255, 0, 0),
            ('ON', 64, 0, 255, 0),
            ('ON', 67, 0, 0, 255),
        ]
        
        self.log("Step 1: Send ON commands (simulate buffer flush)")
        for cmd in buffer:
            if cmd[0] == 'ON':
                _, note, r, g, b = cmd
                self.send_command(f"LED:{note},{r},{g},{b}", 30)
        
        time.sleep(2)
        
        # Simulate chord ending
        off_buffer = [60, 64, 67]
        
        self.log("Step 2: Send OFF commands (simulate note_ended)")
        for note in off_buffer:
            self.arduino.write(f"OFF:{note}\n".encode('utf-8'))
        self.arduino.flush()
        
        time.sleep(1)
        self.log("✅ Test 9 complete\n")
    
    def run_all_tests(self):
        """Run all diagnostic tests"""
        if not self.connect():
            return
        
        time.sleep(1)
        
        tests = [
            self.test_single_on_off,
            self.test_multiple_on_single_off,
            self.test_multiple_off_simultaneous,
            self.test_multiple_off_with_delay,
            self.test_buffer_overflow,
            self.test_batch_vs_individual,
            self.test_rapid_on_off_cycles,
            self.test_clear_vs_multiple_off,
            self.test_python_buffer_simulation,
        ]
        
        for i, test in enumerate(tests, 1):
            self.log(f"\n{'='*60}")
            self.log(f"Running test {i}/{len(tests)}: {test.__name__}")
            self.log('='*60)
            try:
                test()
            except Exception as e:
                self.log(f"❌ Test failed with error: {e}")
            time.sleep(1)
        
        self.log("\n" + "="*60)
        self.log("🎉 ALL TESTS COMPLETED")
        self.log("="*60)
        self.log("\nAnalysis:")
        self.log("- If Test 3 failed: OFF commands are being lost when sent rapidly")
        self.log("- If Test 5 failed: Arduino buffer is overflowing")
        self.log("- If Test 8B failed: Individual OFF is slower than CLEAR")
        self.log("- If Test 9 failed: Python buffer simulation has timing issues")
        
        self.disconnect()


class TestDialog(QDialog):
    """UI for LED testing"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LED System Diagnostic Test")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Info label
        info = QLabel("This test will diagnose LED OFF command issues.\n"
                     "Watch your LED strip during the tests.")
        layout.addWidget(info)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background: black; color: #00ff00; font-family: monospace;")
        layout.addWidget(self.log_display)
        
        # Buttons
        self.run_button = QPushButton("🚀 Run All Tests")
        self.run_button.clicked.connect(self.run_tests)
        layout.addWidget(self.run_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)
        
        # Tester
        self.tester = LEDTester()
        self.tester.log_signal.connect(self.append_log)
    
    def append_log(self, message):
        """Append message to log"""
        self.log_display.append(message)
        self.log_display.ensureCursorVisible()
    
    def run_tests(self):
        """Run all tests"""
        self.run_button.setEnabled(False)
        self.log_display.clear()
        
        # Run tests in separate thread to avoid blocking UI
        QTimer.singleShot(100, self._run_tests_async)
    
    def _run_tests_async(self):
        """Run tests asynchronously"""
        self.tester.run_all_tests()
        self.run_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = TestDialog()
    dialog.show()
    sys.exit(app.exec())
