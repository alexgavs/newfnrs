"""
FNIRSI Power Supply - Port Scanner
Scans all COM ports to find the FNIRSI device
"""
import serial
import serial.tools.list_ports
import time


def make_command(cmd_type: int, register: int, data: bytes) -> bytes:
    length = len(data)
    checksum = (register + length + sum(data)) & 0xFF
    return bytes([0xF1, cmd_type, register, length]) + data + bytes([checksum])


def hex_dump(data: bytes) -> str:
    return ' '.join(f'{b:02X}' for b in data)


def scan_port(port_name: str, baud: int = 9600) -> bool:
    """Try to connect to FNIRSI on specified port"""
    CMD_CONNECT = make_command(0xC1, 0x00, b'\x01')
    CMD_READ_ALL = make_command(0xA1, 0xFF, b'\x00')
    
    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5,
            write_timeout=1
        )
        ser.rts = True
        ser.dtr = True
        ser.reset_input_buffer()
        time.sleep(0.1)
        
        # Send connect
        ser.write(CMD_CONNECT)
        ser.flush()
        time.sleep(0.3)
        
        # Try to read
        response = b''
        if ser.in_waiting:
            response = ser.read(ser.in_waiting)
        
        # Send read all
        ser.write(CMD_READ_ALL)
        ser.flush()
        time.sleep(0.5)
        
        if ser.in_waiting:
            response += ser.read(ser.in_waiting)
        
        ser.close()
        
        # Check if we got valid response (starts with 0xF0)
        if response and 0xF0 in response:
            return True, response
        return False, response
        
    except serial.SerialException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("FNIRSI Power Supply - Port Scanner")
    print("=" * 60)
    
    ports = serial.tools.list_ports.comports()
    print(f"\nFound {len(ports)} COM ports:")
    for p in ports:
        print(f"  {p.device}: {p.description}")
    
    print("\nScanning for FNIRSI device...")
    print("-" * 60)
    
    bauds = [9600, 115200]
    
    for port in ports:
        for baud in bauds:
            print(f"\nTrying {port.device} @ {baud} baud...", end=" ", flush=True)
            result, data = scan_port(port.device, baud)
            
            if result:
                print("FOUND!")
                print(f"  Response: {hex_dump(data[:80] if len(data) > 80 else data)}")
                if len(data) > 80:
                    print(f"  ... and {len(data) - 80} more bytes")
                return port.device, baud
            else:
                if isinstance(data, bytes) and data:
                    print(f"Response but no 0xF0: {hex_dump(data[:40])}")
                elif isinstance(data, str):
                    if "timeout" in data.lower():
                        print("Timeout")
                    elif "denied" in data.lower() or "busy" in data.lower():
                        print("Port busy")
                    else:
                        print(f"Error: {data[:50]}")
                else:
                    print("No response")
    
    print("\n" + "-" * 60)
    print("FNIRSI device not found on any port!")
    return None, None


if __name__ == "__main__":
    port, baud = main()
    if port:
        print(f"\n>>> Use: python fnirsi_test.py {port} {baud}")
