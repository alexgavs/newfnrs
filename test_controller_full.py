"""
Полный тест FnirsiController
"""
import time
import sys
sys.path.insert(0, 'c:/fnirsi/newfnrs')

from controller import FnirsiController

def main():
    print("=== FNIRSI Controller Test ===\n")
    
    psu = FnirsiController()
    
    print("1. Подключение к COM11...")
    if not psu.connect("COM11"):
        print("   ОШИБКА: Не удалось подключиться")
        return
    print("   ОК: Подключено")
    
    time.sleep(0.5)
    psu.read_all()
    
    print(f"\n2. Информация об устройстве:")
    print(f"   Max Voltage: {psu.state.max_voltage:.1f} V")
    print(f"   Max Current: {psu.state.max_current:.1f} A")
    print(f"   Set Voltage: {psu.state.set_voltage:.3f} V")
    print(f"   Set Current: {psu.state.set_current:.3f} A")
    print(f"   Output:      {'ВКЛ' if psu.state.output_enabled else 'ВЫКЛ'}")
    print(f"   Mode:        {'CC' if psu.state.mode == 1 else 'CV'}")
    
    print(f"\n3. Тест выхода:")
    
    # Выключить выход
    print("   Выключение выхода...")
    psu.output_off()
    time.sleep(0.5)
    psu.read_all()
    print(f"   Состояние: {'ВКЛ' if psu.state.output_enabled else 'ВЫКЛ'}")
    
    # Включить выход
    print("   Включение выхода...")
    psu.output_on()
    time.sleep(0.5)
    psu.read_all()
    print(f"   Состояние: {'ВКЛ' if psu.state.output_enabled else 'ВЫКЛ'}")
    
    print(f"\n4. Тест установки напряжения:")
    current_v = psu.state.set_voltage
    print(f"   Текущее: {current_v:.3f} V")
    
    # Установить 5V
    print("   Устанавливаем 5.0V...")
    psu.set_voltage(5.0)
    time.sleep(0.5)
    psu.read_all()
    print(f"   Результат: {psu.state.set_voltage:.3f} V")
    
    # Вернуть обратно
    print(f"   Возвращаем {current_v:.3f}V...")
    psu.set_voltage(current_v)
    time.sleep(0.5)
    psu.read_all()
    print(f"   Результат: {psu.state.set_voltage:.3f} V")
    
    print(f"\n5. Тест установки тока:")
    current_a = psu.state.set_current
    print(f"   Текущий: {current_a:.3f} A")
    
    # Установить 1A
    print("   Устанавливаем 1.0A...")
    psu.set_current(1.0)
    time.sleep(0.5)
    psu.read_all()
    print(f"   Результат: {psu.state.set_current:.3f} A")
    
    # Вернуть обратно
    print(f"   Возвращаем {current_a:.3f}A...")
    psu.set_current(current_a)
    time.sleep(0.5)
    psu.read_all()
    print(f"   Результат: {psu.state.set_current:.3f} A")
    
    print(f"\n6. Показания:")
    print(f"   Вых. напр.: {psu.state.output_voltage:.4f} V")
    print(f"   Вых. ток:   {psu.state.output_current:.5f} A")
    print(f"   Мощность:   {psu.state.output_power:.3f} W")
    print(f"   Температура: {psu.state.temperature:.1f} °C")
    
    psu.disconnect()
    print("\n=== Тест завершён успешно! ===")

if __name__ == "__main__":
    main()
