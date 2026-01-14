# FNIRSI Power Supply Python Library

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Описание / Description

**RU:** Полная Python-библиотека для управления лабораторными источниками питания FNIRSI через USB/Serial интерфейс.

**EN:** Complete Python library for controlling FNIRSI laboratory power supplies via USB/Serial interface.

---

### 📸 Скриншоты / Screenshots

#### Главное окно / Main Window
![FNIRSI GUI - Main Window](docs/screenshot-main-ru.png)
*Графический интерфейс с графиками в реальном времени и управлением*

*Graphical interface with real-time charts and controls*

#### Настройки / Settings
![FNIRSI GUI - Settings Dialog](docs/screenshot-settings-ru.png)
*Диалог настроек с выбором языка (English/Русский)*

*Settings dialog with language selection (English/Russian)*

---

## Возможности / Features

- 🔌 Подключение и управление через COM-порт
- ⚡ Установка напряжения и тока
- 📊 Мониторинг в реальном времени (V, A, W, температура)
- 🎛️ Включение/выключение выхода
- 🛡️ Отображение статуса защит (OVP, OCP, OPP, OTP, SCP)
- 📈 Отслеживание ёмкости (Ah, Wh)
- 🖥️ Графический интерфейс (GUI) с графиками в реальном времени
- 💻 Интерактивный CLI интерфейс
- 🌍 **Мультиязычность** (English, Русский) с возможностью редактирования переводов
- 🔧 Низкоуровневый доступ к протоколу

## Поддерживаемые устройства / Supported Devices

- **FNIRSI IPS3608** (36V / 8.2A) — протестировано / tested ✓
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

### 🖥️ Графический интерфейс / GUI

```bash
pip install matplotlib
python gui.py
```

Возможности GUI:
- 📊 **Графики в реальном времени** — напряжение, ток, мощность, температура
- 🎚️ **Слайдеры** для быстрой настройки V/A
- ⚡ **Настраиваемые пресеты** — сетка 3×3, ЛКМ применить / ПКМ настроить
- 🔆 **Яркость дисплея** — настройка 0-20
- 💾 **Запись данных** — экспорт в CSV
- 📸 **Скриншоты графиков** — сохранение в PNG
- ⚙️ **Настройки** — порт, скорость, защиты, интервал обновления

## Протокол / Protocol

Формат пакета:
```
Request:  [0xF1] [CmdType] [Register] [Length] [Data...] [Checksum]
Response: [0xF0] [CmdType] [Register] [Length] [Data...] [Checksum]

Checksum = (register + length + sum(data)) & 0xFF
```

Данные передаются в формате IEEE 754 float (little-endian, 4 байта).

📖 **Подробная документация протокола:** [PROTOCOL.md](PROTOCOL.md)

## Мультиязычность / Multi-language Support

Приложение поддерживает несколько языков с возможностью редактирования пользователем.

The application supports multiple languages with user-editable translations.

**Доступные языки / Available languages:**
- 🇬🇧 English (по умолчанию / default)
- 🇷🇺 Русский

**Смена языка / Changing language:**
1. Откройте GUI → **Tools → Settings** → **Interface** → **Language**
2. Выберите язык / Select language
3. Перезапустите приложение / Restart application

**Редактирование переводов / Editing translations:**

Файлы переводов находятся в папке `lang/`:
- `lang/en.json` - English
- `lang/ru.json` - Русский

Вы можете редактировать эти JSON файлы для настройки текста интерфейса.

You can edit these JSON files to customize interface text.

📖 **Подробная инструкция:** [lang/README.md](lang/README.md)

## Структура проекта / Project Structure

| Файл | Описание |
|------|----------|
| `fnirsi.py` | Основная библиотека / Main library |
| `controller.py` | Высокоуровневый контроллер / High-level controller |
| `protocol.py` | Реализация протокола / Protocol implementation |
| `gui.py` | 🖥️ Графический интерфейс с графиками / GUI with charts |
| `cli.py` | Интерактивный CLI / Interactive CLI |
| `language_manager.py` | 🌍 Менеджер переводов / Translation manager |
| `serial_port.py` | Работа с COM-портом / COM port handling |
| `config.json` | ⚙️ Конфигурация и пресеты / Config and presets |
| `lang/` | 📁 Языковые файлы / Language files |
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

Данное программное обеспечение распространяется под лицензией MIT с требованием указания авторства.

This software is distributed under the MIT License with attribution requirement.

**Основные положения / Key Points:**

1. ✅ Свободное использование, модификация, распространение
2. ✅ Коммерческое использование разрешено
3. ✅ Создание производных работ разрешено
4. 📋 Необходимо сохранять уведомление об авторских правах
5. 📋 Рекомендуется указывать ссылку на оригинального автора

**Полный текст лицензии:** [LICENSE](LICENSE)

---

**Original Author / Оригинальный автор:** ALEXGAVS
