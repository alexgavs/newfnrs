"""
Анализ структуры ответа 0xFF от FNIRSI
"""
import serial
import struct
import time

PORT = "COM11"
BAUD = 9600

def bytes_to_float(data, offset):
    if len(data) >= offset + 4:
        return struct.unpack('<f', data[offset:offset+4])[0]
    return 0.0

def main():
    print(f"Opening {PORT}...")
    port = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.5)
    
    # Connect
    port.write(bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02]))
    time.sleep(0.3)
    port.read(100)
    
    # Read ALL
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.5)
    raw = port.read(300)
    
    print(f"Raw length: {len(raw)}")
    
    # Найти начало пакета F0 A1 FF
    start = raw.find(b'\xF0\xA1\xFF')
    if start < 0:
        print("Packet not found!")
        port.close()
        return
    
    print(f"Packet start at: {start}")
    length = raw[start + 3]
    print(f"Payload length: {length}")
    
    payload = raw[start + 4 : start + 4 + length]
    print(f"Payload actual: {len(payload)}")
    
    # Dump all float values
    print("\n=== All Float values ===")
    for i in range(0, len(payload)-3, 4):
        val = bytes_to_float(payload, i)
        # Filter only reasonable values
        if -1000 < val < 1000 and val != 0:
            print(f"  Offset {i:3d}: {val:12.4f}  |  bytes: {payload[i:i+4].hex(' ')}")
    
    # Dump bytes 100-140
    print("\n=== Bytes 100-140 ===")
    for i in range(100, min(len(payload), 140)):
        print(f"  [{i:3d}] = {payload[i]:3d} (0x{payload[i]:02X})")
    
    # Try to find max_voltage (should be 36.0)
    print("\n=== Searching for 36.0 (0x00 0x00 0x10 0x42) ===")
    target = struct.pack('<f', 36.0)
    for i in range(len(payload) - 3):
        if payload[i:i+4] == target:
            print(f"  Found at offset {i}")
    
    # Try to find 8.2 for max_current
    print("\n=== Searching for ~8.2 ===")
    for i in range(len(payload) - 3):
        val = bytes_to_float(payload, i)
        if 8.0 < val < 8.5:
            print(f"  Offset {i}: {val:.4f}")
    
    port.close()
    print("\nDone")

if __name__ == "__main__":
    main()
