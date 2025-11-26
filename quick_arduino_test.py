"""
Quick Arduino Connection Test
Tests basic communication with Arduino at 115200 baud
"""

import serial
import serial.tools.list_ports
import time
import sys

def find_arduino_ports():
    """Find all potential Arduino ports"""
    ports = serial.tools.list_ports.comports()
    arduino_ports = []
    
    for port in ports:
        desc = port.description.lower()
        if any(keyword in desc for keyword in ['arduino', 'ch340', 'ch341', 'usb-serial']):
            arduino_ports.append(port)
    
    return arduino_ports

def test_port(port_name, baudrate=500000):
    """Test connection to a specific port - BINARY PROTOCOL"""
    print(f"\n{'='*60}")
    print(f"Testing {port_name} at {baudrate} baud (BINARY PROTOCOL)")
    print(f"{'='*60}")
    
    try:
        print(f"[1/4] Opening serial port...")
        ser = serial.Serial(port_name, baudrate, timeout=1.0)
        print(f"      ✅ Port opened successfully")
        
        print(f"[2/4] Waiting for Arduino to initialize (2 seconds)...")
        time.sleep(2)
        
        # Look for ready byte (0xFF)
        print(f"[3/4] Looking for ready signal (0xFF byte)...")
        ready = False
        start_time = time.time()
        
        while time.time() - start_time < 3:
            if ser.in_waiting > 0:
                byte = ser.read(1)
                if byte == b'\xFF':
                    ready = True
                    print(f"      ✅ Ready signal received!")
                    break
            time.sleep(0.1)
        
        if not ready:
            print(f"      ⚠️  No ready signal, continuing anyway...")
        
        # Test binary commands
        print(f"[4/4] Testing binary LED commands...")
        
        # Test LED 0 (note 21 - A0) - Red
        print(f"  Sending: LED 0 ON (Red)")
        packet_on = bytes([0, 1, 255, 0, 0])  # [note][state][R][G][B]
        ser.write(packet_on)
        print(f"    ✅ Sent 5 bytes: {list(packet_on)}")
        time.sleep(0.3)
        
        # Turn it green
        print(f"  Sending: LED 0 ON (Green)")
        packet_green = bytes([0, 1, 0, 255, 0])
        ser.write(packet_green)
        print(f"    ✅ Sent 5 bytes: {list(packet_green)}")
        time.sleep(0.3)
        
        # Turn it blue
        print(f"  Sending: LED 0 ON (Blue)")
        packet_blue = bytes([0, 1, 0, 0, 255])
        ser.write(packet_blue)
        print(f"    ✅ Sent 5 bytes: {list(packet_blue)}")
        time.sleep(0.3)
        
        # Turn it off
        print(f"  Sending: LED 0 OFF")
        packet_off = bytes([0, 0, 0, 0, 0])
        ser.write(packet_off)
        print(f"    ✅ Sent 5 bytes: {list(packet_off)}")
        time.sleep(0.2)
        
        # Test middle C (LED 39)
        print(f"\n  Testing Middle C (MIDI 60 → LED 39)...")
        led_index = 60 - 21  # = 39
        packet = bytes([led_index, 1, 255, 255, 0])  # Yellow
        ser.write(packet)
        print(f"    ✅ Sent yellow to LED {led_index}")
        time.sleep(0.5)
        
        # Off
        packet = bytes([led_index, 0, 0, 0, 0])
        ser.write(packet)
        time.sleep(0.2)
        
        # Batch test - multiple LEDs at once
        print(f"\n  Testing BATCH (3 LEDs at once)...")
        batch = bytes([
            39, 1, 255, 0, 0,     # LED 39 - Red
            40, 1, 0, 255, 0,     # LED 40 - Green
            41, 1, 0, 0, 255,     # LED 41 - Blue
        ])
        ser.write(batch)
        print(f"    ✅ Sent 15 bytes for 3 LEDs")
        time.sleep(0.5)
        
        # Clear all
        print(f"\n  Sending: CLEAR ALL")
        clear_cmd = bytes([255, 0, 0, 0, 0])  # Special command
        ser.write(clear_cmd)
        print(f"    ✅ Clear command sent")
        
        print(f"\n✅ All binary tests passed!")
        ser.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return False

def main():
    print("="*60)
    print("Quick Arduino Connection Test")
    print("Testing at 500000 baud (BINARY protocol)")
    print("="*60)
    
    # Find Arduino ports
    print("\n🔍 Searching for Arduino devices...")
    arduino_ports = find_arduino_ports()
    
    if not arduino_ports:
        print("❌ No Arduino devices found!")
        print("\nAll available ports:")
        for port in serial.tools.list_ports.comports():
            print(f"  - {port.device}: {port.description}")
        
        # Ask user to specify port
        port_name = input("\nEnter COM port manually (e.g., COM3): ").strip()
        if port_name:
            test_port(port_name)
        return
    
    print(f"✅ Found {len(arduino_ports)} potential Arduino device(s):")
    for i, port in enumerate(arduino_ports, 1):
        print(f"  {i}. {port.device} - {port.description}")
    
    # Test each port
    for port in arduino_ports:
        success = test_port(port.device)
        if success:
            print(f"\n🎉 Arduino is ready to use on {port.device}!")
            break
    else:
        print(f"\n⚠️  Could not establish communication with any Arduino")
        print(f"\nTroubleshooting tips:")
        print(f"  1. Make sure Arduino is connected via USB")
        print(f"  2. Upload the BINARY protocol sketch (ws2812b_piano_leds.ino)")
        print(f"  3. Verify the sketch uses Serial.begin(500000)")
        print(f"  4. Try pressing the reset button on Arduino")
        print(f"  5. Make sure you uploaded from the correct location:")
        print(f"     C:\\Users\\alex\\Documents\\PythonProjects\\HowToPiano\\arduino\\ws2812b_piano_leds\\")
        print(f"  6. Check that FastLED library is installed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    input("\nPress Enter to exit...")
