# FNIRSI Power Supply Python Library

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Custom-red.svg)](#license)

## Описание / Description

**RU:** Полная Python-библиотека для управления лабораторными источниками питания FNIRSI через USB/Serial интерфейс.

**EN:** Complete Python library for controlling FNIRSI laboratory power supplies via USB/Serial interface.

## Возможности / Features

- 🔌 Подключение и управление через COM-порт
- ⚡ Установка напряжения и тока
- 📊 Мониторинг в реальном времени (V, A, W, температура)
- 🎛️ Включение/выключение выхода
- 🛡️ Отображение статуса защит (OVP, OCP, OPP, OTP, SCP)
- 📈 Отслеживание ёмкости (Ah, Wh)
- 💻 Интерактивный CLI интерфейс
- 🔧 Низкоуровневый доступ к протоколу

## Поддерживаемые устройства / Supported Devices

- FNIRSI DPS-150 / FNB58
- Другие модели FNIRSI с аналогичным протоколом

## Установка / Installation

```bash
# Клонировать репозиторий
git clone https://github.com/ALEXGAVS/fnirsi-python.git
cd fnirsi-python

# Установить зависимости
pip install pyserial
```

## Использование / Usage

### Быстрый старт / Quick Start

```python
from controller import FnirsiController

# Создать контроллер и подключиться
psu = FnirsiController()
psu.connect("COM11")

# Установить напряжение и ток
psu.set_voltage(5.0)
psu.set_current(1.0)

# Включить выход
psu.output_on()

# Получить текущие значения
print(f"Voltage: {psu.state.output_voltage} V")
print(f"Current: {psu.state.output_current} A")
print(f"Power: {psu.state.output_power} W")

# Выключить выход
psu.output_off()

# Отключиться
psu.disconnect()
```

### CLI Интерфейс / CLI Interface

```bash
python cli.py
```

Команды CLI:
- `v <V>` - Установить напряжение (например: `v 5.0`)
- `a <A>` - Установить ток (например: `a 1.0`)
- `on` - Включить выход
- `off` - Выключить выход
- `r` - Обновить данные
- `m` - Мониторинг (5 сек)
- `q` - Выход

## Протокол / Protocol

Формат пакета:
```
Request:  [0xF1] [CmdType] [Register] [Length] [Data...] [Checksum]
Response: [0xF0] [CmdType] [Register] [Length] [Data...] [Checksum]

Checksum = (register + length + sum(data)) & 0xFF
```

Данные передаются в формате IEEE 754 float (little-endian, 4 байта).

📖 **Подробная документация протокола:** [PROTOCOL.md](PROTOCOL.md)

## Структура проекта / Project Structure

| Файл | Описание |
|------|----------|
| `fnirsi.py` | Основная библиотека / Main library |
| `controller.py` | Высокоуровневый контроллер / High-level controller |
| `protocol.py` | Реализация протокола / Protocol implementation |
| `cli.py` | Интерактивный CLI / Interactive CLI |
| `serial_port.py` | Работа с COM-портом / COM port handling |
| `scan_ports.py` | Сканирование портов / Port scanning |
| `examples.py` | Примеры использования / Usage examples |

## Требования / Requirements

- Python 3.7+
- pyserial

## Автор / Author

**ALEXGAVS** - [GitHub](https://github.com/ALEXGAVS)

---

## License

### CUSTOM LICENSE - ATTRIBUTION REQUIRED

Copyright (c) 2024-2026 **ALEXGAVS**

Настоящим предоставляется разрешение любому лицу, получившему копию данного программного обеспечения и сопутствующей документации (далее — «Программное обеспечение»), использовать Программное обеспечение **ТОЛЬКО** при соблюдении следующих условий:

1. **ОБЯЗАТЕЛЬНОЕ УКАЗАНИЕ АВТОРСТВА**: При любом использовании, копировании, модификации, объединении, публикации, распространении, сублицензировании и/или продаже копий Программного обеспечения **ОБЯЗАТЕЛЬНО** должна быть сохранена ссылка на оригинального автора **ALEXGAVS** в виде:
   - Упоминания в исходном коде
   - Упоминания в документации
   - Упоминания в пользовательском интерфейсе (если применимо)

2. **ЗАПРЕТ НА УДАЛЕНИЕ АВТОРСТВА**: Удаление, сокрытие или изменение информации об авторе **ALEXGAVS** категорически запрещено.

3. **ПРОИЗВОДНЫЕ РАБОТЫ**: Любые производные работы должны также содержать указание на оригинального автора **ALEXGAVS** и ссылку на данный репозиторий.

4. **КОММЕРЧЕСКОЕ ИСПОЛЬЗОВАНИЕ**: Коммерческое использование разрешено только при явном указании авторства **ALEXGAVS**.

---

Permission is hereby granted to any person obtaining a copy of this software and associated documentation files (the "Software"), to use the Software **ONLY** under the following conditions:

1. **MANDATORY ATTRIBUTION**: Any use, copying, modification, merging, publishing, distribution, sublicensing, and/or selling of copies of the Software **MUST** include a reference to the original author **ALEXGAVS** in the form of:
   - Mention in source code
   - Mention in documentation
   - Mention in user interface (if applicable)

2. **PROHIBITION OF ATTRIBUTION REMOVAL**: Removal, concealment, or alteration of author information **ALEXGAVS** is strictly prohibited.

3. **DERIVATIVE WORKS**: Any derivative works must also contain attribution to the original author **ALEXGAVS** and a link to this repository.

4. **COMMERCIAL USE**: Commercial use is permitted only with explicit attribution to **ALEXGAVS**.

---

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

---

⚠️ **ИСПОЛЬЗОВАНИЕ ДАННОГО КОДА БЕЗ УКАЗАНИЯ АВТОРСТВА ALEXGAVS ЗАПРЕЩЕНО!**

⚠️ **USE OF THIS CODE WITHOUT ATTRIBUTION TO ALEXGAVS IS PROHIBITED!**
