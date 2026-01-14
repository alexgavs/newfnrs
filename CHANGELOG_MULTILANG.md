# Changelog - Multi-language Support

## Version 1.1.0 - Multi-language Support Implementation

**Date:** 2026-01-14

### Added

#### 🌍 Multi-language System
- **Language Manager** (`language_manager.py`)
  - Centralized translation management
  - Dynamic language switching
  - String interpolation support (e.g., `{port}`, `{count}`)
  - Global instance for easy access across modules

- **Language Files** (`lang/` folder)
  - `en.json` - English (default language)
  - `ru.json` - Russian
  - User-editable JSON format
  - Comprehensive translation coverage for all UI elements

- **Documentation**
  - `lang/README.md` - Complete guide for customizing translations
  - Instructions for adding new languages
  - Examples of string interpolation usage

#### 🖥️ GUI Updates
- All UI text now uses translation system
- Language selector in Settings dialog (Interface tab)
- Default language changed from Russian to English
- Automatic notification when language is changed
- All menus, dialogs, buttons, and messages are translatable

#### 🧪 Testing
- `test_translations.py` - Comprehensive test suite for translations
- Validates JSON structure
- Tests all translation keys
- Verifies string interpolation

### Changed

- **Default Language:** Changed from Russian to English (`'en'`)
- **Settings Dialog:** Now accepts `LanguageManager` instance
- **Configuration:** Default `language` setting now `'en'` instead of `'ru'`

### Technical Details

#### Translation Coverage
All UI elements are now translatable:
- Application title
- Menu items (File, Connection, Tools, Help)
- Toolbar elements
- Control panel (voltage, current, output button)
- Readings panel (temperature, capacity, mode, protection)
- Presets panel
- Settings dialog (all tabs and options)
- Chart labels (axes titles)
- Status messages
- Error/warning/success messages
- About dialog

#### Architecture
```
User Interface (GUI/CLI)
    ↓
LanguageManager
    ↓
JSON Language Files (en.json, ru.json)
```

### How to Use

#### Changing Language
1. Open GUI application
2. Go to **Tools → Settings**
3. Select **Interface** tab
4. Choose language from dropdown
5. Click **Save**
6. Restart application

#### Customizing Translations
1. Navigate to `lang/` folder
2. Open `en.json` or `ru.json` in text editor
3. Edit values (keep keys unchanged)
4. Save with UTF-8 encoding
5. Restart application to see changes

#### Adding New Language
1. Copy `lang/en.json` to `lang/<code>.json` (e.g., `de.json`)
2. Translate all values
3. Edit `language_manager.py`:
   ```python
   AVAILABLE_LANGUAGES = ["en", "ru", "de"]  # Add your language
   ```
4. Restart application - new language appears in settings

### Files Modified/Added

**Added:**
- `language_manager.py` - Translation manager module
- `lang/en.json` - English translations
- `lang/ru.json` - Russian translations
- `lang/README.md` - Language customization guide
- `test_translations.py` - Translation test suite
- `CHANGELOG_MULTILANG.md` - This file

**Modified:**
- `gui.py` - Updated to use `LanguageManager`
- `README.md` - Added multi-language documentation section

### Backward Compatibility

- Existing configuration files will work
- If `language` key is missing in config, defaults to `'en'`
- Old Russian interface users need to manually select Russian in settings

### Testing Results

✅ All 26 translation keys tested for both EN and RU
✅ JSON structure validation passed
✅ String interpolation working correctly
✅ GUI module imports without errors
✅ Language manager module functional

### Future Enhancements

Potential improvements for future versions:
- [ ] CLI multi-language support
- [ ] Additional languages (German, French, Chinese, etc.)
- [ ] Hot-reload translations without restart
- [ ] Translation export/import tools
- [ ] Crowdsourced translation platform integration

---

**Author:** ALEXGAVS
**License:** MIT with attribution requirement
