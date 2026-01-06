"""
Тест установки напряжения и тока
"""
from controller import FnirsiController
import time
import sys


def test_set_values(port: str = "COM11"):
    """Тест установки значений"""
    print("=" * 60)
    print("FNIRSI - Тест установки напряжения и тока")
    print("=" * 60)
    
    psu = FnirsiController()
    
    print(f"\n[1] Подключение к {port}...", end=" ", flush=True)
    if not psu.connect(port):
        print("ОШИБКА!")
        return False
    print("OK")
    
    time.sleep(0.5)
    print(f"\n    Текущие значения:")
    print(f"    Уставка V: {psu.state.set_voltage:.2f}V")
    print(f"    Уставка A: {psu.state.set_current:.3f}A")
    print(f"    Выход: {'ВКЛ' if psu.state.output_enabled else 'ВЫКЛ'}")
    
    # Тест установки напряжения
    print(f"\n[2] Установка напряжения 5.0V...", end=" ", flush=True)
    psu.set_voltage(5.0)
    time.sleep(0.5)
    psu.read_all()
    time.sleep(0.5)
    print(f"Уставка: {psu.state.set_voltage:.2f}V")
    
    # Тест установки тока
    print(f"\n[3] Установка тока 1.0A...", end=" ", flush=True)
    psu.set_current(1.0)
    time.sleep(0.5)
    psu.read_all()
    time.sleep(0.5)
    print(f"Уставка: {psu.state.set_current:.3f}A")
    
    # Тест включения выхода
    print(f"\n[4] Включение выхода...", end=" ", flush=True)
    psu.output_on()
    time.sleep(1)
    print(f"Выход: {'ВКЛ' if psu.state.output_enabled else 'ВЫКЛ'}")
    
    # Мониторинг 3 секунды
    print(f"\n[5] Мониторинг 3 секунды:")
    print(f"    {'V':>10}  {'A':>10}  {'W':>10}")
    for i in range(6):
        print(f"    {psu.state.output_voltage:>10.4f}  {psu.state.output_current:>10.5f}  {psu.state.output_power:>10.3f}")
        time.sleep(0.5)
    
    # Изменение напряжения
    print(f"\n[6] Установка напряжения 12.0V...", end=" ", flush=True)
    psu.set_voltage(12.0)
    time.sleep(1)
    psu.read_all()
    time.sleep(0.5)
    print(f"Уставка: {psu.state.set_voltage:.2f}V")
    
    # Мониторинг
    print(f"\n[7] Мониторинг 3 секунды:")
    print(f"    {'V':>10}  {'A':>10}  {'W':>10}")
    for i in range(6):
        print(f"    {psu.state.output_voltage:>10.4f}  {psu.state.output_current:>10.5f}  {psu.state.output_power:>10.3f}")
        time.sleep(0.5)
    
    # Выключение выхода
    print(f"\n[8] Выключение выхода...", end=" ", flush=True)
    psu.output_off()
    time.sleep(0.5)
    print(f"Выход: {'ВКЛ' if psu.state.output_enabled else 'ВЫКЛ'}")
    
    # Отключение
    print(f"\n[9] Отключение...")
    psu.disconnect()
    
    print("\n" + "=" * 60)
    print("Тест завершён!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "COM11"
    test_set_values(port)
