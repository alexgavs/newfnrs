# FNIRSI Power Supply Protocol Specification

**Author: ALEXGAVS**  
**Version: 1.0**  
**Date: January 2026**

---

## Оглавление / Table of Contents

1. [Общие сведения / Overview](#общие-сведения--overview)
2. [Физический уровень / Physical Layer](#физический-уровень--physical-layer)
3. [Структура пакета / Packet Structure](#структура-пакета--packet-structure)
4. [Типы команд / Command Types](#типы-команд--command-types)
5. [Регистры / Registers](#регистры--registers)
6. [Формат данных / Data Format](#формат-данных--data-format)
7. [Контрольная сумма / Checksum](#контрольная-сумма--checksum)
8. [Примеры команд / Command Examples](#примеры-команд--command-examples)
9. [Структура ответа 0xFF / Response 0xFF Structure](#структура-ответа-0xff--response-0xff-structure)
10. [Коды защит / Protection Codes](#коды-защит--protection-codes)

---

## Общие сведения / Overview

Протокол FNIRSI используется для управления лабораторными источниками питания серии FNIRSI (DPS-150, FNB58 и др.) через USB/Serial интерфейс.

The FNIRSI protocol is used to control FNIRSI laboratory power supplies (DPS-150, FNB58, etc.) via USB/Serial interface.

### Основные характеристики / Key Features

| Параметр | Значение |
|----------|----------|
| Интерфейс | USB CDC (Virtual COM Port) |
| Скорость по умолчанию | 115200 baud |
| Формат данных | 8N1 (8 бит данных, без чётности, 1 стоп-бит) |
| Порядок байт | Little-Endian |
| Формат чисел | IEEE 754 Single Precision Float |

---

## Физический уровень / Physical Layer

### Параметры соединения / Connection Parameters

```
Baud Rate:    115200 (default) / 9600 / 19200 / 38400 / 57600
Data Bits:    8
Parity:       None
Stop Bits:    1
Flow Control: None
```

### Поддерживаемые скорости / Supported Baud Rates

| Индекс | Скорость |
|--------|----------|
| 1 | 9600 |
| 2 | 19200 |
| 3 | 38400 |
| 4 | 57600 |
| 5 | 115200 |

---

## Структура пакета / Packet Structure

### Запрос (Request) / Host → Device

```
┌─────────┬──────────┬──────────┬────────┬─────────────┬──────────┐
│ Header  │ CmdType  │ Register │ Length │ Data[0..N]  │ Checksum │
├─────────┼──────────┼──────────┼────────┼─────────────┼──────────┤
│ 1 byte  │ 1 byte   │ 1 byte   │ 1 byte │ N bytes     │ 1 byte   │
│ 0xF1    │ 0xA1-C1  │ 0x00-FF  │ 0-255  │ Payload     │ CS       │
└─────────┴──────────┴──────────┴────────┴─────────────┴──────────┘
```

### Ответ (Response) / Device → Host

```
┌─────────┬──────────┬──────────┬────────┬─────────────┬──────────┐
│ Header  │ CmdType  │ Register │ Length │ Data[0..N]  │ Checksum │
├─────────┼──────────┼──────────┼────────┼─────────────┼──────────┤
│ 1 byte  │ 1 byte   │ 1 byte   │ 1 byte │ N bytes     │ 1 byte   │
│ 0xF0    │ 0xA1-C1  │ 0x00-FF  │ 0-255  │ Payload     │ CS       │
└─────────┴──────────┴──────────┴────────┴─────────────┴──────────┘
```

### Поля пакета / Packet Fields

| Поле | Размер | Описание |
|------|--------|----------|
| **Header** | 1 байт | `0xF1` — запрос, `0xF0` — ответ |
| **CmdType** | 1 байт | Тип команды (см. ниже) |
| **Register** | 1 байт | Адрес регистра |
| **Length** | 1 байт | Длина поля данных (0-255) |
| **Data** | N байт | Данные (Length байт) |
| **Checksum** | 1 байт | Контрольная сумма |

---

## Типы команд / Command Types

| Код | Имя | Описание RU | Description EN |
|-----|-----|-------------|----------------|
| `0xA1` | READ | Чтение регистра | Read register |
| `0xB0` | WRITE | Запись float (4 байта) | Write float value (4 bytes) |
| `0xB1` | WRITE_BYTE | Запись 1 байта | Write single byte |
| `0xC0` | CONFIG | Конфигурация | Configuration |
| `0xC1` | CONNECT | Подключение/отключение | Connect/Disconnect |

### Подробное описание / Detailed Description

#### 0xA1 — READ
Чтение данных из регистра устройства. Поле Data обычно содержит `0x00`.

#### 0xB0 — WRITE (Float)
Запись значения с плавающей точкой. Data содержит 4 байта IEEE 754 float (little-endian).

#### 0xB1 — WRITE_BYTE
Запись одного байта. Используется для переключения состояний (вкл/выкл).

#### 0xC1 — CONNECT
Установка/разрыв соединения с устройством:
- `Data = 0x01` — подключиться
- `Data = 0x00` — отключиться

---

## Регистры / Registers

### Основные регистры / Main Registers

| Адрес | Имя | Тип | Описание RU | Description EN |
|-------|-----|-----|-------------|----------------|
| `0x00` | BAUD_RATE | R/W | Скорость порта | Baud rate setting |
| `0xC0` | SET_VOLTAGE | R/W | Уставка напряжения | Voltage setpoint |
| `0xC1` | WRITE_VOLTAGE | W | Записать напряжение | Write voltage |
| `0xC2` | WRITE_CURRENT | W | Записать ток | Write current |
| `0xC3` | LIVE_VALUES | R | Текущие V, A, W | Live V, A, W readings |
| `0xC4` | TEMPERATURE | R | Температура | Temperature |
| `0xC5-0xD0` | PRESET_1-6 | R/W | Пресеты устройства | Device presets |
| `0xD1` | OVP_LIMIT | R/W | Лимит OVP (V) | OVP limit voltage |
| `0xD2` | OCP_LIMIT | R/W | Лимит OCP (A) | OCP limit current |
| `0xD3` | OPP_LIMIT | R/W | Лимит OPP (W) | OPP limit power |
| `0xD4` | OTP_LIMIT | R/W | Лимит OTP (°C) | OTP limit temp |
| `0xD6` | BRIGHTNESS | R/W | Яркость дисплея (0-20) | Display brightness (0-20) |
| `0xD9` | CAPACITY_AH | R | Ёмкость (Ah) | Capacity (Ah) |
| `0xDA` | CAPACITY_WH | R | Ёмкость (Wh) | Capacity (Wh) |
| `0xDB` | OUTPUT_STATE | R/W | Состояние выхода | Output state |
| `0xDC` | PROTECTION | R | Статус защиты | Protection status |
| `0xDD` | MODE | R | Режим (CV/CC) | Mode (CV/CC) |
| `0xDE` | MODEL/SET_CURRENT | R/W | Модель / Уставка тока | Model / Current setpoint |
| `0xDF` | SERIAL | R | Серийный номер | Serial number |
| `0xE0` | FIRMWARE | R | Версия прошивки | Firmware version |
| `0xE1` | DEVICE_ID | R | ID устройства | Device ID |
| `0xE2` | MAX_VOLTAGE | R | Макс. напряжение | Max voltage |
| `0xE3` | MAX_CURRENT | R | Макс. ток | Max current |
| `0xFF` | ALL | R | Все параметры | All parameters |

### Пресеты устройства / Device Presets

Устройство хранит 6 пресетов в памяти (видны в меню на экране):

| Пресет | V регистр | A регистр |
|--------|-----------|-----------|
| 1 | 0xC5 | 0xC6 |
| 2 | 0xC7 | 0xC8 |
| 3 | 0xC9 | 0xCA |
| 4 | 0xCB | 0xCC |
| 5 | 0xCD | 0xCE |
| 6 | 0xCF | 0xD0 |

Формула: `V_reg = 0xC3 + 2*N`, `A_reg = V_reg + 1` (N = 1..6)

### Регистр 0xC3 — LIVE_VALUES (Измерения в реальном времени)

Ответ содержит 12 байт:

```
┌──────────────┬──────────────┬──────────────┐
│ Offset 0-3   │ Offset 4-7   │ Offset 8-11  │
├──────────────┼──────────────┼──────────────┤
│ Voltage (V)  │ Current (A)  │ Power (W)    │
│ float32 LE   │ float32 LE   │ float32 LE   │
└──────────────┴──────────────┴──────────────┘
```

### Регистр 0xDB — OUTPUT_STATE

| Значение | Состояние |
|----------|-----------|
| `0x00` | Выход ВЫКЛЮЧЕН (OFF) |
| `0x01` | Выход ВКЛЮЧЕН (ON) |

**Примечание:** Отправить 0x01 = включить выход, 0x00 = выключить.

---

## Формат данных / Data Format

### IEEE 754 Single Precision Float (Little-Endian)

Все числовые значения (напряжение, ток, мощность, температура) передаются как 4-байтовые числа с плавающей точкой в формате IEEE 754 (little-endian).

```
Пример: 5.0V
Hex: 00 00 A0 40 (little-endian)
Байты: [0x00, 0x00, 0xA0, 0x40]
```

### Преобразование / Conversion

**Python:**
```python
import struct

# Float → Bytes
def float_to_bytes(value: float) -> bytes:
    return struct.pack('<f', value)

# Bytes → Float
def bytes_to_float(data: bytes) -> float:
    return struct.unpack('<f', data[:4])[0]
```

**C:**
```c
// Float → Bytes
void float_to_bytes(float value, uint8_t* bytes) {
    memcpy(bytes, &value, 4);
}

// Bytes → Float
float bytes_to_float(uint8_t* bytes) {
    float value;
    memcpy(&value, bytes, 4);
    return value;
}
```

### Примеры значений / Value Examples

| Значение | Hex (LE) | Байты |
|----------|----------|-------|
| 0.0 | 00 00 00 00 | [0x00, 0x00, 0x00, 0x00] |
| 1.0 | 00 00 80 3F | [0x00, 0x00, 0x80, 0x3F] |
| 3.3 | 33 33 53 40 | [0x33, 0x33, 0x53, 0x40] |
| 5.0 | 00 00 A0 40 | [0x00, 0x00, 0xA0, 0x40] |
| 12.0 | 00 00 40 41 | [0x00, 0x00, 0x40, 0x41] |
| 24.0 | 00 00 C0 41 | [0x00, 0x00, 0xC0, 0x41] |

---

## Контрольная сумма / Checksum

Контрольная сумма вычисляется как:

```
Checksum = (Register + Length + sum(Data)) & 0xFF
```

### Алгоритм / Algorithm

```python
def calculate_checksum(register: int, data: bytes) -> int:
    cs = register + len(data)
    for byte in data:
        cs += byte
    return cs & 0xFF
```

### Пример / Example

Команда: Установить напряжение 5.0V

```
Header:   0xF1
CmdType:  0xB0
Register: 0xC0
Length:   0x04
Data:     [0x00, 0x00, 0xA0, 0x40]  (5.0 as float)

Checksum = (0xC0 + 0x04 + 0x00 + 0x00 + 0xA0 + 0x40) & 0xFF
         = (192 + 4 + 0 + 0 + 160 + 64) & 0xFF
         = 420 & 0xFF
         = 0xA4

Пакет: F1 B0 C0 04 00 00 A0 40 A4
```

---

## Примеры команд / Command Examples

### Подключение / Connect

```
TX: F1 C1 00 01 01 02
    │  │  │  │  │  └─ Checksum
    │  │  │  │  └──── Data: 0x01 (connect)
    │  │  │  └─────── Length: 1
    │  │  └────────── Register: 0x00
    │  └───────────── CmdType: 0xC1 (CONNECT)
    └──────────────── Header: 0xF1 (Request)
```

### Отключение / Disconnect

```
TX: F1 C1 00 01 00 01
```

### Чтение всех параметров / Read All Parameters

```
TX: F1 A1 FF 01 00 00
    │  │  │  │  │  └─ Checksum: (0xFF + 0x01 + 0x00) & 0xFF = 0x00
    │  │  │  │  └──── Data: 0x00
    │  │  │  └─────── Length: 1
    │  │  └────────── Register: 0xFF (ALL)
    │  └───────────── CmdType: 0xA1 (READ)
    └──────────────── Header: 0xF1
```

### Установить напряжение 5.0V / Set Voltage 5.0V

```
TX: F1 B0 C0 04 00 00 A0 40 A4
    │  │  │  │  └──────────┴── Data: 5.0 as IEEE 754 float LE
    │  │  │  └─────────────── Length: 4
    │  │  └────────────────── Register: 0xC0 (SET_VOLTAGE)
    │  └───────────────────── CmdType: 0xB0 (WRITE)
    └──────────────────────── Header: 0xF1
```

### Установить ток 1.0A / Set Current 1.0A

```
TX: F1 B0 DE 04 00 00 80 3F 61
    │  │  │  │  └──────────┴── Data: 1.0 as IEEE 754 float LE
    │  │  │  └─────────────── Length: 4
    │  │  └────────────────── Register: 0xDE (SET_CURRENT)
    │  └───────────────────── CmdType: 0xB0 (WRITE)
    └──────────────────────── Header: 0xF1
```

### Включить выход / Output ON

```
TX: F1 B1 DB 01 01 DD
    │  │  │  │  │  └─ Checksum
    │  │  │  │  └──── Data: 0x01 (ON)
    │  │  │  └─────── Length: 1
    │  │  └────────── Register: 0xDB (OUTPUT_STATE)
    │  └───────────── CmdType: 0xB1 (WRITE_BYTE)
    └──────────────── Header: 0xF1
```

### Выключить выход / Output OFF

```
TX: F1 B1 DB 01 00 DC
```

### Установить яркость дисплея / Set Display Brightness

```
TX: F1 B1 D6 01 0A E1
    │  │  │  │  │  └─ Checksum: (0xD6 + 0x01 + 0x0A) & 0xFF = 0xE1
    │  │  │  │  └──── Data: 0x0A (10 = середина диапазона)
    │  │  │  └─────── Length: 1
    │  │  └────────── Register: 0xD6 (BRIGHTNESS)
    │  └───────────── CmdType: 0xB1 (WRITE_BYTE)
    └──────────────── Header: 0xF1

Диапазон: 0 (минимум) — 20 (максимум)
```

---

## Структура ответа 0xFF / Response 0xFF Structure

При чтении регистра 0xFF устройство возвращает полный дамп всех параметров (около 140 байт).

### Смещения данных / Data Offsets

| Offset | Размер | Параметр | Тип |
|--------|--------|----------|-----|
| 0 | 4 | Input Voltage | float |
| 4 | 4 | Set Voltage | float |
| 8 | 4 | Set Current | float |
| 12 | 4 | Output Voltage | float |
| 16 | 4 | Output Current | float |
| 20 | 4 | Output Power | float |
| 24 | 4 | Temperature | float |
| 28 | 4 | Preset 1 Voltage | float |
| 32 | 4 | Preset 1 Current | float |
| 36 | 4 | Preset 2 Voltage | float |
| 40 | 4 | Preset 2 Current | float |
| 44 | 4 | Preset 3 Voltage | float |
| 48 | 4 | Preset 3 Current | float |
| 52 | 4 | Preset 4 Voltage | float |
| 56 | 4 | Preset 4 Current | float |
| 60 | 4 | Preset 5 Voltage | float |
| 64 | 4 | Preset 5 Current | float |
| 68 | 4 | Preset 6 Voltage | float |
| 72 | 4 | Preset 6 Current | float |
| 76 | 4 | Max Voltage | float |
| 80 | 4 | Max Current | float |
| 84 | 4 | OPP Limit | float |
| 88 | 4 | OVP Limit | float |
| 92 | 4 | OCP Limit | float |
| 96-103 | 8 | Capacity (Ah, Wh) | float×2 |
| 107 | 1 | Output Enabled | byte (0=OFF, 1=ON) |
| 108 | 1 | Mode (CV/CC) | byte (0=CV, 1=CC) |
| 109 | 1 | Protection Status | byte |

---

## Коды защит / Protection Codes

| Код | Имя | Описание RU | Description EN |
|-----|-----|-------------|----------------|
| 0 | OK | Нет защиты | No protection |
| 1 | OVP | Защита от перенапряжения | Over Voltage Protection |
| 2 | OCP | Защита от перегрузки по току | Over Current Protection |
| 3 | OPP | Защита от перегрузки по мощности | Over Power Protection |
| 4 | OTP | Защита от перегрева | Over Temperature Protection |
| 5 | SCP | Защита от короткого замыкания | Short Circuit Protection |

---

## Режимы работы / Operating Modes

| Код | Режим | Описание |
|-----|-------|----------|
| 0 | CV | Constant Voltage (Стабилизация напряжения) |
| 1 | CC | Constant Current (Стабилизация тока) |

---

## Временные параметры / Timing

| Параметр | Значение |
|----------|----------|
| Таймаут ответа | 100-500 мс |
| Интервал опроса | 100-200 мс |
| Задержка после подключения | 500 мс |

---

## Диаграмма последовательности / Sequence Diagram

```
Host                          Device
 │                              │
 │  ──── CONNECT ───────────▶  │  Установить соединение
 │  ◀─── ACK ───────────────   │
 │                              │
 │  ──── READ_ALL ──────────▶  │  Запрос всех параметров
 │  ◀─── DATA (0xFF) ───────   │  Ответ с полным дампом
 │                              │
 │  ──── SET_VOLTAGE ───────▶  │  Установить напряжение
 │  ◀─── ACK ───────────────   │
 │                              │
 │  ──── SET_CURRENT ───────▶  │  Установить ток
 │  ◀─── ACK ───────────────   │
 │                              │
 │  ──── OUTPUT_ON ─────────▶  │  Включить выход
 │  ◀─── ACK ───────────────   │
 │                              │
 │  ──── READ_LIVE ─────────▶  │  Опрос измерений
 │  ◀─── DATA (0xC3) ───────   │  V, A, W
 │                              │
 │  ──── OUTPUT_OFF ────────▶  │  Выключить выход
 │  ◀─── ACK ───────────────   │
 │                              │
 │  ──── DISCONNECT ────────▶  │  Завершить соединение
 │  ◀─── ACK ───────────────   │
 │                              │
```

---

## Пример сессии / Session Example

```
# Подключение
TX: F1 C1 00 01 01 02
RX: F0 C1 00 01 01 02

# Чтение всех параметров
TX: F1 A1 FF 01 00 00
RX: F0 A1 FF 8C [136 bytes data] [checksum]

# Установить 5V
TX: F1 B0 C0 04 00 00 A0 40 A4
RX: F0 B0 C0 04 00 00 A0 40 A4

# Установить 1A
TX: F1 B0 DE 04 00 00 80 3F 61
RX: F0 B0 DE 04 00 00 80 3F 61

# Включить выход
TX: F1 B1 DB 01 01 DD
RX: F0 B1 DB 01 01 DD

# Чтение измерений
TX: F1 A1 C3 01 00 C4
RX: F0 A1 C3 0C [V:4bytes] [A:4bytes] [W:4bytes] [checksum]

# Выключить выход
TX: F1 B1 DB 01 00 DC
RX: F0 B1 DB 01 00 DC

# Отключение
TX: F1 C1 00 01 00 01
RX: F0 C1 00 01 00 01
```

---

## Примечания / Notes

1. **Порядок байт:** Все многобайтовые значения передаются в формате little-endian.

2. **OUTPUT_STATE:** 0x01 = ВКЛ, 0x00 = ВЫКЛ.

3. **Регистр 0xDE:** Имеет двойное назначение — запись тока и чтение модели устройства.

4. **Буферизация:** При быстрой отправке команд возможна потеря данных. Рекомендуется делать паузу 50-100мс между командами.

5. **Checksum не включает:** Header и CmdType в расчёт контрольной суммы не входят.

---

## License

Copyright (c) 2024-2026 **ALEXGAVS**

Использование данной документации без указания авторства **ALEXGAVS** запрещено.

Use of this documentation without attribution to **ALEXGAVS** is prohibited.
