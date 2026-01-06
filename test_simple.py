"""
Тест установки напряжения/тока на FNIRSI - записывает в файл
"""
import serial
import time
import struct

PORT = "COM11"
BAUD = 9600
LOG_FILE = "c:\\fnirsi\\newfnrs\\test_result.txt"

def float_to_bytes(value: float) -> bytes:
    return struct.pack('<f', value)

def make_command(cmd_type: int, register: int, data: bytes) -> bytes:
    length = len(data)
    checksum = (register + length + sum(data)) & 0xFF
    return bytes([0xF1, cmd_type, register, length]) + data + bytes([checksum])

def hex_dump(data: bytes) -> str:
    return ' '.join(f'{b:02X}' for b in data)

# Открываем лог файл
with open(LOG_FILE, 'w') as log:
    def write(msg):
        log.write(msg + '\n')
        log.flush()
        print(msg)
    
    write(f"=== FNIRSI Set Value Test ===")
    write(f"Port: {PORT}, Baud: {BAUD}")

    # Команды
    CMD_CONNECT = make_command(0xC1, 0x00, b'\x01')
    CMD_SET_V_5 = make_command(0xB0, 0xC0, float_to_bytes(5.0))
    CMD_SET_V_12 = make_command(0xB0, 0xC0, float_to_bytes(12.0))
    CMD_SET_A_1 = make_command(0xB0, 0xDE, float_to_bytes(1.0))

    write(f"\nCommands:")
    write(f"  CONNECT:    {hex_dump(CMD_CONNECT)}")
    write(f"  SET_V_5:    {hex_dump(CMD_SET_V_5)}")
    write(f"  SET_V_12:   {hex_dump(CMD_SET_V_12)}")
    write(f"  SET_A_1:    {hex_dump(CMD_SET_A_1)}")

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1, write_timeout=None)
        ser.rts = True
        ser.dtr = True
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)
        write(f"\nPort opened OK")
        
        # Подключение
        write("\n1. Sending CONNECT...")
        ser.write(CMD_CONNECT)
        ser.flush()
        time.sleep(0.5)
        resp = ser.read(ser.in_waiting) if ser.in_waiting else b''
        write(f"   Response: {len(resp)} bytes")
        
        # Установка напряжения 5V
        write("\n2. Setting voltage to 5.0V...")
        ser.write(CMD_SET_V_5)
        ser.flush()
        time.sleep(0.3)
        resp = ser.read(ser.in_waiting) if ser.in_waiting else b''
        write(f"   Response: {hex_dump(resp[:50]) if resp else 'none'}")
        
        # Установка тока 1A
        write("\n3. Setting current to 1.0A...")
        ser.write(CMD_SET_A_1)
        ser.flush()
        time.sleep(0.3)
        resp = ser.read(ser.in_waiting) if ser.in_waiting else b''
        write(f"   Response: {hex_dump(resp[:50]) if resp else 'none'}")
        
        # Читаем данные
        write("\n4. Reading current values...")
        found = False
        start = time.time()
        while time.time() - start < 3 and not found:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                write(f"   Raw: {hex_dump(data[:60])}")
                for i in range(len(data) - 16):
                    if data[i] == 0xF0 and data[i+1] == 0xA1 and data[i+2] == 0xC3:
                        payload = data[i+4:i+16]
                        set_v = struct.unpack('<f', payload[0:4])[0]
                        out_v = struct.unpack('<f', payload[4:8])[0]
                        out_a = struct.unpack('<f', payload[8:12])[0]
                        write(f"   SetV={set_v:.2f}V  OutV={out_v:.4f}V  OutA={out_a:.5f}A")
                        found = True
                        break
            time.sleep(0.1)
        
        if not found:
            write("   No data packets found")
        
        ser.close()
        write("\nDone!")
        
    except Exception as e:
        write(f"Error: {e}")
        import traceback
        write(traceback.format_exc())
