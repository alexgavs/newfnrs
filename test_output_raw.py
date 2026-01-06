"""
Тест переключения выхода - сырые данные
"""
import serial
import time

PORT = "COM11"
BAUD = 9600

def get_output_state(port):
    """Получить состояние выхода"""
    port.reset_input_buffer()
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.5)
    data = port.read(300)
    
    # Найти пакет
    start = data.find(b'\xF0\xA1\xFF')
    if start < 0:
        return None, None
    
    length = data[start + 3]
    payload = data[start + 4 : start + 4 + length]
    
    if len(payload) > 111:
        return payload[109], payload[110]  # output, mode
    return None, None

def main():
    print(f"Opening {PORT}...")
    port = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.5)
    
    # Connect
    port.write(bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02]))
    time.sleep(0.3)
    port.read(100)
    
    out, mode = get_output_state(port)
    print(f"Initial: output={out}, mode={mode}")
    
    # Try OUTPUT_OFF (0xDB = 0x00)
    print("\nSending OUTPUT_OFF (0x00)...")
    cmd = bytes([0xF1, 0xB1, 0xDB, 0x01, 0x00, 0xDC])
    print(f"  TX: {cmd.hex(' ').upper()}")
    port.write(cmd)
    time.sleep(0.5)
    
    # Read response
    resp = port.read(20)
    print(f"  RX: {resp.hex(' ').upper()}")
    
    out, mode = get_output_state(port)
    print(f"  After: output={out}, mode={mode}")
    
    time.sleep(1)
    
    # Try OUTPUT_ON (0xDB = 0x01)
    print("\nSending OUTPUT_ON (0x01)...")
    cmd = bytes([0xF1, 0xB1, 0xDB, 0x01, 0x01, 0xDD])
    print(f"  TX: {cmd.hex(' ').upper()}")
    port.write(cmd)
    time.sleep(0.5)
    
    resp = port.read(20)
    print(f"  RX: {resp.hex(' ').upper()}")
    
    out, mode = get_output_state(port)
    print(f"  After: output={out}, mode={mode}")
    
    port.close()
    print("\nDone")

if __name__ == "__main__":
    main()
