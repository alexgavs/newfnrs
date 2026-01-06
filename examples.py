"""
FNIRSI Power Supply - Usage Examples
====================================

This file demonstrates how to use the fnirsi.py library
to control FNIRSI power supplies.
"""
from fnirsi import FnirsiDevice, Commands, find_fnirsi_device
import time


def example_basic_connection():
    """Basic connection example"""
    print("=" * 50)
    print("Example 1: Basic Connection")
    print("=" * 50)
    
    device = FnirsiDevice()
    
    # Set error handler
    device.on_error(lambda e: print(f"  [Error] {e}"))
    
    # List available ports
    print("\nAvailable COM ports:")
    for port in device.list_ports_detailed():
        print(f"  {port['device']}: {port['description']}")
    
    # Try to connect
    port = "COM11"  # Change this to your port
    print(f"\nConnecting to {port}...")
    
    if device.connect(port):
        print("  Connected successfully!")
        print(f"\nDevice Info:")
        print(f"  Model:       {device.data.model}")
        print(f"  Firmware:    {device.data.firmware}")
        print(f"  Max Voltage: {device.data.max_voltage}V")
        print(f"  Max Current: {device.data.max_current}A")
        
        device.disconnect()
        print("\n  Disconnected.")
    else:
        print("  Connection failed!")


def example_set_values():
    """Example: Set voltage and current"""
    print("=" * 50)
    print("Example 2: Set Voltage and Current")
    print("=" * 50)
    
    device = FnirsiDevice()
    
    if device.connect("COM11"):
        print("\nConnected!")
        
        # Set voltage to 5V
        print("\nSetting voltage to 5.0V...")
        device.set_voltage(5.0)
        time.sleep(0.5)
        
        # Set current limit to 1A
        print("Setting current limit to 1.0A...")
        device.set_current(1.0)
        time.sleep(0.5)
        
        # Read current values
        device.read_all()
        time.sleep(0.5)
        
        print(f"\nCurrent settings:")
        print(f"  Set Voltage: {device.data.set_voltage}V")
        print(f"  Set Current: {device.data.set_current}A")
        
        device.disconnect()
    else:
        print("Connection failed!")


def example_output_control():
    """Example: Control output on/off"""
    print("=" * 50)
    print("Example 3: Output Control")
    print("=" * 50)
    
    device = FnirsiDevice()
    
    if device.connect("COM11"):
        print("\nConnected!")
        
        # Turn output ON
        print("\nTurning output ON...")
        device.output_on()
        time.sleep(1)
        
        print(f"  Output: {'ON' if device.data.output_enabled else 'OFF'}")
        
        # Read values for 3 seconds
        print("\nReading values for 3 seconds...")
        for i in range(6):
            time.sleep(0.5)
            print(f"  V={device.data.output_voltage:.3f}V  "
                  f"A={device.data.output_current:.4f}A  "
                  f"W={device.data.output_power:.2f}W")
        
        # Turn output OFF
        print("\nTurning output OFF...")
        device.output_off()
        time.sleep(0.5)
        
        print(f"  Output: {'ON' if device.data.output_enabled else 'OFF'}")
        
        device.disconnect()
    else:
        print("Connection failed!")


def example_with_callbacks():
    """Example: Using callbacks for real-time updates"""
    print("=" * 50)
    print("Example 4: Real-time Updates with Callbacks")
    print("=" * 50)
    
    device = FnirsiDevice()
    
    # Set data callback
    def on_data_update(data):
        print(f"  [Data] V={data.output_voltage:.3f}V  "
              f"A={data.output_current:.4f}A  "
              f"Mode={data.mode_string}")
    
    device.on_data(on_data_update)
    device.on_connect(lambda connected: print(f"  [Connect] {'Connected' if connected else 'Disconnected'}"))
    device.on_error(lambda error: print(f"  [Error] {error}"))
    
    if device.connect("COM11"):
        print("\nMonitoring for 5 seconds...")
        time.sleep(5)
        device.disconnect()
    else:
        print("Connection failed!")


def example_auto_find():
    """Example: Auto-find FNIRSI device"""
    print("=" * 50)
    print("Example 5: Auto-find Device")
    print("=" * 50)
    
    print("\nSearching for FNIRSI device...")
    port = find_fnirsi_device()
    
    if port:
        print(f"  Found device on {port}!")
        
        device = FnirsiDevice()
        if device.connect(port):
            print(f"  Model: {device.data.model}")
            device.disconnect()
    else:
        print("  Device not found on any port.")


def example_voltage_sweep():
    """Example: Voltage sweep"""
    print("=" * 50)
    print("Example 6: Voltage Sweep")
    print("=" * 50)
    
    device = FnirsiDevice()
    
    if device.connect("COM11"):
        print("\nConnected!")
        
        # Set current limit
        device.set_current(0.5)
        
        # Turn on output
        device.output_on()
        time.sleep(0.5)
        
        # Sweep voltage from 3V to 12V
        print("\nVoltage sweep 3V -> 12V:")
        for v in range(3, 13):
            device.set_voltage(float(v))
            time.sleep(1)
            
            print(f"  Set: {v}V  ->  "
                  f"Measured: {device.data.output_voltage:.3f}V  "
                  f"Current: {device.data.output_current:.4f}A")
        
        # Turn off
        device.output_off()
        device.disconnect()
        
        print("\nSweep complete!")
    else:
        print("Connection failed!")


if __name__ == "__main__":
    import sys
    
    print("\nFNIRSI Power Supply - Examples")
    print("==============================\n")
    
    # Check command line argument
    if len(sys.argv) > 1:
        example = sys.argv[1]
        examples = {
            "1": example_basic_connection,
            "2": example_set_values,
            "3": example_output_control,
            "4": example_with_callbacks,
            "5": example_auto_find,
            "6": example_voltage_sweep,
        }
        if example in examples:
            examples[example]()
        else:
            print(f"Unknown example: {example}")
    else:
        print("Available examples:")
        print("  1 - Basic connection")
        print("  2 - Set voltage/current")
        print("  3 - Output control")
        print("  4 - Real-time callbacks")
        print("  5 - Auto-find device")
        print("  6 - Voltage sweep")
        print("\nUsage: python examples.py <number>")
        print("\nRunning example 5 (auto-find)...\n")
        example_auto_find()
