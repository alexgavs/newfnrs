"""
Тест логики ON/OFF для FNIRSI
"""
import serial
import time

PORT = "COM11"
BAUD = 9600

def main():
    print(f"Opening {PORT}...")
    try:
        port = serial.Serial(PORT, BAUD, timeout=2)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    time.sleep(0.5)
    
    # Connect
    print("Sending CONNECT...")
    port.write(bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02]))
    time.sleep(0.3)
    port.read(100)
    
    # Read initial state
    print("Reading state...")
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.5)
    data = port.read(300)
    
    if len(data) > 115:
        print(f"  Length: {len(data)}")
        print(f"  Offset 107 (output): {data[4+107]}")
        print(f"  Offset 108 (protection): {data[4+108]}")
        print(f"  Offset 109 (mode): {data[4+109]}")
        initial_state = data[4+107]
    else:
        print(f"  Not enough data: {len(data)}")
        port.close()
        return
    
    # Send OUTPUT_ON (data = 0x01)
    print("\nSending OUTPUT_ON (0x01)...")
    port.write(bytes([0xF1, 0xB1, 0xDB, 0x01, 0x01, 0xDD]))
    time.sleep(0.5)
    
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.5)
    data = port.read(300)
    if len(data) > 115:
        print(f"  Offset 107 after ON: {data[4+107]}")
    
    time.sleep(1)
    
    # Send OUTPUT_OFF (data = 0x00)
    print("\nSending OUTPUT_OFF (0x00)...")
    port.write(bytes([0xF1, 0xB1, 0xDB, 0x01, 0x00, 0xDC]))
    time.sleep(0.5)
    
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.5)
    data = port.read(300)
    if len(data) > 115:
        print(f"  Offset 107 after OFF: {data[4+107]}")
    
    port.close()
    print("\nDone")

if __name__ == "__main__":
    main()
