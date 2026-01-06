"""
FNIRSI Raw Serial Test
Простой тест для отладки связи с устройством
"""
import serial
import time


def test_port(port: str, baud: int = 9600):
    """Raw test of serial port"""
    print(f"\n{'='*50}")
    print(f"Testing {port} @ {baud} baud")
    print('='*50)
    
    # CONNECT command: F1 C1 00 01 01 02
    CMD_CONNECT = bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02])
    
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=0.5,
            write_timeout=None,
            rtscts=False,
            dsrdtr=False
        )
        
        print(f"Port opened: {ser.name}")
        print(f"Settings: {ser.baudrate} baud, {ser.bytesize}{ser.parity}{ser.stopbits}")
        
        # Set control lines
        ser.rts = True
        ser.dtr = True
        print(f"RTS={ser.rts}, DTR={ser.dtr}, CTS={ser.cts}, DSR={ser.dsr}")
        
        # Clear buffers
        time.sleep(0.2)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Send CONNECT
        print(f"\nSending: {CMD_CONNECT.hex(' ').upper()}")
        written = ser.write(CMD_CONNECT)
        ser.flush()
        print(f"Written {written} bytes")
        
        # Wait and read
        print("\nWaiting for response...")
        for i in range(10):
            time.sleep(0.2)
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                print(f"  Received ({len(data)} bytes): {data.hex(' ').upper()}")
                
                # Look for 0xF0 header
                if 0xF0 in data:
                    print("  >>> Found response header 0xF0!")
            else:
                print(f"  ({i+1}) No data...")
        
        # Try reading any leftover data
        time.sleep(0.5)
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"\nFinal read ({len(data)} bytes): {data.hex(' ').upper()}")
        
        ser.close()
        print("\nPort closed")
        
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    port = sys.argv[1] if len(sys.argv) > 1 else "COM11"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 9600
    
    test_port(port, baud)
    
    # Also try 115200 if default baud failed
    if baud == 9600:
        print("\n" + "="*50)
        print("Trying 115200 baud...")
        test_port(port, 115200)
