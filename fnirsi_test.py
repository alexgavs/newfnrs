"""
FNIRSI Power Supply - Test Connection
Based on decompiled C# code from 数控电源上位机

Protocol format:
  Request:  [0xF1] [CmdType] [Register] [Length] [Data...] [Checksum]
  Response: [0xF0] [CmdType] [Register] [Length] [Data...] [Checksum]
  
Checksum = (register + length + sum(data)) & 0xFF  (NO cmd_type!)

Data format: IEEE 754 float, little-endian
"""
import serial
import serial.tools.list_ports
import struct
import time
from dataclasses import dataclass
from typing import Optional, List


def float_to_bytes(value: float) -> bytes:
    """Convert float to 4 bytes (little-endian IEEE 754)"""
    return struct.pack('<f', value)


def bytes_to_float(data: bytes, offset: int = 0) -> float:
    """Convert 4 bytes to float (little-endian IEEE 754)"""
    return struct.unpack('<f', data[offset:offset+4])[0]


def make_command(cmd_type: int, register: int, data: bytes) -> bytes:
    """Create command packet"""
    length = len(data)
    # Checksum: register + length + sum(data) - NO cmd_type!
    checksum = (register + length + sum(data)) & 0xFF
    return bytes([0xF1, cmd_type, register, length]) + data + bytes([checksum])


def hex_dump(data: bytes) -> str:
    """Format bytes as hex string"""
    return ' '.join(f'{b:02X}' for b in data)


# Command definitions based on Command.cs
class Commands:
    """Command constants from decompiled code"""
    # CMD_1: Connect (0xF1, 0xC1, 0x00, 0x01)
    CONNECT = make_command(0xC1, 0x00, b'\x01')
    
    # CMD_2: Disconnect (0xF1, 0xC1, 0x00, 0x00)
    DISCONNECT = make_command(0xC1, 0x00, b'\x00')
    
    # CMD_3: Read all parameters (0xF1, 0xA1, 0xFF, 0x00)
    READ_ALL = make_command(0xA1, 0xFF, b'\x00')
    
    # CMD_4: Read voltage setting (0xF1, 0xA1, 0xC0, 0x00)
    READ_VOLTAGE = make_command(0xA1, 0xC0, b'\x00')
    
    # CMD_5: Read current limit (0xF1, 0xA1, 0xDE, 0x00)
    READ_CURRENT = make_command(0xA1, 0xDE, b'\x00')
    
    # CMD_6: Read model info (0xF1, 0xA1, 0xE0, 0x00)
    READ_MODEL = make_command(0xA1, 0xE0, b'\x00')
    
    # CMD_7: Read firmware version (0xF1, 0xA1, 0xE1, 0x00)
    READ_FIRMWARE = make_command(0xA1, 0xE1, b'\x00')
    
    # CMD_8: Output OFF (0xF1, 0xB1, 0xDB, 0x00)
    OUTPUT_OFF = make_command(0xB1, 0xDB, b'\x00')
    
    # CMD_9: Output ON (0xF1, 0xB1, 0xDB, 0x01)
    OUTPUT_ON = make_command(0xB1, 0xDB, b'\x01')
    
    # CMD_14: Read live values (0xF1, 0xA1, 0xC3, 0x00)
    READ_LIVE = make_command(0xA1, 0xC3, b'\x00')
    
    # CMD_16: Read serial number (0xF1, 0xA1, 0xDF, 0x00)
    READ_SERIAL = make_command(0xA1, 0xDF, b'\x00')
    
    @staticmethod
    def set_voltage(voltage: float) -> bytes:
        """Set voltage - CMD with register 0xC0 and cmd_type 0xB0"""
        return make_command(0xB0, 0xC0, float_to_bytes(voltage))
    
    @staticmethod
    def set_current(current: float) -> bytes:
        """Set current limit - CMD with register 0xDE and cmd_type 0xB0"""
        return make_command(0xB0, 0xDE, float_to_bytes(current))
    
    @staticmethod
    def set_baud_rate(baud_index: int) -> bytes:
        """Set baud rate (1=9600, 2=19200, 3=38400, 4=57600, 5=115200)"""
        return make_command(0xB0, 0x00, bytes([baud_index]))


@dataclass
class DeviceData:
    """Device data structure based on SerialData.cs"""
    # Basic readings
    input_voltage: float = 0.0      # Data1 - offset 0
    set_voltage: float = 0.0        # Data2 - offset 4
    set_current: float = 0.0        # Data3 - offset 8
    output_voltage: float = 0.0     # Data4 - offset 12
    output_current: float = 0.0     # Data5 - offset 16
    output_power: float = 0.0       # Data6 - offset 20
    temperature: float = 0.0        # Data7 - offset 24
    
    # Limits
    max_voltage: float = 0.0        # Data37 - offset 111
    max_current: float = 0.0        # Data38 - offset 115
    
    # Status
    output_enabled: bool = False    # Data30 - offset 107
    protection_status: int = 0      # Data31 - offset 108
    mode: int = 0                   # Data32 - offset 109 (0=CV, 1=CC)
    
    # Capacity counters
    capacity_ah: float = 0.0        # Data28 - offset 99
    capacity_wh: float = 0.0        # Data29 - offset 103
    
    # Device info
    model: str = ""                 # Data33
    serial_number: str = ""         # Data34
    firmware: str = ""              # Data35
    
    @property
    def mode_string(self) -> str:
        return "CC" if self.mode == 1 else "CV"
    
    @property
    def protection_string(self) -> str:
        status_map = {
            0: "OK",
            1: "OVP",  # Over Voltage Protection
            2: "OCP",  # Over Current Protection
            3: "OPP",  # Over Power Protection
            4: "OTP",  # Over Temperature Protection
            5: "SCP",  # Short Circuit Protection
        }
        return status_map.get(self.protection_status, f"Unknown({self.protection_status})")


def parse_response(data: bytes, device: DeviceData) -> bool:
    """Parse response packet based on SerialData.cs setData()"""
    if len(data) < 5 or data[0] != 0xF0:
        return False
    
    cmd_type = data[1]
    register = data[2]
    length = data[3]
    
    if len(data) < 5 + length:
        return False
    
    payload = data[4:4 + length]
    checksum = data[4 + length]
    
    # Verify checksum
    calc_cs = (register + length + sum(payload)) & 0xFF
    if calc_cs != checksum:
        print(f"  [!] Checksum mismatch: expected {checksum:02X}, got {calc_cs:02X}")
        return False
    
    # Parse by register (based on SerialData.cs switch)
    if register == 0xC0:  # Voltage setting (192)
        device.input_voltage = bytes_to_float(payload, 0)
        
    elif register == 0xC3:  # Live readings (195)
        if len(payload) >= 12:
            device.output_voltage = bytes_to_float(payload, 0)
            device.output_current = bytes_to_float(payload, 4)
            device.output_power = bytes_to_float(payload, 8)
            
    elif register == 0xC4:  # Temperature (196)
        device.temperature = bytes_to_float(payload, 0)
        
    elif register == 0xD9:  # Capacity Ah (217)
        device.capacity_ah = bytes_to_float(payload, 0)
        
    elif register == 0xDA:  # Capacity Wh (218)
        device.capacity_wh = bytes_to_float(payload, 0)
        
    elif register == 0xDB:  # Output status (219)
        device.output_enabled = payload[0] == 0
        
    elif register == 0xDC:  # Protection status (220)
        device.protection_status = payload[0]
        
    elif register == 0xDD:  # Mode CV/CC (221)
        device.mode = payload[0]
        
    elif register == 0xDE:  # Model string (222)
        device.model = payload.decode('ascii', errors='ignore').strip('\x00')
        
    elif register == 0xDF:  # Serial number (223)
        device.serial_number = payload.decode('ascii', errors='ignore').strip('\x00')
        
    elif register == 0xE0:  # Firmware string (224)
        device.firmware = payload.decode('ascii', errors='ignore').strip('\x00')
        
    elif register == 0xE2:  # Max voltage (226)
        device.max_voltage = bytes_to_float(payload, 0)
        
    elif register == 0xE3:  # Max current (227)
        device.max_current = bytes_to_float(payload, 0)
        
    elif register == 0xFF:  # All data (255) - based on setAllData()
        if len(payload) >= 119:
            device.input_voltage = bytes_to_float(payload, 0)
            device.set_voltage = bytes_to_float(payload, 4)
            device.set_current = bytes_to_float(payload, 8)
            device.output_voltage = bytes_to_float(payload, 12)
            device.output_current = bytes_to_float(payload, 16)
            device.output_power = bytes_to_float(payload, 20)
            device.temperature = bytes_to_float(payload, 24)
            device.capacity_ah = bytes_to_float(payload, 99)
            device.capacity_wh = bytes_to_float(payload, 103)
            device.output_enabled = payload[107] == 0
            device.protection_status = payload[108]
            device.mode = payload[109]
            device.max_voltage = bytes_to_float(payload, 111)
            device.max_current = bytes_to_float(payload, 115)
    
    return True


def parse_buffer(buffer: bytearray, device: DeviceData) -> int:
    """Parse all packets from buffer, return number of bytes consumed"""
    consumed = 0
    
    while len(buffer) - consumed >= 5:
        if buffer[consumed] != 0xF0:
            consumed += 1
            continue
        
        if len(buffer) - consumed < 4:
            break
        
        length = buffer[consumed + 3]
        packet_len = 5 + length
        
        if len(buffer) - consumed < packet_len:
            break
        
        packet = bytes(buffer[consumed:consumed + packet_len])
        parse_response(packet, device)
        consumed += packet_len
    
    return consumed


def list_ports() -> List[str]:
    """List available COM ports"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def test_connection(port: str = "COM11", baud: int = 9600):
    """Test connection to FNIRSI power supply"""
    print("=" * 60)
    print("FNIRSI Power Supply - Connection Test")
    print("=" * 60)
    
    # List ports
    available_ports = list_ports()
    print(f"\nAvailable ports: {available_ports}")
    print(f"Using port: {port}, Baud: {baud}")
    
    if port not in available_ports:
        print(f"\n[!] Port {port} not found!")
        return False
    
    device = DeviceData()
    buffer = bytearray()
    
    try:
        # Open port
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5
        )
        ser.rts = True
        ser.dtr = True
        ser.reset_input_buffer()
        time.sleep(0.1)
        print(f"\n[+] Port opened successfully")
        
        # Step 1: Send CONNECT
        print(f"\n[1] Sending CONNECT: {hex_dump(Commands.CONNECT)}")
        ser.write(Commands.CONNECT)
        ser.flush()
        time.sleep(0.5)
        
        # Read response
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"    Response ({len(data)} bytes): {hex_dump(data[:60])}...")
            buffer.extend(data)
        
        # Step 2: Send READ_ALL
        print(f"\n[2] Sending READ_ALL: {hex_dump(Commands.READ_ALL)}")
        ser.write(Commands.READ_ALL)
        ser.flush()
        time.sleep(0.5)
        
        # Read response
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"    Response ({len(data)} bytes): {hex_dump(data[:60])}...")
            buffer.extend(data)
        
        # Parse buffer
        consumed = parse_buffer(buffer, device)
        buffer = buffer[consumed:]
        
        # Step 3: Request model info
        print(f"\n[3] Sending READ_MODEL: {hex_dump(Commands.READ_MODEL)}")
        ser.write(Commands.READ_MODEL)
        time.sleep(0.3)
        
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"    Response ({len(data)} bytes): {hex_dump(data)}")
            buffer.extend(data)
            consumed = parse_buffer(buffer, device)
            buffer = buffer[consumed:]
        
        # Step 4: Request firmware
        print(f"\n[4] Sending READ_FIRMWARE: {hex_dump(Commands.READ_FIRMWARE)}")
        ser.write(Commands.READ_FIRMWARE)
        time.sleep(0.3)
        
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"    Response ({len(data)} bytes): {hex_dump(data)}")
            buffer.extend(data)
            consumed = parse_buffer(buffer, device)
            buffer = buffer[consumed:]
        
        # Step 5: Read live values
        print(f"\n[5] Reading live values for 3 seconds...")
        start = time.time()
        while time.time() - start < 3:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                buffer.extend(data)
                consumed = parse_buffer(buffer, device)
                buffer = buffer[consumed:]
            time.sleep(0.1)
        
        # Print device info
        print("\n" + "=" * 60)
        print("Device Information:")
        print("=" * 60)
        print(f"  Model:         {device.model or 'N/A'}")
        print(f"  Firmware:      {device.firmware or 'N/A'}")
        print(f"  Serial:        {device.serial_number or 'N/A'}")
        print(f"  Max Voltage:   {device.max_voltage:.1f}V")
        print(f"  Max Current:   {device.max_current:.2f}A")
        print()
        print("Current Status:")
        print(f"  Input Voltage: {device.input_voltage:.2f}V")
        print(f"  Set Voltage:   {device.set_voltage:.2f}V")
        print(f"  Set Current:   {device.set_current:.3f}A")
        print(f"  Output:        {'ON' if device.output_enabled else 'OFF'}")
        print(f"  Mode:          {device.mode_string}")
        print(f"  Protection:    {device.protection_string}")
        print()
        print("Measurements:")
        print(f"  Voltage:       {device.output_voltage:.4f}V")
        print(f"  Current:       {device.output_current:.5f}A")
        print(f"  Power:         {device.output_power:.3f}W")
        print(f"  Temperature:   {device.temperature:.1f}°C")
        print(f"  Capacity:      {device.capacity_ah:.3f}Ah / {device.capacity_wh:.3f}Wh")
        
        # Close with DISCONNECT
        print(f"\n[6] Sending DISCONNECT: {hex_dump(Commands.DISCONNECT)}")
        ser.write(Commands.DISCONNECT)
        time.sleep(0.1)
        
        ser.close()
        print("\n[+] Connection test completed!")
        return True
        
    except serial.SerialException as e:
        print(f"\n[!] Serial error: {e}")
        return False
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    port = sys.argv[1] if len(sys.argv) > 1 else "COM11"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 9600
    
    test_connection(port, baud)
