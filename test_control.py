#!/usr/bin/env python3
"""
Тестирование FNIRSI с самопроверкой каждого шага.
Каждый тест:
1. Установить параметр
2. Считать и проверить
3. Включить выход на 2 сек
4. Замерять ток каждые 100 мс
5. Выключить выход
"""

import time
import sys
from controller import FnirsiController

# Настройки тестов
TEST_DURATION = 2.0  # секунды
MEASURE_INTERVAL = 0.1  # 100 мс

# Тестовые параметры (напряжение, ток)
TESTS = [
    (5.0, 1.0),   # Тест 1: 5V, 1A
    (12.0, 0.5),  # Тест 2: 12V, 0.5A
    (3.3, 2.0),   # Тест 3: 3.3V, 2A
]


def run_test(ctrl: FnirsiController, test_num: int, voltage: float, current: float) -> bool:
    """Выполнить один тест с проверкой."""
    
    print(f"\n{'='*60}")
    print(f"ТЕСТ {test_num}: Напряжение={voltage}V, Ток={current}A")
    print(f"{'='*60}")
    
    # === ШАГ 1: Убедиться что выход выключен ===
    print("\n[1] Выключаю выход...")
    ctrl.output_off()
    time.sleep(0.3)
    
    # === ШАГ 2: Установить напряжение ===
    print(f"\n[2] Устанавливаю напряжение {voltage}V...")
    ctrl.set_voltage(voltage)
    time.sleep(0.3)
    
    # === ШАГ 3: Установить ток ===
    print(f"\n[3] Устанавливаю ток {current}A...")
    ctrl.set_current(current)
    time.sleep(0.3)
    
    # === ШАГ 4: Считать параметры и проверить ===
    print("\n[4] Считываю параметры для проверки...")
    ctrl.read_all()
    time.sleep(0.3)  # ждём ответа
    state = ctrl.state
    
    print(f"    Уставка напряжения: {state.set_voltage:.2f}V (ожидалось {voltage}V)")
    print(f"    Уставка тока: {state.set_current:.2f}A (ожидалось {current}A)")
    
    # Проверка с допуском 0.1
    v_ok = abs(state.set_voltage - voltage) < 0.1
    a_ok = abs(state.set_current - current) < 0.1
    
    if v_ok and a_ok:
        print("    ✓ Параметры установлены верно!")
    else:
        print("    ✗ ОШИБКА: Параметры не совпадают!")
        if not v_ok:
            print(f"      Напряжение: разница {abs(state.set_voltage - voltage):.3f}V")
        if not a_ok:
            print(f"      Ток: разница {abs(state.set_current - current):.3f}A")
        return False
    
    # === ШАГ 5: Включить выход ===
    print(f"\n[5] Включаю выход на {TEST_DURATION} сек...")
    ctrl.output_on()
    time.sleep(0.2)
    
    # === ШАГ 6: Замерять ток каждые 100 мс ===
    print(f"\n[6] Измерение тока каждые {int(MEASURE_INTERVAL*1000)} мс:")
    
    measurements = []
    start_time = time.time()
    measure_count = int(TEST_DURATION / MEASURE_INTERVAL)
    
    for i in range(measure_count):
        elapsed = time.time() - start_time
        
        # Считываем текущие значения из state (обновляется автоматически)
        state = ctrl.state
        actual_v = state.output_voltage
        actual_a = state.output_current
        actual_w = state.output_power
        measurements.append((elapsed, actual_v, actual_a, actual_w))
        print(f"    [{elapsed:.1f}s] V={actual_v:.3f}V, A={actual_a:.3f}A, W={actual_w:.3f}W")
        
        # Ждём до следующего измерения
        next_time = start_time + (i + 1) * MEASURE_INTERVAL
        sleep_time = next_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    # === ШАГ 7: Выключить выход ===
    print(f"\n[7] Выключаю выход...")
    ctrl.output_off()
    time.sleep(0.2)
    
    # === Статистика теста ===
    if measurements:
        avg_v = sum(m[1] for m in measurements) / len(measurements)
        avg_a = sum(m[2] for m in measurements) / len(measurements)
        avg_w = sum(m[3] for m in measurements) / len(measurements)
        print(f"\n    Статистика ({len(measurements)} измерений):")
        print(f"    Среднее: V={avg_v:.3f}V, A={avg_a:.3f}A, W={avg_w:.3f}W")
    
    print(f"\n    ✓ ТЕСТ {test_num} ЗАВЕРШЁН УСПЕШНО")
    return True


def main():
    port = "COM11"
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ FNIRSI С САМОПРОВЕРКОЙ")
    print("=" * 60)
    print(f"Порт: {port}")
    print(f"Длительность теста: {TEST_DURATION} сек")
    print(f"Интервал измерения: {int(MEASURE_INTERVAL*1000)} мс")
    print(f"Количество тестов: {len(TESTS)}")
    
    # Подключение
    ctrl = FnirsiController()
    if not ctrl.connect(port):
        print("ОШИБКА: Не удалось подключиться!")
        return 1
    
    print("\n✓ Подключено к устройству")
    
    # Считать начальное состояние
    ctrl.read_all()
    time.sleep(0.5)  # ждём ответа
    state = ctrl.state
    print(f"\nНачальное состояние:")
    print(f"  Модель: {state.model}")
    print(f"  Версия: {state.firmware}")
    print(f"  Уставка: {state.set_voltage:.2f}V / {state.set_current:.2f}A")
    
    # Выполнить все тесты
    passed = 0
    failed = 0
    
    for i, (voltage, current) in enumerate(TESTS, 1):
        try:
            if run_test(ctrl, i, voltage, current):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ ОШИБКА в тесте {i}: {e}")
            failed += 1
        
        # Пауза между тестами
        if i < len(TESTS):
            print("\n--- Пауза 1 сек перед следующим тестом ---")
            time.sleep(1.0)
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"Всего тестов: {len(TESTS)}")
    print(f"Успешно: {passed}")
    print(f"Ошибок: {failed}")
    
    # Убедиться что выход выключен
    ctrl.output_off()
    ctrl.disconnect()
    print("\n✓ Отключено от устройства")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
