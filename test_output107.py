"""
Тест команды OUTPUT с правильным offset 107
"""
import serial
import time

PORT = "COM11"
BAUD = 9600

def get_output_state(port):
    """Получить состояние offset 107"""
    port.reset_input_buffer()
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.3)
    data = port.read(300)
    
    start = data.find(b'\xF0\xA1\xFF')
    if start < 0:
        return None
    
    length = data[start + 3]
    payload = data[start + 4 : start + 4 + length]
    
    if len(payload) > 108:
        return payload[107], payload[108]
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
    
    # Попробуем отправить команду OUTPUT_OFF
    print("\nSending OUTPUT_OFF...")
    cmd = bytes([0xF1, 0xB1, 0xDB, 0x01, 0x00, 0xDC])
    print(f"  TX: {cmd.hex(' ').upper()}")
    port.write(cmd)
    time.sleep(0.5)
    
    out, mode = get_output_state(port)
    print(f"After OFF: output={out}, mode={mode}")
    
    time.sleep(1)
    
    # Попробуем отправить команду OUTPUT_ON
    print("\nSending OUTPUT_ON...")
    cmd = bytes([0xF1, 0xB1, 0xDB, 0x01, 0x01, 0xDD])
    print(f"  TX: {cmd.hex(' ').upper()}")
    port.write(cmd)
    time.sleep(0.5)
    
    out, mode = get_output_state(port)
    print(f"After ON: output={out}, mode={mode}")
    
    port.close()
    print("\nDone")

if __name__ == "__main__":
    main()
