"""
FNIRSI Power Supply - Interactive CLI
=====================================
Интерактивное консольное приложение для управления блоком питания FNIRSI
"""

from controller import FnirsiController
import time
import sys
import os


class FnirsiCLI:
    """Интерактивный CLI для FNIRSI"""
    
    def __init__(self, port: str = "COM11"):
        self.psu = FnirsiController()
        self.port = port
        self.running = False
    
    def clear_screen(self):
        """Очистить экран"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Печать заголовка"""
        print("=" * 60)
        print("  FNIRSI Power Supply Controller")
        print("=" * 60)
    
    def print_status(self):
        """Печать текущего состояния"""
        s = self.psu.state
        
        print(f"\n┌{'─' * 28}┬{'─' * 28}┐")
        print(f"│ {'Модель:':<12} {s.model:<14} │ {'Прошивка:':<12} {s.firmware:<14} │")
        print(f"├{'─' * 28}┼{'─' * 28}┤")
        print(f"│ {'Макс V:':<12} {s.max_voltage:>10.1f} V   │ {'Макс A:':<12} {s.max_current:>10.3f} A   │")
        print(f"├{'─' * 28}┼{'─' * 28}┤")
        print(f"│ {'Уставка V:':<12} {s.set_voltage:>10.2f} V   │ {'Уставка A:':<12} {s.set_current:>10.3f} A   │")
        print(f"├{'─' * 28}┴{'─' * 28}┤")
        
        output_str = ">>> ВКЛ <<<" if s.output_enabled else "    ВЫКЛ    "
        print(f"│ {'Выход:':<12} {output_str:^44} │")
        print(f"├{'─' * 58}┤")
        print(f"│ {'Режим:':<12} {s.mode_str:<10} {'Защита:':<12} {s.protection_str:<18} │")
        print(f"├{'─' * 58}┤")
        print(f"│ {'ИЗМЕРЕНИЯ':^56} │")
        print(f"├{'─' * 18}┬{'─' * 19}┬{'─' * 18}┤")
        print(f"│ {'Напряжение':^16} │ {'Ток':^17} │ {'Мощность':^16} │")
        print(f"│ {s.output_voltage:>10.4f} V     │ {s.output_current:>11.5f} A    │ {s.output_power:>10.3f} W    │")
        print(f"├{'─' * 18}┴{'─' * 19}┴{'─' * 18}┤")
        print(f"│ {'Температура:':<14} {s.temperature:>8.1f} °C  ({s.temperature_f:.1f} °F){' ' * 18} │")
        print(f"│ {'Ёмкость:':<14} {s.capacity_ah:>8.3f} Ah  /  {s.capacity_wh:.3f} Wh{' ' * 15} │")
        print(f"└{'─' * 58}┘")
    
    def print_menu(self):
        """Печать меню команд"""
        print("\n┌─ Команды " + "─" * 48 + "┐")
        print("│  v <V>    - Установить напряжение (например: v 5.0)      │")
        print("│  a <A>    - Установить ток (например: a 1.0)             │")
        print("│  on       - Включить выход                               │")
        print("│  off      - Выключить выход                              │")
        print("│  r        - Обновить данные                              │")
        print("│  m        - Мониторинг (5 сек)                           │")
        print("│  q        - Выход                                        │")
        print("└" + "─" * 58 + "┘")
    
    def connect(self) -> bool:
        """Подключение к устройству"""
        print(f"\nПодключение к {self.port}...", end=" ", flush=True)
        if self.psu.connect(self.port):
            print("OK!")
            time.sleep(0.5)
            return True
        else:
            print("ОШИБКА!")
            return False
    
    def monitor(self, duration: float = 5.0):
        """Мониторинг в реальном времени"""
        print(f"\nМониторинг {duration} сек (Ctrl+C для остановки)...")
        print("-" * 60)
        print(f"{'Время':>8}  {'V':>10}  {'A':>10}  {'W':>10}  {'°C':>6}  {'Режим':>6}")
        print("-" * 60)
        
        start = time.time()
        try:
            while time.time() - start < duration:
                s = self.psu.state
                elapsed = time.time() - start
                print(f"{elapsed:>7.1f}s  {s.output_voltage:>10.4f}  {s.output_current:>10.5f}  "
                      f"{s.output_power:>10.3f}  {s.temperature:>6.1f}  {s.mode_str:>6}")
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        print("-" * 60)
    
    def run(self):
        """Главный цикл"""
        self.clear_screen()
        self.print_header()
        
        if not self.connect():
            return
        
        self.running = True
        
        while self.running:
            self.print_status()
            self.print_menu()
            
            try:
                cmd = input("\n> ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                break
            
            if not cmd:
                continue
            
            parts = cmd.split()
            command = parts[0]
            
            if command == 'q':
                break
            
            elif command == 'r':
                self.psu.read_all()
                time.sleep(0.3)
            
            elif command == 'on':
                print("Включение выхода...", end=" ", flush=True)
                if self.psu.output_on():
                    print("OK")
                else:
                    print("ОШИБКА")
                time.sleep(0.5)
            
            elif command == 'off':
                print("Выключение выхода...", end=" ", flush=True)
                if self.psu.output_off():
                    print("OK")
                else:
                    print("ОШИБКА")
                time.sleep(0.5)
            
            elif command == 'v':
                if len(parts) >= 2:
                    try:
                        voltage = float(parts[1])
                        print(f"Установка напряжения {voltage}V...", end=" ", flush=True)
                        if self.psu.set_voltage(voltage):
                            print("OK")
                        else:
                            print("ОШИБКА")
                    except ValueError:
                        print("Неверное значение!")
                else:
                    print("Использование: v <напряжение>")
                time.sleep(0.5)
            
            elif command == 'a':
                if len(parts) >= 2:
                    try:
                        current = float(parts[1])
                        print(f"Установка тока {current}A...", end=" ", flush=True)
                        if self.psu.set_current(current):
                            print("OK")
                        else:
                            print("ОШИБКА")
                    except ValueError:
                        print("Неверное значение!")
                else:
                    print("Использование: a <ток>")
                time.sleep(0.5)
            
            elif command == 'm':
                duration = float(parts[1]) if len(parts) >= 2 else 5.0
                self.monitor(duration)
            
            else:
                print(f"Неизвестная команда: {command}")
                time.sleep(1)
            
            self.clear_screen()
            self.print_header()
        
        print("\nОтключение...")
        self.psu.disconnect()
        print("До свидания!")


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM11"
    cli = FnirsiCLI(port)
    cli.run()


if __name__ == "__main__":
    main()
