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

def test_port(port_name, baudrate=115200):
    """Test connection to a specific port"""
    print(f"\n{'='*60}")
    print(f"Testing {port_name} at {baudrate} baud")
    print(f"{'='*60}")
    
    try:
        print(f"[1/4] Opening serial port...")
        ser = serial.Serial(port_name, baudrate, timeout=1.0)
        print(f"      ✅ Port opened successfully")
        
        print(f"[2/4] Waiting for Arduino to initialize (3 seconds)...")
        time.sleep(3)
        
        # Read any startup messages
        print(f"[3/4] Reading startup messages...")
        startup_messages = []
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                startup_messages.append(line)
                print(f"      📥 {line}")
        
        if not startup_messages:
            print(f"      ⚠️  No startup messages received")
        
        # Test PING command
        print(f"[4/4] Testing PING command...")
        ser.write(b"PING\n")
        time.sleep(0.3)
        
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"      📥 {response}")
            
            if "PONG" in response:
                print(f"\n✅ SUCCESS! Arduino is responding correctly")
                
                # Test a few more commands
                print(f"\nTesting additional commands...")
                
                # Test LED ON
                print(f"  Sending: ON:60:100 (Middle C)")
                ser.write(b"ON:60:100\n")
                time.sleep(0.1)
                if ser.in_waiting > 0:
                    print(f"    📥 {ser.readline().decode('utf-8', errors='ignore').strip()}")
                
                time.sleep(0.5)
                
                # Test LED OFF
                print(f"  Sending: OFF:60")
                ser.write(b"OFF:60\n")
                time.sleep(0.1)
                if ser.in_waiting > 0:
                    print(f"    📥 {ser.readline().decode('utf-8', errors='ignore').strip()}")
                
                print(f"\n✅ All tests passed!")
                ser.close()
                return True
            else:
                print(f"\n❌ Unexpected response to PING: {response}")
        else:
            print(f"\n❌ No response to PING command")
        
        ser.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return False

def main():
    print("="*60)
    print("Quick Arduino Connection Test")
    print("Testing at 115200 baud (new protocol)")
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
        print(f"  2. Check that the correct sketch is uploaded (ws2812b_piano_leds.ino)")
        print(f"  3. Verify the sketch uses Serial.begin(115200)")
        print(f"  4. Try pressing the reset button on Arduino")
        print(f"  5. Check Arduino IDE Serial Monitor at 115200 baud")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    input("\nPress Enter to exit...")
