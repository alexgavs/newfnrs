"""
Поиск регистра яркости дисплея
Пробуем отправить команду записи на разные регистры
"""
import serial
import time

PORT = "COM11"
BAUD = 9600

def make_cmd(reg, value):
    """Создать команду записи байта"""
    cs = (reg + 1 + value) & 0xFF
    return bytes([0xF1, 0xB1, reg, 0x01, value, cs])

def main():
    print(f"Opening {PORT}...")
    port = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.5)
    
    # Connect
    port.write(bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02]))
    time.sleep(0.3)
    port.read(100)
    
    print("Попробуем разные регистры для яркости (0x01-0x0F)...")
    print("Следи за дисплеем устройства!\n")
    
    # Попробуем регистры 0x01-0x0F
    for reg in range(0x01, 0x10):
        print(f"Регистр 0x{reg:02X}, значение 50...")
        cmd = make_cmd(reg, 50)
        port.write(cmd)
        time.sleep(0.5)
        resp = port.read(20)
        if resp:
            print(f"  Ответ: {resp.hex(' ').upper()}")
        
        input("  Нажми Enter для следующего...")
    
    port.close()
    print("Done")

if __name__ == "__main__":
    main()
