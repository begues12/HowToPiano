from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import serial
import time
import random

class ArduinoWorker(QObject):
    note_on = pyqtSignal(int, int) # note, velocity
    note_off = pyqtSignal(int)
    connection_status = pyqtSignal(bool, str)

    def __init__(self, port="COM3", baudrate=9600, mock=False):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.mock = mock
        self.running = False
        self.serial = None

    def run(self):
        self.running = True
        if not self.mock:
            try:
                self.serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
                self.connection_status.emit(True, f"Connected to {self.port}")
            except Exception as e:
                print(f"Error connecting to Arduino: {e}")
                self.connection_status.emit(False, str(e))
                self.running = False
                return
        else:
            self.connection_status.emit(True, "Mock Mode")

        while self.running:
            if self.mock:
                # Simulate random notes for testing
                if random.random() < 0.05:
                    note = random.randint(60, 72)
                    self.note_on.emit(note, 100)
                    QThread.msleep(200)
                    self.note_off.emit(note)
                QThread.msleep(100)
            else:
                if self.serial and self.serial.in_waiting:
                    try:
                        line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self.parse_line(line)
                    except Exception as e:
                        print(f"Serial read error: {e}")
                QThread.msleep(10)

    def parse_line(self, line):
        # Expected Protocol examples: 
        # "ON:60:100" -> Note On 60, velocity 100
        # "OFF:60"    -> Note Off 60
        try:
            parts = line.split(':')
            cmd = parts[0].upper()
            if cmd == "ON" and len(parts) >= 3:
                self.note_on.emit(int(parts[1]), int(parts[2]))
            elif cmd == "OFF" and len(parts) >= 2:
                self.note_off.emit(int(parts[1]))
        except ValueError:
            pass

    def stop(self):
        self.running = False
        if self.serial:
            self.serial.close()
