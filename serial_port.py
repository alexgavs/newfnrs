"""
FNIRSI Power Supply Serial Port Module - Fixed Version
"""

import serial
import serial.tools.list_ports
from typing import Optional, Callable, List
from threading import Thread, Event
import time

from protocol import Command, Commands, DeviceData, ResponseParser


class SerialConnection:
    """Класс для работы с последовательным портом"""
    
    BAUD_RATES = [9600, 19200, 38400, 57600, 115200]
    DEFAULT_BAUD = 9600
    
    def __init__(self):
        self._port: Optional[serial.Serial] = None
        self._device_data = DeviceData()
        self._read_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._data_callback: Optional[Callable[[DeviceData], None]] = None
        self._connection_callback: Optional[Callable[[bool], None]] = None
        self._is_verified = False
        self._buffer = bytearray()
    
    @property
    def is_open(self) -> bool:
        return self._port is not None and self._port.is_open and self._is_verified
    
    @property
    def device_data(self) -> DeviceData:
        return self._device_data
    
    @staticmethod
    def list_ports() -> List[str]:
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def set_data_callback(self, callback: Callable[[DeviceData], None]):
        self._data_callback = callback
    
    def set_connection_callback(self, callback: Callable[[bool], None]):
        self._connection_callback = callback
    
    def connect(self, port_name: str, baud_rate: int = DEFAULT_BAUD) -> bool:
        try:
            self.disconnect()
            
            self._port = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5
            )
            self._port.rts = True
            self._port.dtr = True
            self._port.reset_input_buffer()
            self._buffer.clear()
            
            # Запустить поток чтения
            self._stop_event.clear()
            self._read_thread = Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            
            # Отправить команду подключения
            self.send(Commands.CONNECT)
            time.sleep(0.5)
            
            # Ждём данные
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self._device_data.packet_count > 0:
                    self._is_verified = True
                    break
                time.sleep(0.1)
            
            if self._is_verified:
                self.send(Commands.READ_ALL)
                if self._connection_callback:
                    self._connection_callback(True)
                return True
            else:
                self.disconnect()
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        if self._port and self._port.is_open:
            try:
                self.send(Commands.DISCONNECT)
                time.sleep(0.1)
            except:
                pass
        
        self._stop_event.set()
        self._is_verified = False
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1)
        
        if self._port:
            try:
                self._port.close()
            except:
                pass
            self._port = None
        
        self._device_data = DeviceData()
        
        if self._connection_callback:
            self._connection_callback(False)
    
    def send(self, command: Command) -> bool:
        if not self._port or not self._port.is_open:
            return False
        try:
            self._port.write(command.packet)
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def set_voltage(self, voltage: float) -> bool:
        voltage = max(0, min(voltage, self._device_data.max_voltage))
        cmd = Commands.set_voltage(voltage)
        print(f"Sending set_voltage({voltage}): {cmd}")
        return self.send(cmd)
    
    def set_current(self, current: float) -> bool:
        current = max(0, min(current, self._device_data.max_current))
        cmd = Commands.set_current(current)
        print(f"Sending set_current({current}): {cmd}")
        return self.send(cmd)
    
    def set_output(self, enabled: bool) -> bool:
        cmd = Commands.OUTPUT_ON if enabled else Commands.OUTPUT_OFF
        print(f"Sending output {'ON' if enabled else 'OFF'}: {cmd}")
        return self.send(cmd)
    
    def request_data(self) -> bool:
        return self.send(Commands.READ_ALL)
    
    def _read_loop(self):
        while not self._stop_event.is_set():
            try:
                if self._port and self._port.is_open and self._port.in_waiting > 0:
                    data = self._port.read(self._port.in_waiting)
                    self._buffer.extend(data)
                    self._process_buffer()
                time.sleep(0.01)
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"Read error: {e}")
                time.sleep(0.1)
    
    def _process_buffer(self):
        while len(self._buffer) >= 5:
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
            
            if ResponseParser.parse(packet, self._device_data):
                if self._data_callback:
                    try:
                        self._data_callback(self._device_data)
                    except:
                        pass
