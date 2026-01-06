"""
Тест установки напряжения/тока на FNIRSI
"""
import serial
import time
import struct
import sys

PORT = "COM11"
BAUD = 9600

def log(msg):
    print(msg, flush=True)

def float_to_bytes(value: float) -> bytes:
    return struct.pack('<f', value)

def make_command(cmd_type: int, register: int, data: bytes) -> bytes:
    length = len(data)
    checksum = (register + length + sum(data)) & 0xFF
    return bytes([0xF1, cmd_type, register, length]) + data + bytes([checksum])

def hex_dump(data: bytes) -> str:
    return ' '.join(f'{b:02X}' for b in data)

log(f"=== FNIRSI Set Value Test ===")
log(f"Port: {PORT}, Baud: {BAUD}")

# Команды
CMD_CONNECT = make_command(0xC1, 0x00, b'\x01')
CMD_DISCONNECT = make_command(0xC1, 0x00, b'\x00')
CMD_SET_V_5 = make_command(0xB0, 0xC0, float_to_bytes(5.0))
CMD_SET_V_12 = make_command(0xB0, 0xC0, float_to_bytes(12.0))
CMD_SET_A_1 = make_command(0xB0, 0xDE, float_to_bytes(1.0))
CMD_OUTPUT_ON = make_command(0xB1, 0xDB, b'\x01')
CMD_OUTPUT_OFF = make_command(0xB1, 0xDB, b'\x00')
CMD_READ_ALL = make_command(0xA1, 0xFF, b'\x00')

log(f"\nCommands:")
log(f"  CONNECT:    {hex_dump(CMD_CONNECT)}")
log(f"  SET_V_5:    {hex_dump(CMD_SET_V_5)}")
log(f"  SET_V_12:   {hex_dump(CMD_SET_V_12)}")
log(f"  SET_A_1:    {hex_dump(CMD_SET_A_1)}")
log(f"  OUTPUT_ON:  {hex_dump(CMD_OUTPUT_ON)}")
log(f"  OUTPUT_OFF: {hex_dump(CMD_OUTPUT_OFF)}")

try:
    ser = serial.Serial(PORT, BAUD, timeout=1, write_timeout=None)
    ser.rts = True
    ser.dtr = True
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.2)
    log(f"\nPort opened")
    
    # Подключение
    log("\n1. Sending CONNECT...")
    ser.write(CMD_CONNECT)
    ser.flush()
    time.sleep(0.5)
    resp = ser.read(ser.in_waiting) if ser.in_waiting else b''
    log(f"   Response: {len(resp)} bytes")
    
    # Установка напряжения 5V
    log("\n2. Setting voltage to 5.0V...")
    ser.write(CMD_SET_V_5)
    time.sleep(0.3)
    resp = ser.read(ser.in_waiting) if ser.in_waiting else b''
    log(f"   Response: {hex_dump(resp[:50]) if resp else 'none'}...")
    
    # Установка тока 1A
    log("\n3. Setting current to 1.0A...")
    ser.write(CMD_SET_A_1)
    time.sleep(0.3)
    resp = ser.read(ser.in_waiting) if ser.in_waiting else b''
    log(f"   Response: {hex_dump(resp[:50]) if resp else 'none'}...")
    
    # Читаем данные
    log("\n4. Reading current values for 2 seconds...")
    start = time.time()
    while time.time() - start < 2:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            # Ищем пакет 0xC3 (показания)
            for i in range(len(data) - 16):
                if data[i] == 0xF0 and data[i+1] == 0xA1 and data[i+2] == 0xC3:
                    payload = data[i+4:i+16]
                    set_v = struct.unpack('<f', payload[0:4])[0]
                    out_v = struct.unpack('<f', payload[4:8])[0]
                    out_a = struct.unpack('<f', payload[8:12])[0]
                    log(f"   SetV={set_v:.2f}V  OutV={out_v:.4f}V  OutA={out_a:.5f}A")
                    break
        time.sleep(0.1)
    
    # Теперь попробуем 12V
    log("\n5. Setting voltage to 12.0V...")
    ser.write(CMD_SET_V_12)
    time.sleep(1)
    
    log("   Reading new values...")
    start = time.time()
    while time.time() - start < 2:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            for i in range(len(data) - 16):
                if data[i] == 0xF0 and data[i+1] == 0xA1 and data[i+2] == 0xC3:
                    payload = data[i+4:i+16]
                    set_v = struct.unpack('<f', payload[0:4])[0]
                    out_v = struct.unpack('<f', payload[4:8])[0]
                    out_a = struct.unpack('<f', payload[8:12])[0]
                    log(f"   SetV={set_v:.2f}V  OutV={out_v:.4f}V  OutA={out_a:.5f}A")
                    break
        time.sleep(0.1)
    
    ser.close()
    log("\nDone!")
    
except Exception as e:
    log(f"Error: {e}")
