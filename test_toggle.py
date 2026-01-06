"""
Тест переключения выхода с задержками
"""
import serial
import time

PORT = "COM11"
BAUD = 9600

def get_output_state(port):
    """Получить состояние offset 107"""
    port.reset_input_buffer()
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.5)
    data = port.read(300)
    
    start = data.find(b'\xF0\xA1\xFF')
    if start < 0:
        return None
    
    length = data[start + 3]
    payload = data[start + 4 : start + 4 + length]
    
    if len(payload) > 108:
        return payload[107]
    return None

def main():
    print(f"Opening {PORT}...")
    port = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.5)
    
    # Connect
    port.write(bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02]))
    time.sleep(0.3)
    port.read(100)
    
    for i in range(5):
        out = get_output_state(port)
        print(f"State #{i}: output={out}")
        
        if i % 2 == 0:
            print("  -> Sending OFF")
            port.write(bytes([0xF1, 0xB1, 0xDB, 0x01, 0x00, 0xDC]))
        else:
            print("  -> Sending ON")
            port.write(bytes([0xF1, 0xB1, 0xDB, 0x01, 0x01, 0xDD]))
        
        time.sleep(1)  # Ждём 1 секунду
        port.read(100)  # Очищаем буфер
    
    out = get_output_state(port)
    print(f"Final: output={out}")
    
    port.close()
    print("Done")

if __name__ == "__main__":
    main()
