"""
FNIRSI Power Supply Python Library
===================================
Complete Python implementation for FNIRSI power supply control.

This module provides:
- FnirsiDevice: Main class for controlling FNIRSI power supplies
- Commands: Predefined command constants
- DeviceData: Data structure for device state
- Protocol utilities for packet creation/parsing

Protocol Format:
    Request:  [0xF1] [CmdType] [Register] [Length] [Data...] [Checksum]
    Response: [0xF0] [CmdType] [Register] [Length] [Data...] [Checksum]
    
Checksum = (register + length + sum(data)) & 0xFF

Data encoding: IEEE 754 float, little-endian (4 bytes)
"""

import serial
import serial.tools.list_ports
import struct
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from enum import IntEnum


# =============================================================================
# Protocol Constants
# =============================================================================

class Header:
    REQUEST = 0xF1
    RESPONSE = 0xF0


class CmdType:
    """Command types"""
    READ = 0xA1     # Read register
    WRITE = 0xB0    # Write value (float)
    WRITE_BYTE = 0xB1  # Write single byte
    CONNECT = 0xC1  # Connect/Disconnect
    CONFIG = 0xC0   # Configuration


class Register(IntEnum):
    """Register addresses"""
    # Settings
    BAUD_RATE = 0x00
    SET_VOLTAGE = 0xC0
    SET_CURRENT = 0xDE
    
    # Live readings
    LIVE_VALUES = 0xC3  # V, A, W
    TEMPERATURE = 0xC4
    
    # Capacity
    CAPACITY_AH = 0xD9
    CAPACITY_WH = 0xDA
    
    # Status
    OUTPUT_STATE = 0xDB
    PROTECTION = 0xDC
    MODE = 0xDD
    
    # Device info
    MODEL = 0xDE
    SERIAL = 0xDF
    FIRMWARE = 0xE0
    DEVICE_ID = 0xE1
    
    # Limits
    MAX_VOLTAGE = 0xE2
    MAX_CURRENT = 0xE3
    
    # Preset groups
    PRESET_V1 = 0xC1
    PRESET_A1 = 0xC2
    
    # All parameters
    ALL = 0xFF


class Protection(IntEnum):
    """Protection status codes"""
    OK = 0
    OVP = 1   # Over Voltage Protection
    OCP = 2   # Over Current Protection
    OPP = 3   # Over Power Protection  
    OTP = 4   # Over Temperature Protection
    SCP = 5   # Short Circuit Protection


class Mode(IntEnum):
    """Output mode"""
    CV = 0  # Constant Voltage
    CC = 1  # Constant Current


# =============================================================================
# Utility Functions
# =============================================================================

def float_to_bytes(value: float) -> bytes:
    """Convert float to 4 bytes (little-endian IEEE 754)"""
    return struct.pack('<f', value)


def bytes_to_float(data: bytes, offset: int = 0) -> float:
    """Convert 4 bytes to float (little-endian IEEE 754)"""
    if len(data) >= offset + 4:
        return struct.unpack('<f', data[offset:offset + 4])[0]
    return 0.0


def hex_dump(data: bytes, max_len: int = 0) -> str:
    """Format bytes as hex string"""
    if max_len and len(data) > max_len:
        return ' '.join(f'{b:02X}' for b in data[:max_len]) + f" ... ({len(data)} bytes)"
    return ' '.join(f'{b:02X}' for b in data)


# =============================================================================
# Command Builder
# =============================================================================

class CommandBuilder:
    """
    Command packet builder
    
    Packet format: [Header] [CmdType] [Register] [Length] [Data...] [Checksum]
    Checksum = (Register + Length + sum(Data)) & 0xFF
    """
    
    def __init__(self, header: int = Header.REQUEST, cmd_type: int = CmdType.READ,
                 register: int = 0, data: bytes = b'\x00'):
        self.header = header
        self.cmd_type = cmd_type
        self.register = register
        self.data = data
    
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
        return hex_dump(self.packet)
    
    def __bytes__(self) -> bytes:
        return self.packet


def make_command(cmd_type: int, register: int, data: bytes = b'\x00') -> bytes:
    """Create command packet (convenience function)"""
    return CommandBuilder(Header.REQUEST, cmd_type, register, data).packet


# =============================================================================
# Predefined Commands
# =============================================================================

class Commands:
    """Predefined command packets"""
    
    # Connection
    CONNECT = make_command(CmdType.CONNECT, 0x00, b'\x01')
    DISCONNECT = make_command(CmdType.CONNECT, 0x00, b'\x00')
    
    # Read commands
    READ_ALL = make_command(CmdType.READ, Register.ALL, b'\x00')
    READ_VOLTAGE = make_command(CmdType.READ, Register.SET_VOLTAGE, b'\x00')
    READ_CURRENT = make_command(CmdType.READ, Register.SET_CURRENT, b'\x00')
    READ_LIVE = make_command(CmdType.READ, Register.LIVE_VALUES, b'\x00')
    READ_MODEL = make_command(CmdType.READ, Register.FIRMWARE, b'\x00')
    READ_DEVICE_ID = make_command(CmdType.READ, Register.DEVICE_ID, b'\x00')
    
    # Output control
    OUTPUT_ON = make_command(CmdType.WRITE_BYTE, Register.OUTPUT_STATE, b'\x01')
    OUTPUT_OFF = make_command(CmdType.WRITE_BYTE, Register.OUTPUT_STATE, b'\x00')
    
    @staticmethod
    def set_voltage(voltage: float) -> bytes:
        """Set output voltage"""
        return make_command(CmdType.WRITE, Register.SET_VOLTAGE, float_to_bytes(voltage))
    
    @staticmethod
    def set_current(current: float) -> bytes:
        """Set current limit"""
        return make_command(CmdType.WRITE, Register.SET_CURRENT, float_to_bytes(current))
    
    @staticmethod
    def set_baud_rate(index: int) -> bytes:
        """Set baud rate (1=9600, 2=19200, 3=38400, 4=57600, 5=115200)"""
        return make_command(CmdType.WRITE, Register.BAUD_RATE, bytes([index]))


# =============================================================================
# Device Data Structure
# =============================================================================

@dataclass
class DeviceData:
    """
    Device state data structure
    
    Field offsets in 0xFF response:
    - 0:   Input voltage (Data1)
    - 4:   Set voltage (Data2)
    - 8:   Set current (Data3)
    - 12:  Output voltage (Data4)
    - 16:  Output current (Data5)
    - 20:  Output power (Data6)
    - 24:  Temperature (Data7)
    - 28-72: Preset values (Data8-Data19)
    - 96:  Preset index (Data25)
    - 97:  Unknown (Data26)
    - 98:  Unknown (Data27)
    - 99:  Capacity Ah (Data28)
    - 103: Capacity Wh (Data29)
    - 107: Output enabled (Data30)
    - 108: Protection status (Data31)
    - 109: Mode CV/CC (Data32)
    - 110: Unknown
    - 111: Max voltage (Data37)
    - 115: Max current (Data38)
    - 119+: OVP/OCP limits (Data39-43)
    """
    
    # Basic readings
    input_voltage: float = 0.0
    set_voltage: float = 0.0
    set_current: float = 0.0
    output_voltage: float = 0.0
    output_current: float = 0.0
    output_power: float = 0.0
    temperature: float = 0.0
    
    # Limits
    max_voltage: float = 24.0
    max_current: float = 5.0
    
    # Protection limits
    ovp_voltage: float = 0.0
    ocp_current: float = 0.0
    opp_power: float = 0.0
    otp_temp: float = 0.0
    
    # Status
    output_enabled: bool = False
    protection_status: int = 0
    mode: int = 0
    
    # Capacity counters
    capacity_ah: float = 0.0
    capacity_wh: float = 0.0
    
    # Device info
    model: str = ""
    serial_number: str = ""
    firmware: str = ""
    device_id: int = 0
    
    # Presets (6 groups, V/A pairs)
    presets: List[tuple] = field(default_factory=lambda: [(0.0, 0.0)] * 6)
    preset_index: int = 0
    
    # Connection state
    connected: bool = False
    packet_count: int = 0
    last_update: float = 0.0
    
    @property
    def mode_string(self) -> str:
        return "CC" if self.mode == 1 else "CV"
    
    @property
    def protection_string(self) -> str:
        names = {
            0: "OK", 1: "OVP", 2: "OCP", 
            3: "OPP", 4: "OTP", 5: "SCP"
        }
        return names.get(self.protection_status, f"Unknown({self.protection_status})")
    
    @property
    def temperature_f(self) -> float:
        return self.temperature * 9 / 5 + 32
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'input_voltage': self.input_voltage,
            'set_voltage': self.set_voltage,
            'set_current': self.set_current,
            'output_voltage': self.output_voltage,
            'output_current': self.output_current,
            'output_power': self.output_power,
            'temperature': self.temperature,
            'max_voltage': self.max_voltage,
            'max_current': self.max_current,
            'output_enabled': self.output_enabled,
            'protection_status': self.protection_string,
            'mode': self.mode_string,
            'capacity_ah': self.capacity_ah,
            'capacity_wh': self.capacity_wh,
            'model': self.model,
            'firmware': self.firmware,
            'connected': self.connected,
        }


# =============================================================================
# Response Parser
# =============================================================================

class ResponseParser:
    """
    Response packet parser
    """
    
    @staticmethod
    def validate_packet(data: bytes) -> bool:
        """Validate packet header and checksum"""
        if len(data) < 5 or data[0] != Header.RESPONSE:
            return False
        
        register = data[2]
        length = data[3]
        
        if len(data) < 5 + length:
            return False
        
        payload = data[4:4 + length]
        checksum = data[4 + length]
        calc_cs = (register + length + sum(payload)) & 0xFF
        
        return calc_cs == checksum
    
    @staticmethod
    def parse_packet(data: bytes, device: DeviceData) -> bool:
        """Parse single response packet and update device data"""
        if not ResponseParser.validate_packet(data):
            return False
        
        register = data[2]
        length = data[3]
        payload = data[4:4 + length]
        
        # Parse by register
        if register == Register.SET_VOLTAGE:  # 0xC0
            device.input_voltage = bytes_to_float(payload, 0)
            
        elif register == Register.LIVE_VALUES:  # 0xC3
            if len(payload) >= 12:
                device.output_voltage = bytes_to_float(payload, 0)
                device.output_current = bytes_to_float(payload, 4)
                device.output_power = bytes_to_float(payload, 8)
                
        elif register == Register.TEMPERATURE:  # 0xC4
            device.temperature = bytes_to_float(payload, 0)
            
        elif register == Register.CAPACITY_AH:  # 0xD9
            device.capacity_ah = bytes_to_float(payload, 0)
            
        elif register == Register.CAPACITY_WH:  # 0xDA
            device.capacity_wh = bytes_to_float(payload, 0)
            
        elif register == Register.OUTPUT_STATE:  # 0xDB
            # Note: 0 = ON, 1 = OFF in original code
            device.output_enabled = (payload[0] == 0)
            
        elif register == Register.PROTECTION:  # 0xDC
            device.protection_status = payload[0]
            
        elif register == Register.MODE:  # 0xDD
            device.mode = payload[0]
            
        elif register == Register.MODEL:  # 0xDE
            device.model = payload.decode('ascii', errors='ignore').rstrip('\x00')
            
        elif register == Register.SERIAL:  # 0xDF
            device.serial_number = payload.decode('ascii', errors='ignore').rstrip('\x00')
            
        elif register == Register.FIRMWARE:  # 0xE0
            device.firmware = payload.decode('ascii', errors='ignore').rstrip('\x00')
            
        elif register == Register.DEVICE_ID:  # 0xE1
            if payload:
                device.device_id = payload[0]
                
        elif register == Register.MAX_VOLTAGE:  # 0xE2
            device.max_voltage = bytes_to_float(payload, 0)
            
        elif register == Register.MAX_CURRENT:  # 0xE3
            device.max_current = bytes_to_float(payload, 0)
            
        elif register == Register.ALL:  # 0xFF - all parameters
            ResponseParser._parse_all_data(payload, device)
        
        device.packet_count += 1
        device.last_update = time.time()
        return True
    
    @staticmethod
    def _parse_all_data(payload: bytes, device: DeviceData):
        """Parse 0xFF response (all parameters) based on setAllData()"""
        if len(payload) < 119:
            return
        
        # Basic readings
        device.input_voltage = bytes_to_float(payload, 0)
        device.set_voltage = bytes_to_float(payload, 4)
        device.set_current = bytes_to_float(payload, 8)
        device.output_voltage = bytes_to_float(payload, 12)
        device.output_current = bytes_to_float(payload, 16)
        device.output_power = bytes_to_float(payload, 20)
        device.temperature = bytes_to_float(payload, 24)
        
        # Presets (6 pairs at offsets 28-72)
        presets = []
        for i in range(6):
            v = bytes_to_float(payload, 28 + i * 8)
            a = bytes_to_float(payload, 32 + i * 8)
            presets.append((v, a))
        device.presets = presets
        
        # Status bytes
        device.preset_index = payload[96]
        device.capacity_ah = bytes_to_float(payload, 99)
        device.capacity_wh = bytes_to_float(payload, 103)
        device.output_enabled = (payload[107] == 0)
        device.protection_status = payload[108]
        device.mode = payload[109]
        
        # Limits
        device.max_voltage = bytes_to_float(payload, 111)
        device.max_current = bytes_to_float(payload, 115)
        
        # Protection limits (if available)
        if len(payload) >= 139:
            device.ovp_voltage = bytes_to_float(payload, 119)
            device.ocp_current = bytes_to_float(payload, 123)
            device.opp_power = bytes_to_float(payload, 127)
            device.otp_temp = bytes_to_float(payload, 131)
    
    @staticmethod
    def parse_buffer(buffer: bytearray, device: DeviceData) -> int:
        """Parse all complete packets from buffer, return bytes consumed"""
        consumed = 0
        
        while len(buffer) - consumed >= 5:
            # Find response header
            if buffer[consumed] != Header.RESPONSE:
                consumed += 1
                continue
            
            if len(buffer) - consumed < 4:
                break
            
            length = buffer[consumed + 3]
            packet_len = 5 + length
            
            if len(buffer) - consumed < packet_len:
                break
            
            packet = bytes(buffer[consumed:consumed + packet_len])
            ResponseParser.parse_packet(packet, device)
            consumed += packet_len
        
        return consumed


# =============================================================================
# FNIRSI Device Class
# =============================================================================

class FnirsiDevice:
    """
    Main class for controlling FNIRSI power supplies
    
    Usage:
        device = FnirsiDevice()
        if device.connect("COM11"):
            device.set_voltage(5.0)
            device.set_current(1.0)
            device.output_on()
            print(device.data)
            device.disconnect()
    """
    
    BAUD_RATES = [9600, 19200, 38400, 57600, 115200]
    DEFAULT_BAUD = 9600
    
    def __init__(self):
        self._port: Optional[serial.Serial] = None
        self._data = DeviceData()
        self._buffer = bytearray()
        self._read_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Callbacks
        self._data_callback: Optional[Callable[[DeviceData], None]] = None
        self._connect_callback: Optional[Callable[[bool], None]] = None
        self._error_callback: Optional[Callable[[str], None]] = None
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def is_connected(self) -> bool:
        return self._port is not None and self._port.is_open and self._data.connected
    
    @property
    def data(self) -> DeviceData:
        return self._data
    
    @property
    def port_name(self) -> Optional[str]:
        return self._port.name if self._port else None
    
    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------
    
    def on_data(self, callback: Callable[[DeviceData], None]):
        """Set callback for data updates"""
        self._data_callback = callback
    
    def on_connect(self, callback: Callable[[bool], None]):
        """Set callback for connection state changes"""
        self._connect_callback = callback
    
    def on_error(self, callback: Callable[[str], None]):
        """Set callback for errors"""
        self._error_callback = callback
    
    # -------------------------------------------------------------------------
    # Static methods
    # -------------------------------------------------------------------------
    
    @staticmethod
    def list_ports() -> List[str]:
        """List available COM ports"""
        return [p.device for p in serial.tools.list_ports.comports()]
    
    @staticmethod
    def list_ports_detailed() -> List[dict]:
        """List available COM ports with details"""
        return [
            {'device': p.device, 'description': p.description, 'hwid': p.hwid}
            for p in serial.tools.list_ports.comports()
        ]
    
    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------
    
    def connect(self, port: str, baud: int = DEFAULT_BAUD, timeout: float = 2.0) -> bool:
        """
        Connect to FNIRSI device
        """
        self.disconnect()
        
        try:
            self._port = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                write_timeout=None  # No write timeout
            )
            self._port.rts = True
            self._port.dtr = True
            time.sleep(0.1)  # Wait for port to stabilize
            self._port.reset_input_buffer()
            self._port.reset_output_buffer()
            self._buffer.clear()
            
            # Start read thread
            self._stop_event.clear()
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            
            # Send CONNECT command
            self._send(Commands.CONNECT)
            time.sleep(0.3)
            
            # Wait for response
            start = time.time()
            while time.time() - start < timeout:
                if self._data.packet_count > 0:
                    self._data.connected = True
                    break
                time.sleep(0.1)
            
            if self._data.connected:
                # Initialize - send command sequence from commandInit()
                self._send(Commands.READ_CURRENT)
                self._send(Commands.READ_MODEL)
                self._send(Commands.READ_ALL)
                
                if self._connect_callback:
                    self._connect_callback(True)
                return True
            else:
                self.disconnect()
                return False
                
        except Exception as e:
            self._handle_error(f"Connect error: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from device"""
        self._stop_event.set()
        self._data.connected = False
        
        if self._port and self._port.is_open:
            try:
                # Try to send disconnect without blocking
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
        
        self._data = DeviceData()
        
        if self._connect_callback:
            self._connect_callback(False)
    
    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------
    
    def set_voltage(self, voltage: float) -> bool:
        """Set output voltage"""
        voltage = max(0, min(voltage, self._data.max_voltage))
        return self._send(Commands.set_voltage(voltage))
    
    def set_current(self, current: float) -> bool:
        """Set current limit"""
        current = max(0, min(current, self._data.max_current))
        return self._send(Commands.set_current(current))
    
    def output_on(self) -> bool:
        """Turn output ON"""
        return self._send(Commands.OUTPUT_ON)
    
    def output_off(self) -> bool:
        """Turn output OFF"""
        return self._send(Commands.OUTPUT_OFF)
    
    def read_all(self) -> bool:
        """Request all parameters"""
        return self._send(Commands.READ_ALL)
    
    def read_live(self) -> bool:
        """Request live readings (V, A, W)"""
        return self._send(Commands.READ_LIVE)
    
    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------
    
    def _send(self, command: bytes) -> bool:
        """Send command to device"""
        if not self._port or not self._port.is_open:
            return False
        
        try:
            with self._lock:
                self._port.write(command)
                self._port.flush()
            return True
        except Exception as e:
            self._handle_error(f"Send error: {e}")
            return False
    
    def _read_loop(self):
        """Background read thread"""
        while not self._stop_event.is_set():
            try:
                if self._port and self._port.is_open and self._port.in_waiting > 0:
                    with self._lock:
                        data = self._port.read(self._port.in_waiting)
                    
                    self._buffer.extend(data)
                    consumed = ResponseParser.parse_buffer(self._buffer, self._data)
                    self._buffer = self._buffer[consumed:]
                    
                    if self._data_callback and consumed > 0:
                        try:
                            self._data_callback(self._data)
                        except:
                            pass
                
                time.sleep(0.01)
                
            except Exception as e:
                if not self._stop_event.is_set():
                    self._handle_error(f"Read error: {e}")
                time.sleep(0.1)
    
    def _handle_error(self, message: str):
        """Handle error"""
        if self._error_callback:
            self._error_callback(message)
        else:
            print(f"[FNIRSI] {message}")


# =============================================================================
# Convenience Functions
# =============================================================================

def find_fnirsi_device(baud: int = 9600) -> Optional[str]:
    """
    Scan all COM ports to find FNIRSI device
    Returns port name if found, None otherwise
    """
    for port in FnirsiDevice.list_ports():
        try:
            ser = serial.Serial(port, baud, timeout=0.5, write_timeout=1)
            ser.rts = True
            ser.reset_input_buffer()
            time.sleep(0.1)
            
            ser.write(Commands.CONNECT)
            ser.flush()
            time.sleep(0.3)
            
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                if Header.RESPONSE in data:
                    ser.close()
                    return port
            
            ser.close()
        except:
            pass
    
    return None


# =============================================================================
# Main (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("FNIRSI Power Supply Library")
    print("=" * 40)
    
    # List ports
    print("\nAvailable ports:")
    for p in FnirsiDevice.list_ports_detailed():
        print(f"  {p['device']}: {p['description']}")
    
    # Try to connect
    port = sys.argv[1] if len(sys.argv) > 1 else "COM11"
    
    device = FnirsiDevice()
    device.on_error(lambda e: print(f"Error: {e}"))
    
    print(f"\nConnecting to {port}...")
    if device.connect(port):
        print("Connected!")
        print(f"\nDevice data:")
        for k, v in device.data.to_dict().items():
            print(f"  {k}: {v}")
        
        device.disconnect()
    else:
        print("Connection failed!")
