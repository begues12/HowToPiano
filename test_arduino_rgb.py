"""
Test script for Arduino text protocol with RGB support
Tests all commands: ON, LED, OFF, BATCH, CLEAR, BRIGHTNESS, TEST, PING
"""
import serial
import time
import serial.tools.list_ports

def find_arduino():
    """Find Arduino port automatically"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            return port.device
    return None

def test_arduino_rgb():
    # Find Arduino
    port = find_arduino()
    if not port:
        print("❌ No Arduino found. Please specify COM port manually.")
        port = input("Enter COM port (e.g., COM19): ").strip()
    
    print(f"🔌 Connecting to {port} at 115200 baud...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)  # Wait for Arduino startup
        
        # Read READY message
        ready = False
        for _ in range(10):
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"Arduino: {line}")
                if line == "READY":
                    ready = True
                    break
        
        if not ready:
            print("⚠️ No READY signal, continuing anyway...")
        
        print("\n✅ Connected! Starting tests...\n")
        
        # Test 1: PING
        print("Test 1: PING")
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(0.2)
        if ser.in_waiting:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"  Response: {response}")
        
        # Test 2: ON command (default green with brightness)
        print("\nTest 2: ON command (green with brightness)")
        for note in [21, 40, 60, 80, 108]:  # A0, E2, C4, G#5, C8
            brightness = 100
            print(f"  ON:{note}:{brightness}")
            ser.write(f"ON:{note}:{brightness}\n".encode())
            ser.flush()
            time.sleep(0.1)
        
        time.sleep(1)
        
        # Clear
        print("\nClearing...")
        ser.write(b"CLEAR\n")
        ser.flush()
        time.sleep(0.5)
        
        # Test 3: LED command (RGB colors)
        print("\nTest 3: LED command (RGB colors)")
        
        # Red
        print("  Red: LED:60,255,0,0")
        ser.write(b"LED:60,255,0,0\n")
        ser.flush()
        time.sleep(0.5)
        
        # Green
        print("  Green: LED:62,0,255,0")
        ser.write(b"LED:62,0,255,0\n")
        ser.flush()
        time.sleep(0.5)
        
        # Blue
        print("  Blue: LED:64,0,0,255")
        ser.write(b"LED:64,0,0,255\n")
        ser.flush()
        time.sleep(0.5)
        
        # Yellow
        print("  Yellow: LED:65,255,255,0")
        ser.write(b"LED:65,255,255,0\n")
        ser.flush()
        time.sleep(0.5)
        
        # Magenta
        print("  Magenta: LED:67,255,0,255")
        ser.write(b"LED:67,255,0,255\n")
        ser.flush()
        time.sleep(0.5)
        
        # Cyan
        print("  Cyan: LED:69,0,255,255")
        ser.write(b"LED:69,0,255,255\n")
        ser.flush()
        time.sleep(1)
        
        # Test 4: OFF command
        print("\nTest 4: OFF command")
        for note in [60, 62, 64, 65, 67, 69]:
            print(f"  OFF:{note}")
            ser.write(f"OFF:{note}\n".encode())
            ser.flush()
            time.sleep(0.2)
        
        time.sleep(0.5)
        
        # Test 5: BATCH command (multiple LEDs at once)
        print("\nTest 5: BATCH command (C major chord - red, green, blue)")
        batch_cmd = "BATCH:60,255,0,0;64,0,255,0;67,0,0,255\n"
        print(f"  {batch_cmd.strip()}")
        ser.write(batch_cmd.encode())
        ser.flush()
        time.sleep(1.5)
        
        # Clear
        print("\nClearing...")
        ser.write(b"CLEAR\n")
        ser.flush()
        time.sleep(0.5)
        
        # Test 6: BRIGHTNESS
        print("\nTest 6: BRIGHTNESS control")
        ser.write(b"LED:60,255,255,255\n")  # White LED
        ser.flush()
        
        for brightness in [255, 128, 64, 32, 128, 255]:
            print(f"  BRIGHTNESS:{brightness}")
            ser.write(f"BRIGHTNESS:{brightness}\n".encode())
            ser.flush()
            time.sleep(0.5)
        
        # Clear
        print("\nClearing...")
        ser.write(b"CLEAR\n")
        ser.flush()
        time.sleep(0.5)
        
        # Test 7: TEST animation
        print("\nTest 7: TEST animation (RGB sweep)")
        ser.write(b"TEST\n")
        ser.flush()
        
        # Read test messages
        time.sleep(3)
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"  Arduino: {line}")
        
        print("\n✅ All tests complete!")
        
        # Final cleanup
        print("\nFinal cleanup...")
        ser.write(b"CLEAR\n")
        ser.flush()
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("Arduino RGB LED Test - Text Protocol")
    print("=" * 60)
    test_arduino_rgb()
