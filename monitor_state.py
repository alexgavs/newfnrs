"""
Мониторинг состояния устройства
Нажми кнопку OUTPUT на устройстве и посмотри какие байты меняются
"""
import serial
import time

PORT = "COM11"
BAUD = 9600

def get_full_state(port):
    """Получить полный payload"""
    port.reset_input_buffer()
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.3)
    data = port.read(300)
    
    start = data.find(b'\xF0\xA1\xFF')
    if start < 0:
        return None
    
    length = data[start + 3]
    payload = data[start + 4 : start + 4 + length]
    return payload

def main():
    print(f"Opening {PORT}...")
    port = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.5)
    
    # Connect
    port.write(bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02]))
    time.sleep(0.3)
    port.read(100)
    
    print("Мониторинг состояния. Нажми OUTPUT на устройстве.")
    print("Ctrl+C для выхода.\n")
    
    prev_payload = None
    
    try:
        while True:
            payload = get_full_state(port)
            if payload and len(payload) >= 115:
                # Показываем ключевые байты
                # 109 - output?, 110 - mode?
                
                if prev_payload and payload != prev_payload:
                    print("\n=== ИЗМЕНЕНИЕ ОБНАРУЖЕНО ===")
                    # Найти изменения
                    for i in range(min(len(payload), len(prev_payload))):
                        if payload[i] != prev_payload[i]:
                            print(f"  Offset {i}: {prev_payload[i]:02X} -> {payload[i]:02X}")
                    print("=" * 30)
                
                # Показать текущее состояние
                print(f"\rOffset 109={payload[109]:02X}, 110={payload[110]:02X}", end="")
                
                prev_payload = payload
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nОстановлено")
    
    port.close()

if __name__ == "__main__":
    main()
