"""
Тест отправки команд с отладкой
"""
from controller import FnirsiController, Commands, make_command, float_to_bytes
import time
import struct


def hex_dump(data: bytes) -> str:
    return ' '.join(f'{b:02X}' for b in data)


def test_commands():
    """Проверка формата команд"""
    print("=" * 60)
    print("Проверка формата команд")
    print("=" * 60)
    
    # Команда установки напряжения 5V
    cmd_v5 = Commands.set_voltage(5.0)
    print(f"\nset_voltage(5.0):")
    print(f"  Команда: {hex_dump(cmd_v5)}")
    print(f"  Разбор: Header={cmd_v5[0]:02X} Cmd={cmd_v5[1]:02X} Reg={cmd_v5[2]:02X} Len={cmd_v5[3]}")
    print(f"  Data: {hex_dump(cmd_v5[4:-1])}")
    print(f"  Float value: {struct.unpack('<f', cmd_v5[4:8])[0]}")
    
    # Команда установки напряжения 12V
    cmd_v12 = Commands.set_voltage(12.0)
    print(f"\nset_voltage(12.0):")
    print(f"  Команда: {hex_dump(cmd_v12)}")
    print(f"  Float value: {struct.unpack('<f', cmd_v12[4:8])[0]}")
    
    # Команда установки тока 1A
    cmd_a1 = Commands.set_current(1.0)
    print(f"\nset_current(1.0):")
    print(f"  Команда: {hex_dump(cmd_a1)}")
    print(f"  Float value: {struct.unpack('<f', cmd_a1[4:8])[0]}")
    
    print("\n" + "=" * 60)
    print("Ожидаемый формат:")
    print("  set_voltage(5.0): F1 B1 C1 04 00 00 A0 40 xx")
    print("=" * 60)


def test_live():
    """Живой тест с устройством"""
    print("\n" + "=" * 60)
    print("Живой тест с устройством")
    print("=" * 60)
    
    psu = FnirsiController()
    
    print(f"\nПодключение...", end=" ", flush=True)
    if not psu.connect("COM11"):
        print("ОШИБКА!")
        return
    print("OK")
    
    time.sleep(0.5)
    print(f"\nНачальные значения:")
    print(f"  Уставка V: {psu.state.set_voltage:.2f}V")
    print(f"  Уставка A: {psu.state.set_current:.3f}A")
    print(f"  Выход V:   {psu.state.output_voltage:.4f}V")
    
    # Отправляем команду установки 5V
    cmd = Commands.set_voltage(5.0)
    print(f"\nОтправка: {hex_dump(cmd)}")
    psu._send(cmd)
    time.sleep(1)
    psu.read_all()
    time.sleep(0.5)
    
    print(f"После set_voltage(5.0):")
    print(f"  Уставка V: {psu.state.set_voltage:.2f}V")
    print(f"  Выход V:   {psu.state.output_voltage:.4f}V")
    
    # Отправляем команду установки 12V
    cmd = Commands.set_voltage(12.0)
    print(f"\nОтправка: {hex_dump(cmd)}")
    psu._send(cmd)
    time.sleep(1)
    psu.read_all()
    time.sleep(0.5)
    
    print(f"После set_voltage(12.0):")
    print(f"  Уставка V: {psu.state.set_voltage:.2f}V")
    print(f"  Выход V:   {psu.state.output_voltage:.4f}V")
    
    psu.disconnect()
    print("\nОтключено.")


if __name__ == "__main__":
    test_commands()
    test_live()
