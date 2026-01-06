"""
FNIRSI Power Supply Protocol Module - Fixed Version
Исправленная реализация протокола связи с источником питания FNIRSI

Формат пакета:
[0xF1] [CmdType] [Register] [Length] [Data...] [Checksum]
Ответ:
[0xF0] [CmdType] [Register] [Length] [Data...] [Checksum]

Данные передаются как IEEE 754 float (little-endian)
"""

from dataclasses import dataclass, field
from typing import List
import struct


def float_to_bytes(value: float) -> bytes:
    """Преобразовать float в 4 байта (little-endian IEEE 754)"""
    return struct.pack('<f', value)


def bytes_to_float(data: bytes) -> float:
    """Преобразовать 4 байта в float (little-endian IEEE 754)"""
    if len(data) >= 4:
        return struct.unpack('<f', data[:4])[0]
    return 0.0


@dataclass
class Command:
    """Класс для формирования команды"""
    header: int = 0xF1
    cmd_type: int = 0xA1
    register: int = 0x00
    data: bytes = field(default_factory=lambda: b'\x00')
    
    @property
    def length(self) -> int:
        return len(self.data)
    
    @property
    def checksum(self) -> int:
        cs = self.register + self.length
        for b in self.data:
            cs += b
        return cs & 0xFF
    
    @property
    def packet(self) -> bytes:
        return bytes([
            self.header,
            self.cmd_type,
            self.register,
            self.length,
            *self.data,
            self.checksum
        ])
    
    def __repr__(self) -> str:
        return ' '.join(f'{b:02X}' for b in self.packet)


class Commands:
    """Предопределённые команды"""
    
    # Подключение/отключение  
    CONNECT = Command(0xF1, 0xC1, 0x00, b'\x01')
    DISCONNECT = Command(0xF1, 0xC1, 0x00, b'\x00')
    
    # Чтение параметров
    READ_ALL = Command(0xF1, 0xA1, 0xFF, b'\x00')
    
    # Управление выходом
    OUTPUT_ON = Command(0xF1, 0xB1, 0xDB, b'\x01')
    OUTPUT_OFF = Command(0xF1, 0xB1, 0xDB, b'\x00')
    
    @staticmethod
    def set_voltage(voltage: float) -> Command:
        """Установить напряжение - передаётся как float"""
        data = float_to_bytes(voltage)
        return Command(0xF1, 0xB0, 0xC0, data)
    
    @staticmethod
    def set_current(current: float) -> Command:
        """Установить ток - передаётся как float"""
        data = float_to_bytes(current)
        return Command(0xF1, 0xB0, 0xDE, data)


@dataclass
class DeviceData:
    """Данные устройства"""
    # Текущие показания
    input_voltage: float = 0.0
    output_voltage: float = 0.0
    output_current: float = 0.0
    output_power: float = 0.0
    temperature: float = 0.0
    
    # Установленные значения
    set_voltage: float = 0.0
    set_current: float = 0.0
    
    # Лимиты
    max_voltage: float = 48.0
    max_current: float = 10.0
    
    # Статус
    output_enabled: bool = False
    protection_status: int = 0
    mode: int = 0  # 0=CV, 1=CC
    
    # Счётчик пакетов
    packet_count: int = 0
    
    @property
    def mode_string(self) -> str:
        return "CC" if self.mode == 1 else "CV"


class ResponseParser:
    """Парсер ответов от устройства"""
    
    @staticmethod
    def parse(data: bytes, device: DeviceData) -> bool:
        """Разбор входящих данных"""
        if len(data) < 5 or data[0] != 0xF0:
            return False
        
        register = data[2]
        length = data[3]
        
        if len(data) < 5 + length:
            return False
        
        payload = data[4:4 + length]
        checksum = data[4 + length]
        
        # Проверка контрольной суммы (без cmd_type)
        calc_cs = (register + length + sum(payload)) & 0xFF
        if calc_cs != checksum:
            return False
        
        # Разбор данных по регистру
        if register == 0xC3 and len(payload) >= 12:
            # Регистр 0xC3: set_V (4), measured_V (4), measured_A (4)
            device.set_voltage = bytes_to_float(payload[0:4])
            # Это мгновенные измерения, которые могут быть шумными
            # Используем их только если выход включен
            measured_v = bytes_to_float(payload[4:8])
            measured_a = bytes_to_float(payload[8:12])
            # Обновляем только если значения разумные
            if measured_v > 0.01 or device.output_enabled:
                device.output_voltage = measured_v
                device.output_current = measured_a
            
        elif register == 0xC4 and len(payload) >= 4:
            # Регистр 0xC4: мощность
            device.output_power = bytes_to_float(payload[0:4])
            
        elif register == 0xFF and len(payload) >= 20:
            # Регистр 0xFF: все параметры
            device.max_voltage = bytes_to_float(payload[0:4])
            device.set_voltage = bytes_to_float(payload[4:8])
            device.set_current = bytes_to_float(payload[8:12])
            # output_voltage и output_current из 0xFF могут быть устаревшими
            # Лучше использовать данные из 0xC3
            
            # Статус выхода примерно в offset 113
            if len(payload) >= 114:
                device.output_enabled = bool(payload[113])
        
        device.packet_count += 1
        return True


if __name__ == "__main__":
    print("=== Commands ===")
    print(f"Set 5.0V: {Commands.set_voltage(5.0)}")
    print(f"Set 1.0A: {Commands.set_current(1.0)}")
    print(f"OUTPUT_ON: {Commands.OUTPUT_ON}")
