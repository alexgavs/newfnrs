# Language Files / Языковые файлы

This folder contains language translation files for the FNIRSI Power Supply Control application.

Эта папка содержит файлы переводов для приложения управления блоком питания FNIRSI.

## Available Languages / Доступные языки

- **en.json** - English (Default)
- **ru.json** - Русский

## How to Customize Translations / Как настроить переводы

You can edit these JSON files to customize the text displayed in the application.

Вы можете редактировать эти JSON файлы для настройки текста, отображаемого в приложении.

### File Structure / Структура файла

Each language file is a JSON object with nested keys:

Каждый языковой файл - это JSON объект с вложенными ключами:

```json
{
  "app_title": "Application Title",
  "menu": {
    "file": "File",
    "connection": "Connection"
  },
  "messages": {
    "warning": "Warning",
    "error": "Error"
  }
}
```

### String Interpolation / Подстановка значений

Some strings support variables using `{variable}` syntax:

Некоторые строки поддерживают переменные с использованием синтаксиса `{variable}`:

```json
{
  "status": {
    "connecting": "Connecting to {port}...",
    "packets": "Packets: {count}"
  }
}
```

## How to Change Language / Как изменить язык

1. Open the application / Откройте приложение
2. Go to **Tools → Settings** / Перейдите в **Инструменты → Настройки**
3. Select **Interface** tab / Выберите вкладку **Интерфейс**
4. Choose your language from the dropdown / Выберите язык из выпадающего списка
5. Click **Save** / Нажмите **Сохранить**
6. Restart the application / Перезапустите приложение

## Adding a New Language / Добавление нового языка

To add a new language:

Чтобы добавить новый язык:

1. Copy one of the existing JSON files (e.g., `en.json`)

   Скопируйте один из существующих JSON файлов (например, `en.json`)

2. Rename it using a two-letter language code (e.g., `de.json` for German)

   Переименуйте его, используя двухбуквенный код языка (например, `de.json` для немецкого)

3. Translate all values (keep the keys unchanged!)

   Переведите все значения (ключи оставьте без изменений!)

4. Edit `language_manager.py` and add your language code to `AVAILABLE_LANGUAGES`:

   Отредактируйте `language_manager.py` и добавьте код вашего языка в `AVAILABLE_LANGUAGES`:

   ```python
   AVAILABLE_LANGUAGES = ["en", "ru", "de"]  # Added German
   ```

5. The new language will appear in the settings dialog

   Новый язык появится в диалоге настроек

## Important Notes / Важные замечания

- **Always keep the JSON structure valid** - use a JSON validator if unsure

  **Всегда сохраняйте корректную структуру JSON** - используйте валидатор JSON при сомнениях

- **Do not change the keys** (e.g., "app_title"), only change the values

  **Не изменяйте ключи** (например, "app_title"), изменяйте только значения

- **Preserve placeholders** like `{port}`, `{count}`, `{filename}`, etc.

  **Сохраняйте заполнители** типа `{port}`, `{count}`, `{filename}` и т.д.

- **Use UTF-8 encoding** when editing files

  **Используйте кодировку UTF-8** при редактировании файлов

## Example Customization / Пример настройки

If you want to change "Connect" to "Link" in English:

Если вы хотите изменить "Connect" на "Link" в английском:

Open `en.json` and find:

Откройте `en.json` и найдите:

```json
{
  "toolbar": {
    "connect": "Connect",
    ...
  }
}
```

Change to / Измените на:

```json
{
  "toolbar": {
    "connect": "Link",
    ...
  }
}
```

Save the file and restart the application.

Сохраните файл и перезапустите приложение.

---

**Author / Автор:** ALEXGAVS

**License / Лицензия:** MIT with attribution requirement
