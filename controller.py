"""
FNIRSI Power Supply Controller
===============================
Класс управления блоком питания FNIRSI.
"""

import serial
import struct
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Callable, List
from enum import IntEnum


# =============================================================================
# Protocol Constants
# =============================================================================

class CmdType(IntEnum):
    """Типы команд"""
    READ = 0xA1       # Чтение регистра
    WRITE_FLOAT = 0xB0  # Запись float значения
    WRITE_BYTE = 0xB1   # Запись байта
    CONNECT = 0xC1      # Подключение/отключение
    CONFIG = 0xC0       # Конфигурация


class Register(IntEnum):
    """Регистры устройства"""
    # Настройки
    BAUD_RATE = 0x00
    
    # Установка значений
    SET_VOLTAGE = 0xC1  # Установить напряжение (через 0xB1)
    SET_CURRENT = 0xC2  # Установить ток (через 0xB1)
    
    # Чтение настроек
    READ_VOLTAGE = 0xC0  # Чтение уставки напряжения
    READ_CURRENT = 0xDE  # Чтение уставки тока
    
    # Показания в реальном времени
    LIVE_VALUES = 0xC3   # V, A, W
    TEMPERATURE = 0xC4   # Температура
    
    # Ёмкость
    CAPACITY_AH = 0xD9
    CAPACITY_WH = 0xDA
    
    # Управление
    OUTPUT_STATE = 0xDB  # Состояние выхода
    PROTECTION = 0xDC    # Статус защиты
    MODE = 0xDD          # Режим CV/CC
    
    # Информация об устройстве
    MODEL = 0xDE
    SERIAL = 0xDF
    FIRMWARE = 0xE0
    DEVICE_ID = 0xE1
    
    # Лимиты
    MAX_VOLTAGE = 0xE2
    MAX_CURRENT = 0xE3
    
    # Все параметры
    ALL = 0xFF


class Protection(IntEnum):
    """Статусы защиты"""
    OK = 0
    OVP = 1   # Over Voltage Protection
    OCP = 2   # Over Current Protection
    OPP = 3   # Over Power Protection
    OTP = 4   # Over Temperature Protection
    SCP = 5   # Short Circuit Protection


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class PowerSupplyState:
    """Состояние блока питания"""
    # Настройки
    set_voltage: float = 0.0    # Data2 - установленное напряжение
    set_current: float = 0.0    # Data3 - установленный ток
    
    # Измерения
    input_voltage: float = 0.0  # Data1 - входное напряжение
    output_voltage: float = 0.0 # Data4 - выходное напряжение
    output_current: float = 0.0 # Data5 - выходной ток
    output_power: float = 0.0   # Data6 - выходная мощность
    temperature: float = 0.0    # Data7 - температура °C
    
    # Лимиты
    max_voltage: float = 24.0   # Data37 - макс. напряжение
    max_current: float = 5.0    # Data38 - макс. ток
    
    # Статус
    output_enabled: bool = False  # Data30
    protection: int = 0           # Data31
    mode: int = 0                 # Data32 (0=CV, 1=CC)
    
    # Ёмкость
    capacity_ah: float = 0.0    # Data28
    capacity_wh: float = 0.0    # Data29
    
    # Информация
    model: str = ""             # Data33
    firmware: str = ""          # Data35
    
    # Пресеты (6 пар V/A)
    presets: List[tuple] = field(default_factory=lambda: [(0.0, 0.0)] * 6)
    
    # Счётчик пакетов
    packet_count: int = 0
    
    @property
    def mode_str(self) -> str:
        return "CC" if self.mode == 1 else "CV"
    
    @property
    def protection_str(self) -> str:
        names = {0: "OK", 1: "OVP", 2: "OCP", 3: "OPP", 4: "OTP", 5: "SCP"}
        return names.get(self.protection, f"ERR({self.protection})")
    
    @property
    def temperature_f(self) -> float:
        return self.temperature * 9 / 5 + 32


# =============================================================================
# Protocol Functions
# =============================================================================

def make_command(cmd_type: int, register: int, data: bytes) -> bytes:
    """
    Создать пакет команды
    
    Формат: [0xF1] [CmdType] [Register] [Length] [Data...] [Checksum]
    Checksum = (Register + Length + sum(Data)) & 0xFF
    """
    length = len(data)
    checksum = (register + length + sum(data)) & 0xFF
    return bytes([0xF1, cmd_type, register, length]) + data + bytes([checksum])


def float_to_bytes(value: float) -> bytes:
    """Преобразовать float в 4 байта (IEEE 754 little-endian)"""
    return struct.pack('<f', value)


def bytes_to_float(data: bytes, offset: int = 0) -> float:
    """Преобразовать 4 байта в float"""
    if len(data) >= offset + 4:
        return struct.unpack('<f', data[offset:offset + 4])[0]
    return 0.0


def hex_dump(data: bytes) -> str:
    """Форматировать байты как hex строку"""
    return ' '.join(f'{b:02X}' for b in data)


# =============================================================================
# Predefined Commands
# =============================================================================

class Commands:
    """Предопределённые команды"""
    
    # CMD_1: Подключение
    CONNECT = make_command(CmdType.CONNECT, 0x00, b'\x01')
    
    # CMD_2: Отключение
    DISCONNECT = make_command(CmdType.CONNECT, 0x00, b'\x00')
    
    # CMD_3: Читать все параметры
    READ_ALL = make_command(CmdType.READ, Register.ALL, b'\x00')
    
    # CMD_4: Читать уставку напряжения
    READ_VOLTAGE = make_command(CmdType.READ, Register.READ_VOLTAGE, b'\x00')
    
    # CMD_5: Читать уставку тока
    READ_CURRENT = make_command(CmdType.READ, Register.READ_CURRENT, b'\x00')
    
    # CMD_6: Читать модель
    READ_MODEL = make_command(CmdType.READ, Register.FIRMWARE, b'\x00')
    
    # CMD_7: Читать ID устройства (для проверки связи)
    READ_DEVICE_ID = make_command(CmdType.READ, Register.DEVICE_ID, b'\x00')
    
    # CMD_8: Выход ВЫКЛ
    OUTPUT_OFF = make_command(CmdType.WRITE_BYTE, Register.OUTPUT_STATE, b'\x00')
    
    # CMD_9: Выход ВКЛ
    OUTPUT_ON = make_command(CmdType.WRITE_BYTE, Register.OUTPUT_STATE, b'\x01')
    
    @staticmethod
    def set_voltage(voltage: float) -> bytes:
        """
        Установить напряжение
        Использует регистр 0xC1 и cmd_type 0xB1
        """
        return make_command(CmdType.WRITE_BYTE, Register.SET_VOLTAGE, float_to_bytes(voltage))
    
    @staticmethod
    def set_current(current: float) -> bytes:
        """
        Установить ток
        Использует регистр 0xC2 и cmd_type 0xB1
        """
        return make_command(CmdType.WRITE_BYTE, Register.SET_CURRENT, float_to_bytes(current))
    
    @staticmethod
    def set_baud_rate(index: int) -> bytes:
        """Установить скорость порта (1=9600, 2=19200...)"""
        return make_command(CmdType.WRITE_FLOAT, Register.BAUD_RATE, bytes([index]))


# =============================================================================
# Response Parser
# =============================================================================

class ResponseParser:
    """Парсер ответов устройства"""
    
    @staticmethod
    def parse(data: bytes, state: PowerSupplyState) -> bool:
        """Разбор пакета ответа"""
        if len(data) < 5 or data[0] != 0xF0:
            return False
        
        register = data[2]
        length = data[3]
        
        if len(data) < 5 + length:
            return False
        
        payload = data[4:4 + length]
        checksum = data[4 + length]
        
        # Проверка контрольной суммы
        calc_cs = (register + length + sum(payload)) & 0xFF
        if calc_cs != checksum:
            return False
        
        # Разбор по регистру
        if register == 0xC0:  # 192 - входное напряжение
            state.input_voltage = bytes_to_float(payload, 0)
            
        elif register == 0xC3:  # 195 - V, A, W
            if len(payload) >= 12:
                state.output_voltage = bytes_to_float(payload, 0)
                state.output_current = bytes_to_float(payload, 4)
                state.output_power = bytes_to_float(payload, 8)
                
        elif register == 0xC4:  # 196 - температура
            state.temperature = bytes_to_float(payload, 0)
            
        elif register == 0xD9:  # 217 - ёмкость Ah
            state.capacity_ah = bytes_to_float(payload, 0)
            
        elif register == 0xDA:  # 218 - ёмкость Wh
            state.capacity_wh = bytes_to_float(payload, 0)
            
        elif register == 0xDB:  # 219 - состояние выхода
            # 0 = ON, 1 = OFF (инвертировано)
            state.output_enabled = (payload[0] == 0)
            
        elif register == 0xDC:  # 220 - статус защиты
            state.protection = payload[0]
            
        elif register == 0xDD:  # 221 - режим CV/CC
            state.mode = payload[0]
            
        elif register == 0xDE:  # 222 - модель
            state.model = payload.decode('ascii', errors='ignore').rstrip('\x00')
            
        elif register == 0xE0:  # 224 - прошивка
            state.firmware = payload.decode('ascii', errors='ignore').rstrip('\x00')
            
        elif register == 0xE2:  # 226 - макс. напряжение
            state.max_voltage = bytes_to_float(payload, 0)
            
        elif register == 0xE3:  # 227 - макс. ток
            state.max_current = bytes_to_float(payload, 0)
            
        elif register == 0xFF:  # 255 - все параметры (из setAllData())
            ResponseParser._parse_all(payload, state)
        
        state.packet_count += 1
        return True
    
    @staticmethod
    def _parse_all(payload: bytes, state: PowerSupplyState):
        """Разбор пакета 0xFF (все параметры)"""
        if len(payload) < 119:
            return
        
        # Основные данные
        state.input_voltage = bytes_to_float(payload, 0)
        state.set_voltage = bytes_to_float(payload, 4)
        state.set_current = bytes_to_float(payload, 8)
        state.output_voltage = bytes_to_float(payload, 12)
        state.output_current = bytes_to_float(payload, 16)
        state.output_power = bytes_to_float(payload, 20)
        state.temperature = bytes_to_float(payload, 24)
        
        # Пресеты (6 пар по 8 байт, начиная с offset 28)
        presets = []
        for i in range(6):
            v = bytes_to_float(payload, 28 + i * 8)
            a = bytes_to_float(payload, 32 + i * 8)
            presets.append((v, a))
        state.presets = presets
        
        # Статусы
        state.capacity_ah = bytes_to_float(payload, 99)
        state.capacity_wh = bytes_to_float(payload, 103)
        state.output_enabled = (payload[107] == 0)
        state.protection = payload[108]
        state.mode = payload[109]
        
        # Лимиты
        state.max_voltage = bytes_to_float(payload, 111)
        state.max_current = bytes_to_float(payload, 115)


# =============================================================================
# FnirsiController - Главный класс управления
# =============================================================================

class FnirsiController:
    """
    Контроллер блока питания FNIRSI
    
    Использование:
        psu = FnirsiController()
        if psu.connect("COM11"):
            psu.set_voltage(5.0)
            psu.set_current(1.0)
            psu.output_on()
            print(f"V = {psu.state.output_voltage}V")
            psu.disconnect()
    """
    
    BAUD_RATES = [9600, 19200, 38400, 57600, 115200]
    
    def __init__(self):
        self._port: Optional[serial.Serial] = None
        self._state = PowerSupplyState()
        self._buffer = bytearray()
        self._verified = False
        
        # Потоки
        self._read_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Callbacks
        self._on_data: Optional[Callable[[PowerSupplyState], None]] = None
        self._on_connect: Optional[Callable[[bool], None]] = None
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def is_connected(self) -> bool:
        """Подключено ли устройство (из Serial.IsOpen)"""
        return self._port is not None and self._port.is_open and self._verified
    
    @property
    def state(self) -> PowerSupplyState:
        """Текущее состояние устройства"""
        return self._state
    
    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------
    
    def on_data_update(self, callback: Callable[[PowerSupplyState], None]):
        """Установить callback для обновления данных"""
        self._on_data = callback
    
    def on_connection_change(self, callback: Callable[[bool], None]):
        """Установить callback для изменения состояния подключения"""
        self._on_connect = callback
    
    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------
    
    def connect(self, port: str, baud: int = 9600, timeout: float = 2.0) -> bool:
        """
        Подключиться к устройству
        """
        self.disconnect()
        
        try:
            self._port = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=0.5,
                write_timeout=None
            )
            self._port.rts = True
            self._port.dtr = True
            time.sleep(0.1)
            self._port.reset_input_buffer()
            self._port.reset_output_buffer()
            self._buffer.clear()
            
            # Запуск потока чтения
            self._stop_event.clear()
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            
            # Отправить CMD_1 (CONNECT)
            self._send(Commands.CONNECT)
            time.sleep(0.3)
            
            # Ожидание ответа (проверка CMD_7 как в оригинале)
            start = time.time()
            while time.time() - start < timeout:
                if self._state.packet_count > 0:
                    self._verified = True
                    break
                # Отправить CMD_7 для проверки связи
                self._send(Commands.READ_DEVICE_ID)
                time.sleep(0.5)
            
            if self._verified:
                # Инициализация (из Serial.commandInit())
                self._send(Commands.READ_CURRENT)
                self._send(Commands.READ_MODEL)
                self._send(Commands.READ_ALL)
                time.sleep(0.3)
                
                if self._on_connect:
                    self._on_connect(True)
                return True
            else:
                self.disconnect()
                return False
                
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """
        Отключиться от устройства
        """
        self._stop_event.set()
        self._verified = False
        
        if self._port and self._port.is_open:
            try:
                self._port.write(Commands.DISCONNECT)
            except:
                pass
            time.sleep(0.1)
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1)
        
        if self._port:
            try:
                self._port.close()
            except:
                pass
            self._port = None
        
        self._state = PowerSupplyState()
        
        if self._on_connect:
            self._on_connect(False)
    
    # -------------------------------------------------------------------------
    # Control Commands
    # -------------------------------------------------------------------------
    
    def set_voltage(self, voltage: float) -> bool:
        """
        Установить напряжение
        """
        voltage = max(0.0, min(voltage, self._state.max_voltage))
        cmd = Commands.set_voltage(voltage)
        return self._send(cmd)
    
    def set_current(self, current: float) -> bool:
        """
        Установить ток
        """
        current = max(0.0, min(current, self._state.max_current))
        cmd = Commands.set_current(current)
        return self._send(cmd)
    
    def output_on(self) -> bool:
        """
        Включить выход
        """
        return self._send(Commands.OUTPUT_ON)
    
    def output_off(self) -> bool:
        """
        Выключить выход
        """
        return self._send(Commands.OUTPUT_OFF)
    
    def read_all(self) -> bool:
        """Запросить все параметры"""
        return self._send(Commands.READ_ALL)
    
    # -------------------------------------------------------------------------
    # Internal Methods
    # -------------------------------------------------------------------------
    
    def _send(self, command: bytes) -> bool:
        """Отправить команду"""
        if not self._port or not self._port.is_open:
            return False
        try:
            with self._lock:
                self._port.write(command)
                self._port.flush()
            return True
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return False
    
    def _read_loop(self):
        """Поток чтения данных"""
        while not self._stop_event.is_set():
            try:
                if self._port and self._port.is_open and self._port.in_waiting > 0:
                    with self._lock:
                        data = self._port.read(self._port.in_waiting)
                    
                    self._buffer.extend(data)
                    self._process_buffer()
                
                time.sleep(0.01)
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"Ошибка чтения: {e}")
                time.sleep(0.1)
    
    def _process_buffer(self):
        """Обработка буфера данных"""
        while len(self._buffer) >= 5:
            # Поиск заголовка ответа
            if self._buffer[0] != 0xF0:
                self._buffer.pop(0)
                continue
            
            if len(self._buffer) < 4:
                break
            
            length = self._buffer[3]
            packet_len = 5 + length
            
            if len(self._buffer) < packet_len:
                break
            
            packet = bytes(self._buffer[:packet_len])
            self._buffer = self._buffer[packet_len:]
            
            if ResponseParser.parse(packet, self._state):
                if self._on_data:
                    try:
                        self._on_data(self._state)
                    except:
                        pass


# =============================================================================
# Main (тестирование)
# =============================================================================

if __name__ == "__main__":
    import sys
    
    port = sys.argv[1] if len(sys.argv) > 1 else "COM11"
    
    print("=" * 60)
    print("FNIRSI Power Supply Controller")
    print("=" * 60)
    
    psu = FnirsiController()
    
    print(f"\nПодключение к {port}...")
    if psu.connect(port):
        print("Подключено!")
        
        # Ждём данных
        time.sleep(1)
        
        print(f"\n--- Состояние устройства ---")
        print(f"Модель:      {psu.state.model}")
        print(f"Прошивка:    {psu.state.firmware}")
        print(f"Макс V:      {psu.state.max_voltage}V")
        print(f"Макс A:      {psu.state.max_current}A")
        print(f"Уставка V:   {psu.state.set_voltage}V")
        print(f"Уставка A:   {psu.state.set_current}A")
        print(f"Выход:       {'ВКЛ' if psu.state.output_enabled else 'ВЫКЛ'}")
        print(f"Режим:       {psu.state.mode_str}")
        print(f"Защита:      {psu.state.protection_str}")
        print(f"\n--- Измерения ---")
        print(f"Напряжение:  {psu.state.output_voltage:.4f}V")
        print(f"Ток:         {psu.state.output_current:.5f}A")
        print(f"Мощность:    {psu.state.output_power:.3f}W")
        print(f"Температура: {psu.state.temperature:.1f}°C")
        
        psu.disconnect()
        print("\nОтключено.")
    else:
        print("Ошибка подключения!")
