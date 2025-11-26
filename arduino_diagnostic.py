"""
Advanced Arduino Diagnostic Tool
Tests multiple baudrates and communication methods
"""

import serial
import serial.tools.list_ports
import time

def test_baudrates(port_name):
    """Test multiple baudrates to find the correct one"""
    baudrates = [115200, 9600, 57600, 38400, 19200, 14400, 4800, 2400, 1200]
    
    print(f"\n{'='*60}")
    print(f"Testing {port_name} with multiple baudrates")
    print(f"{'='*60}\n")
    
    for baud in baudrates:
        print(f"📡 Trying {baud} baud...", end=" ")
        try:
            ser = serial.Serial(port_name, baud, timeout=1.0)
            
            # Don't wait for reset at first
            time.sleep(0.5)
            
            # Clear buffer
            while ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                try:
                    text = data.decode('utf-8', errors='ignore').strip()
                    if text:
                        print(f"\n  📥 Got data: {text[:50]}...")
                except:
                    pass
            
            # Try PING
            ser.write(b"PING\n")
            time.sleep(0.3)
            
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    print(f"✅ Response: {response}")
                    
                    if "PONG" in response or "READY" in response:
                        print(f"\n🎉 SUCCESS! Arduino is at {baud} baud!")
                        
                        # Do more tests
                        print(f"\nTesting additional commands at {baud} baud:")
                        
                        # Test ON command
                        print(f"  Sending: ON:60:100")
                        ser.write(b"ON:60:100\n")
                        time.sleep(0.2)
                        if ser.in_waiting > 0:
                            resp = ser.readline().decode('utf-8', errors='ignore').strip()
                            print(f"    📥 {resp}")
                        
                        # Test OFF command
                        print(f"  Sending: OFF:60")
                        ser.write(b"OFF:60\n")
                        time.sleep(0.2)
                        if ser.in_waiting > 0:
                            resp = ser.readline().decode('utf-8', errors='ignore').strip()
                            print(f"    📥 {resp}")
                        
                        ser.close()
                        return baud
                    else:
                        print(f"⚠️  Unexpected: {response}")
                else:
                    print(f"❌ Empty response")
            else:
                print(f"❌ No response")
            
            ser.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(0.5)
    
    print(f"\n❌ No working baudrate found")
    return None

def manual_monitor(port_name, baudrate=115200):
    """Open a manual serial monitor to see what Arduino is sending"""
    print(f"\n{'='*60}")
    print(f"Manual Serial Monitor")
    print(f"Port: {port_name} | Baudrate: {baudrate}")
    print(f"Press Ctrl+C to exit")
    print(f"{'='*60}\n")
    
    try:
        ser = serial.Serial(port_name, baudrate, timeout=0.1)
        print(f"✅ Port opened. Listening...")
        print(f"💡 Try pressing the reset button on your Arduino\n")
        
        last_time = time.time()
        
        while True:
            # Read data
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                try:
                    text = data.decode('utf-8', errors='ignore')
                    if text:
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] 📥 {text}", end="")
                        last_time = time.time()
                except:
                    print(f"[Raw bytes] {data.hex()}")
            
            # Send heartbeat every 5 seconds
            if time.time() - last_time > 5:
                ser.write(b"PING\n")
                last_time = time.time()
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

def check_drivers():
    """Check if CH340 drivers are installed"""
    print(f"\n{'='*60}")
    print(f"Driver Check")
    print(f"{'='*60}\n")
    
    ports = serial.tools.list_ports.comports()
    
    print(f"Found {len(ports)} serial port(s):\n")
    
    for port in ports:
        print(f"📌 {port.device}")
        print(f"   Description: {port.description}")
        print(f"   Manufacturer: {port.manufacturer}")
        print(f"   Hardware ID: {port.hwid}")
        
        # Check if it's a CH340
        if 'CH340' in port.description or 'CH341' in port.description:
            print(f"   ⚠️  CH340 chip detected - make sure drivers are installed!")
            print(f"   Download: http://www.wch.cn/downloads/CH341SER_ZIP.html")
        
        print()

def main():
    print("="*60)
    print("Arduino Advanced Diagnostic Tool")
    print("="*60)
    
    # Check drivers and ports
    check_drivers()
    
    # Find Arduino ports
    ports = serial.tools.list_ports.comports()
    arduino_ports = [p for p in ports if any(k in p.description.lower() 
                     for k in ['arduino', 'ch340', 'ch341', 'usb-serial'])]
    
    if not arduino_ports:
        print("❌ No Arduino devices found!")
        
        port_name = input("\nEnter COM port manually (or press Enter to skip): ").strip()
        if not port_name:
            return
        arduino_ports = [type('obj', (object,), {'device': port_name})]
    
    for port in arduino_ports:
        port_name = port.device
        
        print(f"\n{'='*60}")
        print(f"Testing {port_name}")
        print(f"{'='*60}")
        
        # Option menu
        print(f"\nWhat would you like to do?")
        print(f"  1. Test all baudrates (auto-detect)")
        print(f"  2. Manual monitor at 115200 baud")
        print(f"  3. Manual monitor at 9600 baud")
        print(f"  4. Skip this port")
        
        choice = input("\nChoice [1]: ").strip() or "1"
        
        if choice == "1":
            baud = test_baudrates(port_name)
            if baud:
                print(f"\n✅ Found working configuration:")
                print(f"   Port: {port_name}")
                print(f"   Baudrate: {baud}")
                
                # Update settings
                print(f"\n💡 Update your code to use:")
                print(f"   serial.Serial('{port_name}', {baud})")
                break
        
        elif choice == "2":
            manual_monitor(port_name, 115200)
        
        elif choice == "3":
            manual_monitor(port_name, 9600)
        
        else:
            continue
    
    print(f"\n{'='*60}")
    print(f"Diagnostic Complete")
    print(f"{'='*60}\n")
    
    print(f"Next steps:")
    print(f"  1. Make sure the Arduino sketch is uploaded")
    print(f"  2. Check Arduino IDE Serial Monitor to verify sketch is running")
    print(f"  3. Verify Serial.begin() baudrate in sketch matches Python")
    print(f"  4. If using CH340 chip, install drivers from:")
    print(f"     http://www.wch.cn/downloads/CH341SER_ZIP.html")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrupted by user")
    
    input("\nPress Enter to exit...")
