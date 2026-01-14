"""
FNIRSI Power Supply - Graphical User Interface
===============================================
Графический интерфейс для управления блоком питания FNIRSI
с графиками в реальном времени и расширенными настройками.

Author: ALEXGAVS
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import csv
from datetime import datetime
from collections import deque
from typing import Optional, List, Tuple
import serial.tools.list_ports

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.animation import FuncAnimation
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not installed. Charts will be disabled.")

from controller import FnirsiController, PowerSupplyState
from language_manager import LanguageManager


class ChartData:
    """Хранение данных для графиков"""
    
    def __init__(self, max_points: int = 300):
        self.max_points = max_points
        self.time_data: deque = deque(maxlen=max_points)
        self.voltage_data: deque = deque(maxlen=max_points)
        self.current_data: deque = deque(maxlen=max_points)
        self.power_data: deque = deque(maxlen=max_points)
        self.temperature_data: deque = deque(maxlen=max_points)
        self.start_time = time.time()
    
    def add_point(self, voltage: float, current: float, power: float, temperature: float):
        elapsed = time.time() - self.start_time
        self.time_data.append(elapsed)
        self.voltage_data.append(voltage)
        self.current_data.append(current)
        self.power_data.append(power)
        self.temperature_data.append(temperature)
    
    def clear(self):
        self.time_data.clear()
        self.voltage_data.clear()
        self.current_data.clear()
        self.power_data.clear()
        self.temperature_data.clear()
        self.start_time = time.time()
    
    def get_data(self) -> dict:
        return {
            'time': list(self.time_data),
            'voltage': list(self.voltage_data),
            'current': list(self.current_data),
            'power': list(self.power_data),
            'temperature': list(self.temperature_data)
        }


class SettingsDialog(tk.Toplevel):
    """Диалог настроек"""

    def __init__(self, parent, settings: dict, lang: LanguageManager):
        super().__init__(parent)
        self.lang = lang
        self.title(lang.t("settings_dialog.title"))
        self.geometry("400x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.settings = settings.copy()
        self.result = None

        self._create_widgets()
        self._center_window()
    
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка "Соединение"
        conn_frame = ttk.Frame(notebook, padding=10)
        notebook.add(conn_frame, text=self.lang.t("settings_dialog.connection_tab"))

        ttk.Label(conn_frame, text=self.lang.t("settings_dialog.baud_rate")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.baud_var = tk.StringVar(value=str(self.settings.get('baud_rate', 9600)))
        baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var,
                                   values=['9600', '19200', '38400', '57600', '115200'])
        baud_combo.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(conn_frame, text=self.lang.t("settings_dialog.timeout")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.StringVar(value=str(self.settings.get('timeout', 2.0)))
        ttk.Entry(conn_frame, textvariable=self.timeout_var).grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(conn_frame, text=self.lang.t("settings_dialog.auto_reconnect")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.auto_reconnect_var = tk.BooleanVar(value=self.settings.get('auto_reconnect', True))
        ttk.Checkbutton(conn_frame, variable=self.auto_reconnect_var).grid(row=2, column=1, sticky=tk.W, pady=5)

        conn_frame.columnconfigure(1, weight=1)

        # Вкладка "Графики"
        chart_frame = ttk.Frame(notebook, padding=10)
        notebook.add(chart_frame, text=self.lang.t("settings_dialog.charts_tab"))

        ttk.Label(chart_frame, text=self.lang.t("settings_dialog.max_points")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_points_var = tk.StringVar(value=str(self.settings.get('max_chart_points', 300)))
        ttk.Entry(chart_frame, textvariable=self.max_points_var).grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(chart_frame, text=self.lang.t("settings_dialog.update_interval")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.update_interval_var = tk.StringVar(value=str(self.settings.get('update_interval', 200)))
        ttk.Entry(chart_frame, textvariable=self.update_interval_var).grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(chart_frame, text=self.lang.t("settings_dialog.show_grid")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.show_grid_var = tk.BooleanVar(value=self.settings.get('show_grid', True))
        ttk.Checkbutton(chart_frame, variable=self.show_grid_var).grid(row=2, column=1, sticky=tk.W, pady=5)

        chart_frame.columnconfigure(1, weight=1)

        # Вкладка "Защиты"
        protection_frame = ttk.Frame(notebook, padding=10)
        notebook.add(protection_frame, text=self.lang.t("settings_dialog.protection_tab"))

        ttk.Label(protection_frame, text=self.lang.t("settings_dialog.ovp")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ovp_var = tk.StringVar(value=str(self.settings.get('ovp_limit', 0)))
        ttk.Entry(protection_frame, textvariable=self.ovp_var).grid(row=0, column=1, sticky=tk.EW, pady=5)
        ttk.Label(protection_frame, text="V").grid(row=0, column=2, padx=5)

        ttk.Label(protection_frame, text=self.lang.t("settings_dialog.ocp")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ocp_var = tk.StringVar(value=str(self.settings.get('ocp_limit', 0)))
        ttk.Entry(protection_frame, textvariable=self.ocp_var).grid(row=1, column=1, sticky=tk.EW, pady=5)
        ttk.Label(protection_frame, text="A").grid(row=1, column=2, padx=5)

        ttk.Label(protection_frame, text=self.lang.t("settings_dialog.opp")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.opp_var = tk.StringVar(value=str(self.settings.get('opp_limit', 0)))
        ttk.Entry(protection_frame, textvariable=self.opp_var).grid(row=2, column=1, sticky=tk.EW, pady=5)
        ttk.Label(protection_frame, text="W").grid(row=2, column=2, padx=5)

        protection_frame.columnconfigure(1, weight=1)

        # Вкладка "Интерфейс"
        ui_frame = ttk.Frame(notebook, padding=10)
        notebook.add(ui_frame, text=self.lang.t("settings_dialog.interface_tab"))

        ttk.Label(ui_frame, text=self.lang.t("settings_dialog.theme")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.theme_var = tk.StringVar(value=self.settings.get('theme', 'default'))
        theme_combo = ttk.Combobox(ui_frame, textvariable=self.theme_var,
                                    values=['default', 'clam', 'alt', 'classic'])
        theme_combo.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(ui_frame, text=self.lang.t("settings_dialog.language")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.lang_var = tk.StringVar(value=self.settings.get('language', 'en'))
        lang_combo = ttk.Combobox(ui_frame, textvariable=self.lang_var,
                                   values=['en', 'ru'])
        lang_combo.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ui_frame.columnconfigure(1, weight=1)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text=self.lang.t("settings_dialog.cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text=self.lang.t("settings_dialog.save"), command=self._save).pack(side=tk.RIGHT, padx=5)
    
    def _save(self):
        try:
            self.result = {
                'baud_rate': int(self.baud_var.get()),
                'timeout': float(self.timeout_var.get()),
                'auto_reconnect': self.auto_reconnect_var.get(),
                'max_chart_points': int(self.max_points_var.get()),
                'update_interval': int(self.update_interval_var.get()),
                'show_grid': self.show_grid_var.get(),
                'ovp_limit': float(self.ovp_var.get()),
                'ocp_limit': float(self.ocp_var.get()),
                'opp_limit': float(self.opp_var.get()),
                'theme': self.theme_var.get(),
                'language': self.lang_var.get()
            }
            self.destroy()
        except ValueError as e:
            messagebox.showerror(self.lang.t("messages.error"), self.lang.t("messages.invalid_value", error=str(e)))


class FnirsiGUI:
    """Главное окно приложения"""
    
    CONFIG_FILE = "fnirsi_gui_config.json"
    
    def __init__(self):
        self.root = tk.Tk()

        # Настройки
        self.settings = self._load_settings()

        # Language manager - английский по умолчанию
        self.lang = LanguageManager(self.settings.get('language', 'en'))

        self.root.title(self.lang.t("app_title"))
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)

        # Контроллер
        self.psu = FnirsiController()
        self.connected = False

        # Данные для графиков
        self.chart_data = ChartData()
        self.recording = False
        self.recorded_data: List[dict] = []

        # Применить тему
        style = ttk.Style()
        try:
            style.theme_use(self.settings.get('theme', 'default'))
        except:
            pass

        # Переменные
        self._create_variables()

        # UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()

        # Таймер обновления
        self._update_job = None
        self._start_update_loop()

        # Обработчик закрытия
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _load_settings(self) -> dict:
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {
                'baud_rate': 9600,
                'timeout': 2.0,
                'auto_reconnect': True,
                'max_chart_points': 300,
                'update_interval': 200,
                'show_grid': True,
                'ovp_limit': 0,
                'ocp_limit': 0,
                'opp_limit': 0,
                'theme': 'default',
                'language': 'en',  # Английский по умолчанию
                'last_port': ''
            }
    
    def _save_settings(self):
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _create_variables(self):
        self.port_var = tk.StringVar(value=self.settings.get('last_port', ''))
        self.voltage_set_var = tk.StringVar(value="0.00")
        self.current_set_var = tk.StringVar(value="0.000")
        self.voltage_read_var = tk.StringVar(value="0.0000 V")
        self.current_read_var = tk.StringVar(value="0.00000 A")
        self.power_read_var = tk.StringVar(value="0.000 W")
        self.temperature_var = tk.StringVar(value="0.0 °C")
        self.capacity_ah_var = tk.StringVar(value="0.000 Ah")
        self.capacity_wh_var = tk.StringVar(value="0.000 Wh")
        self.mode_var = tk.StringVar(value="--")
        self.protection_var = tk.StringVar(value="OK")
        self.output_var = tk.BooleanVar(value=False)
        self.model_var = tk.StringVar(value="--")
        self.firmware_var = tk.StringVar(value="--")
        
        # Флаг редактирования - предотвращает сброс значений при вводе
        self._user_editing = False

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang.t("menu.file"), menu=file_menu)
        file_menu.add_command(label=self.lang.t("menu.export_data"), command=self._export_data)
        file_menu.add_command(label=self.lang.t("menu.save_screenshot"), command=self._save_screenshot)
        file_menu.add_separator()
        file_menu.add_command(label=self.lang.t("menu.exit"), command=self._on_close)

        # Соединение
        conn_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang.t("menu.connection"), menu=conn_menu)
        conn_menu.add_command(label=self.lang.t("menu.connect"), command=self._connect)
        conn_menu.add_command(label=self.lang.t("menu.disconnect"), command=self._disconnect)
        conn_menu.add_separator()
        conn_menu.add_command(label=self.lang.t("menu.refresh_ports"), command=self._refresh_ports)

        # Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang.t("menu.tools"), menu=tools_menu)
        tools_menu.add_command(label=self.lang.t("menu.clear_charts"), command=self._clear_charts)
        tools_menu.add_checkbutton(label=self.lang.t("menu.data_recording"), command=self._toggle_recording)
        tools_menu.add_separator()
        tools_menu.add_command(label=self.lang.t("menu.settings"), command=self._show_settings)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang.t("menu.help"), menu=help_menu)
        help_menu.add_command(label=self.lang.t("menu.about"), command=self._show_about)
    
    def _create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Выбор порта
        ttk.Label(toolbar, text=self.lang.t("toolbar.port")).pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(toolbar, textvariable=self.port_var, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        self._refresh_ports()

        # Кнопки подключения
        self.connect_btn = ttk.Button(toolbar, text=self.lang.t("toolbar.connect"), command=self._connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(toolbar, text=self.lang.t("toolbar.disconnect"), command=self._disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Индикатор статуса
        self.status_indicator = tk.Canvas(toolbar, width=20, height=20)
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        self._update_status_indicator(False)

        ttk.Label(toolbar, textvariable=self.model_var).pack(side=tk.LEFT, padx=5)
    
    def _create_main_layout(self):
        # Главный контейнер с панелями
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - управление
        left_frame = ttk.Frame(paned, width=350)
        paned.add(left_frame, weight=0)
        
        self._create_control_panel(left_frame)
        self._create_readings_panel(left_frame)
        self._create_presets_panel(left_frame)
        
        # Правая панель - графики
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        self._create_charts_panel(right_frame)
    
    def _create_control_panel(self, parent):
        frame = ttk.LabelFrame(parent, text=self.lang.t("control_panel.title"), padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        # Напряжение
        v_frame = ttk.Frame(frame)
        v_frame.pack(fill=tk.X, pady=3)

        ttk.Label(v_frame, text=self.lang.t("control_panel.voltage"), width=15).pack(side=tk.LEFT)
        self.voltage_spinbox = ttk.Spinbox(v_frame, textvariable=self.voltage_set_var,
                                            from_=0, to=60, increment=0.1, width=8,
                                            command=self._on_voltage_spinbox)
        self.voltage_spinbox.pack(side=tk.LEFT, padx=5)
        self.voltage_spinbox.bind('<FocusIn>', self._on_entry_focus_in)
        self.voltage_spinbox.bind('<FocusOut>', self._on_entry_focus_out)
        self.voltage_spinbox.bind('<Return>', lambda e: self._set_voltage())
        ttk.Button(v_frame, text=self.lang.t("control_panel.set_button"), command=self._set_voltage, width=5).pack(side=tk.LEFT)

        # Ползунок напряжения
        v_scale_frame = ttk.Frame(frame)
        v_scale_frame.pack(fill=tk.X, pady=2)
        self.voltage_scale = ttk.Scale(v_scale_frame, from_=0, to=36, orient=tk.HORIZONTAL,
                                        command=self._on_voltage_scale)
        self.voltage_scale.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.voltage_scale.bind('<ButtonPress-1>', self._on_scale_press)
        self.voltage_scale.bind('<ButtonRelease-1>', self._on_scale_release_voltage)

        # Ток
        a_frame = ttk.Frame(frame)
        a_frame.pack(fill=tk.X, pady=3)

        ttk.Label(a_frame, text=self.lang.t("control_panel.current"), width=15).pack(side=tk.LEFT)
        self.current_spinbox = ttk.Spinbox(a_frame, textvariable=self.current_set_var,
                                            from_=0, to=20, increment=0.1, width=8,
                                            command=self._on_current_spinbox)
        self.current_spinbox.pack(side=tk.LEFT, padx=5)
        self.current_spinbox.bind('<FocusIn>', self._on_entry_focus_in)
        self.current_spinbox.bind('<FocusOut>', self._on_entry_focus_out)
        self.current_spinbox.bind('<Return>', lambda e: self._set_current())
        ttk.Button(a_frame, text=self.lang.t("control_panel.set_button"), command=self._set_current, width=5).pack(side=tk.LEFT)

        # Ползунок тока
        a_scale_frame = ttk.Frame(frame)
        a_scale_frame.pack(fill=tk.X, pady=2)
        self.current_scale = ttk.Scale(a_scale_frame, from_=0, to=10, orient=tk.HORIZONTAL,
                                        command=self._on_current_scale)
        self.current_scale.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.current_scale.bind('<ButtonPress-1>', self._on_scale_press)
        self.current_scale.bind('<ButtonRelease-1>', self._on_scale_release_current)

        # Кнопка выхода
        self.output_btn = tk.Button(frame, text=self.lang.t("control_panel.output_off"), bg="#cc0000", fg="white",
                                     font=("Arial", 14, "bold"), height=2,
                                     command=self._toggle_output)
        self.output_btn.pack(fill=tk.X, pady=10)
    
    def _create_readings_panel(self, parent):
        frame = ttk.LabelFrame(parent, text=self.lang.t("readings_panel.title"), padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        # Большие цифры для V, A, W
        readings_frame = ttk.Frame(frame)
        readings_frame.pack(fill=tk.X)

        # Напряжение
        v_label = ttk.Label(readings_frame, textvariable=self.voltage_read_var,
                            font=("Courier", 24, "bold"), foreground="#00aa00")
        v_label.pack(fill=tk.X)

        # Ток
        a_label = ttk.Label(readings_frame, textvariable=self.current_read_var,
                            font=("Courier", 24, "bold"), foreground="#0066cc")
        a_label.pack(fill=tk.X)

        # Мощность
        w_label = ttk.Label(readings_frame, textvariable=self.power_read_var,
                            font=("Courier", 24, "bold"), foreground="#cc6600")
        w_label.pack(fill=tk.X)

        # Дополнительная информация
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=10)

        ttk.Label(info_frame, text=self.lang.t("readings_panel.temperature")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.temperature_var).grid(row=0, column=1, sticky=tk.E)

        ttk.Label(info_frame, text=self.lang.t("readings_panel.capacity")).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.capacity_ah_var).grid(row=1, column=1, sticky=tk.E)

        ttk.Label(info_frame, text=self.lang.t("readings_panel.energy")).grid(row=2, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.capacity_wh_var).grid(row=2, column=1, sticky=tk.E)

        ttk.Label(info_frame, text=self.lang.t("readings_panel.mode")).grid(row=3, column=0, sticky=tk.W)
        self.mode_label = ttk.Label(info_frame, textvariable=self.mode_var, font=("Arial", 10, "bold"))
        self.mode_label.grid(row=3, column=1, sticky=tk.E)

        ttk.Label(info_frame, text=self.lang.t("readings_panel.protection")).grid(row=4, column=0, sticky=tk.W)
        self.protection_label = ttk.Label(info_frame, textvariable=self.protection_var,
                                           font=("Arial", 10, "bold"))
        self.protection_label.grid(row=4, column=1, sticky=tk.E)

        info_frame.columnconfigure(1, weight=1)

        # Яркость дисплея (0-35)
        brightness_frame = ttk.LabelFrame(frame, text=self.lang.t("readings_panel.brightness_title"), padding=5)
        brightness_frame.pack(fill=tk.X, pady=5)

        self.brightness_var = tk.IntVar(value=20)
        self.brightness_spinbox = ttk.Spinbox(brightness_frame, from_=0, to=20,
                                               textvariable=self.brightness_var,
                                               width=5, command=self._on_brightness_change)
        self.brightness_spinbox.pack(side=tk.LEFT, padx=5)
        self.brightness_spinbox.bind('<Return>', lambda e: self._on_brightness_change())

        ttk.Label(brightness_frame, text=self.lang.t("readings_panel.brightness_range")).pack(side=tk.LEFT)
    
    def _create_presets_panel(self, parent):
        frame = ttk.LabelFrame(parent, text=self.lang.t("presets_panel.title"), padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        # Загрузка пресетов из конфига
        self.preset_buttons = []
        default_presets = [
            {"name": "1.2V/1A", "voltage": 1.2, "current": 1.0},
            {"name": "1.8V/1A", "voltage": 1.8, "current": 1.0},
            {"name": "3.3V/2A", "voltage": 3.3, "current": 2.0},
            {"name": "4.2V/1A", "voltage": 4.2, "current": 1.0},
            {"name": "5V/3A", "voltage": 5.0, "current": 3.0},
            {"name": "12V/5A", "voltage": 12.0, "current": 5.0},
            {"name": "14V/5A", "voltage": 14.0, "current": 5.0},
            {"name": "16.8V/5A", "voltage": 16.8, "current": 5.0},
            {"name": "24V/8A", "voltage": 24.0, "current": 8.0},
        ]

        self.presets = self.settings.get('presets', default_presets)
        # Убедимся что 9 пресетов
        while len(self.presets) < 9:
            idx = len(self.presets) + 1
            self.presets.append({"name": f"P{idx}", "voltage": 5.0, "current": 1.0})

        # Создание кнопок 3x3
        for i in range(9):
            row, col = divmod(i, 3)
            preset = self.presets[i]
            btn = ttk.Button(frame, text=preset.get('name', f'{preset["voltage"]}V/{preset["current"]}A'),
                            width=10)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            btn.bind('<Button-1>', lambda e, idx=i: self._apply_preset_by_index(idx))
            btn.bind('<Button-3>', lambda e, idx=i: self._edit_preset(idx))
            self.preset_buttons.append(btn)

        # Подсказка
        ttk.Label(frame, text=self.lang.t("presets_panel.hint"),
                 font=("Arial", 8)).grid(row=3, column=0, columnspan=3, pady=(5,0))
    
    def _apply_preset_by_index(self, idx: int):
        """Применить пресет по индексу."""
        if 0 <= idx < len(self.presets):
            preset = self.presets[idx]
            self._apply_preset(preset['voltage'], preset['current'])
    
    def _edit_preset(self, idx: int):
        """Редактировать пресет."""
        if idx < 0 or idx >= len(self.presets):
            return

        preset = self.presets[idx]

        # Диалоговое окно редактирования
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{self.lang.t('presets_panel.edit_title')} {idx + 1}")
        dialog.geometry("280x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрирование
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 280) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Название
        ttk.Label(main_frame, text=self.lang.t("presets_panel.name")).grid(row=0, column=0, sticky='w', pady=5)
        name_var = tk.StringVar(value=preset.get('name', ''))
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=15)
        name_entry.grid(row=0, column=1, sticky='ew', pady=5)

        # Напряжение
        ttk.Label(main_frame, text=self.lang.t("presets_panel.voltage")).grid(row=1, column=0, sticky='w', pady=5)
        voltage_var = tk.DoubleVar(value=preset['voltage'])
        voltage_spin = ttk.Spinbox(main_frame, from_=0, to=36, increment=0.1,
                                   textvariable=voltage_var, width=10)
        voltage_spin.grid(row=1, column=1, sticky='ew', pady=5)

        # Ток
        ttk.Label(main_frame, text=self.lang.t("presets_panel.current")).grid(row=2, column=0, sticky='w', pady=5)
        current_var = tk.DoubleVar(value=preset['current'])
        current_spin = ttk.Spinbox(main_frame, from_=0, to=10, increment=0.1,
                                   textvariable=current_var, width=10)
        current_spin.grid(row=2, column=1, sticky='ew', pady=5)

        def save_preset():
            self.presets[idx] = {
                'name': name_var.get() or f'{voltage_var.get():.1f}V/{current_var.get():.1f}A',
                'voltage': voltage_var.get(),
                'current': current_var.get()
            }
            # Обновить кнопку
            self.preset_buttons[idx].config(text=self.presets[idx]['name'])
            # Сохранить в конфиг
            self.settings['presets'] = self.presets
            self._save_settings()
            dialog.destroy()

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text=self.lang.t("presets_panel.save"), command=save_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=self.lang.t("presets_panel.cancel"), command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _create_charts_panel(self, parent):
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text=self.lang.t("matplotlib_warning"),
                     font=("Arial", 14)).pack(expand=True)
            return
        
        # Создание фигуры с подграфиками
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.fig.set_facecolor('#f0f0f0')
        
        # 4 графика: V, A, W, Temperature
        self.ax_voltage = self.fig.add_subplot(411)
        self.ax_current = self.fig.add_subplot(412)
        self.ax_power = self.fig.add_subplot(413)
        self.ax_temp = self.fig.add_subplot(414)
        
        # Настройка графиков
        for ax, label_key, color in [
            (self.ax_voltage, "charts.voltage", "#00aa00"),
            (self.ax_current, "charts.current", "#0066cc"),
            (self.ax_power, "charts.power", "#cc6600"),
            (self.ax_temp, "charts.temperature", "#cc0066")
        ]:
            ax.set_ylabel(self.lang.t(label_key), fontsize=9)
            ax.tick_params(labelsize=8)
            ax.grid(self.settings.get('show_grid', True), alpha=0.3)
            ax.set_facecolor('#ffffff')

        self.ax_temp.set_xlabel(self.lang.t("charts.time"), fontsize=9)
        
        self.fig.tight_layout()
        
        # Линии графиков
        self.line_voltage, = self.ax_voltage.plot([], [], '#00aa00', linewidth=1.5)
        self.line_current, = self.ax_current.plot([], [], '#0066cc', linewidth=1.5)
        self.line_power, = self.ax_power.plot([], [], '#cc6600', linewidth=1.5)
        self.line_temp, = self.ax_temp.plot([], [], '#cc0066', linewidth=1.5)
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        
        # Toolbar
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(status_frame, text=self.lang.t("status.ready"), relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.packets_label = ttk.Label(status_frame, text=self.lang.t("status.packets", count=0), width=15, relief=tk.SUNKEN)
        self.packets_label.pack(side=tk.RIGHT)

        self.recording_label = ttk.Label(status_frame, text="", width=10, relief=tk.SUNKEN)
        self.recording_label.pack(side=tk.RIGHT)
    
    def _update_status_indicator(self, connected: bool):
        self.status_indicator.delete("all")
        color = "#00ff00" if connected else "#ff0000"
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline="#333333")
    
    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
    
    def _connect(self):
        port = self.port_var.get()
        if not port:
            messagebox.showwarning(self.lang.t("messages.warning"), self.lang.t("messages.select_port"))
            return

        self.status_label.config(text=self.lang.t("status.connecting", port=port))
        self.root.update()

        baud = self.settings.get('baud_rate', 9600)
        timeout = self.settings.get('timeout', 2.0)

        if self.psu.connect(port, baud, timeout):
            self.connected = True
            self.settings['last_port'] = port
            self._save_settings()

            self._update_status_indicator(True)
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.status_label.config(text=self.lang.t("status.connected", port=port))

            # Обновить лимиты слайдеров
            state = self.psu.state
            if state.max_voltage > 0:
                self.voltage_scale.config(to=state.max_voltage)
            if state.max_current > 0:
                self.current_scale.config(to=state.max_current)

            self.model_var.set(state.model or "FNIRSI")
            self.firmware_var.set(state.firmware)

            self.chart_data.clear()
        else:
            messagebox.showerror(self.lang.t("messages.error"), self.lang.t("messages.connection_failed", port=port))
            self.status_label.config(text=self.lang.t("status.connection_error"))
    
    def _disconnect(self):
        self.psu.disconnect()
        self.connected = False

        self._update_status_indicator(False)
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.status_label.config(text=self.lang.t("status.disconnected"))
        self.model_var.set("--")
    
    def _set_voltage(self):
        try:
            voltage = float(self.voltage_set_var.get())
            if self.connected:
                self.psu.set_voltage(voltage)
                self.voltage_scale.set(voltage)
        except ValueError:
            messagebox.showerror(self.lang.t("messages.error"), self.lang.t("messages.invalid_voltage"))

    def _set_current(self):
        try:
            current = float(self.current_set_var.get())
            if self.connected:
                self.psu.set_current(current)
                self.current_scale.set(current)
        except ValueError:
            messagebox.showerror(self.lang.t("messages.error"), self.lang.t("messages.invalid_current"))
    
    def _on_entry_focus_in(self, event):
        """Начало редактирования - блокируем обновление"""
        self._user_editing = True
    
    def _on_entry_focus_out(self, event):
        """Конец редактирования - разрешаем обновление"""
        self._user_editing = False
    
    def _on_scale_press(self, event):
        """Начало редактирования"""
        self._user_editing = True
    
    def _on_voltage_spinbox(self):
        """Изменение значения напряжения через Spinbox"""
        if self.connected:
            try:
                v = float(self.voltage_set_var.get())
                self.psu.set_voltage(v)
            except ValueError:
                pass
    
    def _on_current_spinbox(self):
        """Изменение значения тока через Spinbox"""
        if self.connected:
            try:
                a = float(self.current_set_var.get())
                self.psu.set_current(a)
            except ValueError:
                pass
    
    def _on_voltage_scale(self, value):
        """Изменение ползунка напряжения"""
        v = float(value)
        self.voltage_set_var.set(f"{v:.2f}")
    
    def _on_current_scale(self, value):
        """Изменение ползунка тока"""
        a = float(value)
        self.current_set_var.set(f"{a:.3f}")
    
    def _on_scale_release_voltage(self, event):
        """Отпускание ползунка напряжения - отправляем значение"""
        self._user_editing = False
        if self.connected:
            try:
                v = float(self.voltage_set_var.get())
                self.psu.set_voltage(v)
            except ValueError:
                pass
    
    def _on_scale_release_current(self, event):
        """Отпускание ползунка тока - отправляем значение"""
        self._user_editing = False
        if self.connected:
            try:
                a = float(self.current_set_var.get())
                self.psu.set_current(a)
            except ValueError:
                pass
    
    def _on_brightness_change(self):
        """Изменение яркости дисплея"""
        if self.connected:
            try:
                level = self.brightness_var.get()
                self.psu.set_brightness(level)
            except (ValueError, tk.TclError):
                pass

    def _toggle_output(self):
        if not self.connected:
            return

        if self.output_var.get():
            self.psu.output_off()
            self.output_var.set(False)
            self.output_btn.config(text=self.lang.t("control_panel.output_off"), bg="#cc0000")
        else:
            self.psu.output_on()
            self.output_var.set(True)
            self.output_btn.config(text=self.lang.t("control_panel.output_on"), bg="#00cc00")
    
    def _apply_preset(self, voltage: float, current: float):
        if self.connected:
            self.psu.set_voltage(voltage)
            self.psu.set_current(current)
            self.voltage_set_var.set(f"{voltage:.2f}")
            self.current_set_var.set(f"{current:.3f}")
            self.voltage_scale.set(voltage)
            self.current_scale.set(current)
    
    def _start_update_loop(self):
        self._update_data()
    
    def _update_data(self):
        if self.connected:
            state = self.psu.state
            
            # Обновить показания
            self.voltage_read_var.set(f"{state.output_voltage:.4f} V")
            self.current_read_var.set(f"{state.output_current:.5f} A")
            self.power_read_var.set(f"{state.output_power:.3f} W")
            self.temperature_var.set(f"{state.temperature:.1f} °C")
            self.capacity_ah_var.set(f"{state.capacity_ah:.3f} Ah")
            self.capacity_wh_var.set(f"{state.capacity_wh:.3f} Wh")
            self.mode_var.set(state.mode_str)
            self.protection_var.set(state.protection_str)
            
            # Обновить уставки только если пользователь не редактирует
            if not self._user_editing:
                if state.set_voltage > 0:
                    self.voltage_set_var.set(f"{state.set_voltage:.2f}")
                    self.voltage_scale.set(state.set_voltage)
                if state.set_current > 0:
                    self.current_set_var.set(f"{state.set_current:.3f}")
                    self.current_scale.set(state.set_current)
            
            # Обновить кнопку выхода
            self.output_var.set(state.output_enabled)
            if state.output_enabled:
                self.output_btn.config(text=self.lang.t("control_panel.output_on"), bg="#00cc00")
            else:
                self.output_btn.config(text=self.lang.t("control_panel.output_off"), bg="#cc0000")

            # Цвет защиты
            if state.protection_str != "OK":
                self.protection_label.config(foreground="red")
            else:
                self.protection_label.config(foreground="green")

            # Добавить точку на график
            self.chart_data.add_point(
                state.output_voltage,
                state.output_current,
                state.output_power,
                state.temperature
            )

            # Запись данных
            if self.recording:
                self.recorded_data.append({
                    'timestamp': datetime.now().isoformat(),
                    'voltage': state.output_voltage,
                    'current': state.output_current,
                    'power': state.output_power,
                    'temperature': state.temperature
                })

            # Обновить счётчик пакетов
            self.packets_label.config(text=self.lang.t("status.packets", count=state.packet_count))
            
            # Обновить графики
            self._update_charts()
            
            # Запросить новые данные
            self.psu.read_all()
        
        # Планировать следующее обновление
        interval = self.settings.get('update_interval', 200)
        self._update_job = self.root.after(interval, self._update_data)
    
    def _update_charts(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        
        data = self.chart_data.get_data()
        if not data['time']:
            return
        
        t = data['time']
        
        # Обновить данные линий
        self.line_voltage.set_data(t, data['voltage'])
        self.line_current.set_data(t, data['current'])
        self.line_power.set_data(t, data['power'])
        self.line_temp.set_data(t, data['temperature'])
        
        # Обновить пределы осей
        for ax, values in [
            (self.ax_voltage, data['voltage']),
            (self.ax_current, data['current']),
            (self.ax_power, data['power']),
            (self.ax_temp, data['temperature'])
        ]:
            ax.set_xlim(min(t), max(t) + 0.1)
            if values:
                min_v, max_v = min(values), max(values)
                margin = (max_v - min_v) * 0.1 + 0.1
                ax.set_ylim(min_v - margin, max_v + margin)
        
        self.canvas.draw_idle()
    
    def _clear_charts(self):
        self.chart_data.clear()
        if MATPLOTLIB_AVAILABLE:
            for line in [self.line_voltage, self.line_current, self.line_power, self.line_temp]:
                line.set_data([], [])
            self.canvas.draw_idle()
    
    def _toggle_recording(self):
        self.recording = not self.recording
        if self.recording:
            self.recorded_data = []
            self.recording_label.config(text=self.lang.t("status.recording"), foreground="red")
        else:
            self.recording_label.config(text="")

    def _export_data(self):
        if not self.recorded_data:
            messagebox.showinfo(self.lang.t("messages.info"), self.lang.t("messages.no_data"))
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'voltage', 'current', 'power', 'temperature'])
                    writer.writeheader()
                    writer.writerows(self.recorded_data)
                messagebox.showinfo(self.lang.t("messages.success"), self.lang.t("messages.export_success", filename=filename))
            except Exception as e:
                messagebox.showerror(self.lang.t("messages.error"), self.lang.t("messages.export_error", error=str(e)))

    def _save_screenshot(self):
        if not MATPLOTLIB_AVAILABLE:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if filename:
            try:
                self.fig.savefig(filename, dpi=150, bbox_inches='tight')
                messagebox.showinfo(self.lang.t("messages.success"), self.lang.t("messages.screenshot_success", filename=filename))
            except Exception as e:
                messagebox.showerror(self.lang.t("messages.error"), self.lang.t("messages.screenshot_error", error=str(e)))

    def _show_settings(self):
        dialog = SettingsDialog(self.root, self.settings, self.lang)
        self.root.wait_window(dialog)

        if dialog.result:
            old_lang = self.settings.get('language', 'en')
            self.settings.update(dialog.result)
            self._save_settings()

            # Применить новые настройки
            self.chart_data.max_points = self.settings['max_chart_points']

            if MATPLOTLIB_AVAILABLE:
                for ax in [self.ax_voltage, self.ax_current, self.ax_power, self.ax_temp]:
                    ax.grid(self.settings['show_grid'], alpha=0.3)
                self.canvas.draw_idle()

            # Если язык изменился, перезагрузить интерфейс
            if self.settings.get('language') != old_lang:
                self.lang.set_language(self.settings['language'])
                messagebox.showinfo(self.lang.t("messages.info"),
                                  "Please restart the application to apply language changes.\n"
                                  "Пожалуйста, перезапустите приложение для применения языка.")

    def _show_about(self):
        messagebox.showinfo(self.lang.t("menu.about"), self.lang.t("about.text"))
    
    def _on_close(self):
        if self.connected:
            self.psu.disconnect()
        
        if self._update_job:
            self.root.after_cancel(self._update_job)
        
        self._save_settings()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()


def main():
    print("=" * 60)
    print("  FNIRSI Power Supply GUI")
    print("  Author: ALEXGAVS")
    print("=" * 60)
    
    if not MATPLOTLIB_AVAILABLE:
        print("\nWARNING: matplotlib not installed!")
        print("Install it with: pip install matplotlib")
        print("Charts will be disabled.\n")
    
    app = FnirsiGUI()
    app.run()


if __name__ == "__main__":
    main()
