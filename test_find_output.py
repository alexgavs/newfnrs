"""
Поиск правильной команды для управления выходом
"""
import serial
import time

PORT = "COM11"
BAUD = 9600

def get_state(port, offset):
    """Получить байт по смещению"""
    port.reset_input_buffer()
    port.write(bytes([0xF1, 0xA1, 0xFF, 0x01, 0x00, 0x00]))
    time.sleep(0.5)
    data = port.read(300)
    
    start = data.find(b'\xF0\xA1\xFF')
    if start < 0:
        return None
    
    length = data[start + 3]
    payload = data[start + 4 : start + 4 + length]
    
    if len(payload) > offset:
        return payload[offset]
    return None

def try_command(port, cmd_type, register, value, desc):
    """Попробовать команду"""
    length = 1
    checksum = (register + length + value) & 0xFF
    cmd = bytes([0xF1, cmd_type, register, length, value, checksum])
    
    print(f"\n{desc}")
    print(f"  TX: {cmd.hex(' ').upper()}")
    port.write(cmd)
    time.sleep(0.3)
    resp = port.read(50)
    if resp:
        print(f"  RX: {resp[:20].hex(' ').upper()}")
    
    # Check state
    out = get_state(port, 109)
    print(f"  Offset 109: {out}")
    return out

def main():
    print(f"Opening {PORT}...")
    port = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.5)
    
    # Connect
    port.write(bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02]))
    time.sleep(0.3)
    port.read(100)
    
    out = get_state(port, 109)
    print(f"Initial offset 109: {out}")
    
    # Пробуем разные регистры для выключения
    
    # 0xDB с 0xB1 (текущий вариант)
    try_command(port, 0xB1, 0xDB, 0x00, "CMD: 0xB1 0xDB 0x00 (current)")
    time.sleep(1)
    
    # 0xDB с 0xB0 (float write)
    try_command(port, 0xB0, 0xDB, 0x00, "CMD: 0xB0 0xDB 0x00")
    time.sleep(1)
    
    # Другой регистр - может быть 0x0A или что-то подобное
    # Пробуем включить обратно
    try_command(port, 0xB1, 0xDB, 0x01, "CMD: 0xB1 0xDB 0x01 (ON)")
    
    port.close()
    print("\nDone")

if __name__ == "__main__":
    main()
