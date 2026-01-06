"""
Полный тест контроллера FNIRSI
"""
from controller import FnirsiController
import time

def main():
    psu = FnirsiController()
    
    print("=" * 50)
    print("FNIRSI Controller Test")
    print("=" * 50)
    
    print("\n1. Connecting to COM11...")
    if not psu.connect("COM11", 9600, 3):
        print("FAILED!")
        return
    print("Connected!")
    
    time.sleep(0.5)
    s = psu.state
    
    print("\n2. Device Info:")
    print(f"   Model: {s.model}")
    print(f"   Firmware: {s.firmware}")
    print(f"   Max V: {s.max_voltage} V")
    print(f"   Max A: {s.max_current} A")
    
    print("\n3. Current State:")
    print(f"   Set V: {s.set_voltage} V")
    print(f"   Set A: {s.set_current} A")
    print(f"   Output V: {s.output_voltage} V")
    print(f"   Output A: {s.output_current} A")
    print(f"   Power: {s.output_power} W")
    print(f"   Temperature: {s.temperature:.1f} °C")
    print(f"   Output: {'ON' if s.output_enabled else 'OFF'}")
    print(f"   Mode: {s.mode_str}")
    print(f"   Protection: {s.protection_str}")
    
    print("\n4. Testing Output Toggle:")
    print(f"   Initial: {'ON' if psu.state.output_enabled else 'OFF'}")
    
    print("   Turning OFF...")
    psu.output_off()
    time.sleep(0.5)
    psu.read_all()
    time.sleep(0.3)
    print(f"   After OFF: {'ON' if psu.state.output_enabled else 'OFF'}")
    
    print("   Turning ON...")
    psu.output_on()
    time.sleep(0.5)
    psu.read_all()
    time.sleep(0.3)
    print(f"   After ON: {'ON' if psu.state.output_enabled else 'OFF'}")
    
    print("\n5. Testing Set Values:")
    print(f"   Current: {psu.state.set_voltage}V / {psu.state.set_current}A")
    
    print("   Setting 3.3V / 0.5A...")
    psu.set_voltage(3.3)
    psu.set_current(0.5)
    time.sleep(0.5)
    psu.read_all()
    time.sleep(0.3)
    print(f"   After: {psu.state.set_voltage}V / {psu.state.set_current}A")
    
    print("   Restoring 5.0V / 1.0A...")
    psu.set_voltage(5.0)
    psu.set_current(1.0)
    time.sleep(0.5)
    
    print("\n6. Disconnecting...")
    psu.disconnect()
    print("Done!")

if __name__ == "__main__":
    main()
