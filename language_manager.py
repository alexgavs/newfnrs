"""
Language Manager Module
=======================
Manages application translations and language switching.
Users can edit language files (lang/en.json, lang/ru.json) to customize translations.

Author: ALEXGAVS
"""

import json
import os
from typing import Dict, Any, Optional


class LanguageManager:
    """Manages application translations"""

    LANG_DIR = "lang"
    DEFAULT_LANGUAGE = "en"
    AVAILABLE_LANGUAGES = ["en", "ru"]

    def __init__(self, language: str = None):
        """
        Initialize language manager

        Args:
            language: Language code (en, ru). If None, uses DEFAULT_LANGUAGE
        """
        self._translations: Dict[str, Any] = {}
        self._current_language = language or self.DEFAULT_LANGUAGE
        self._load_language(self._current_language)

    def _load_language(self, lang_code: str) -> bool:
        """
        Load language file

        Args:
            lang_code: Language code (en, ru)

        Returns:
            True if loaded successfully, False otherwise
        """
        if lang_code not in self.AVAILABLE_LANGUAGES:
            print(f"Warning: Language '{lang_code}' not available, using '{self.DEFAULT_LANGUAGE}'")
            lang_code = self.DEFAULT_LANGUAGE

        lang_file = os.path.join(self.LANG_DIR, f"{lang_code}.json")

        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self._translations = json.load(f)
            self._current_language = lang_code
            return True
        except FileNotFoundError:
            print(f"Error: Language file '{lang_file}' not found")
            # Try to load default language
            if lang_code != self.DEFAULT_LANGUAGE:
                return self._load_language(self.DEFAULT_LANGUAGE)
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in '{lang_file}': {e}")
            return False

    def set_language(self, lang_code: str) -> bool:
        """
        Change current language

        Args:
            lang_code: Language code (en, ru)

        Returns:
            True if changed successfully, False otherwise
        """
        return self._load_language(lang_code)

    def get_current_language(self) -> str:
        """Get current language code"""
        return self._current_language

    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return self.AVAILABLE_LANGUAGES.copy()

    def get(self, key_path: str, default: str = None, **kwargs) -> str:
        """
        Get translation by key path

        Args:
            key_path: Dot-separated path to translation (e.g., "menu.file")
            default: Default value if key not found
            **kwargs: Format parameters for string interpolation

        Returns:
            Translated string or default value

        Examples:
            >>> lang.get("menu.file")
            "File"
            >>> lang.get("status.connecting", port="COM3")
            "Connecting to COM3..."
        """
        keys = key_path.split('.')
        value = self._translations

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break

        if value is None:
            if default is not None:
                return default
            # Return key path if translation not found (for debugging)
            return f"[{key_path}]"

        # Apply string formatting if kwargs provided
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError) as e:
                print(f"Warning: Format error in '{key_path}': {e}")
                return value

        return value

    def __getitem__(self, key_path: str) -> str:
        """
        Get translation using dict-like syntax

        Example:
            >>> lang["menu.file"]
            "File"
        """
        return self.get(key_path)

    def t(self, key_path: str, **kwargs) -> str:
        """
        Short alias for get()

        Example:
            >>> lang.t("status.connecting", port="COM3")
            "Connecting to COM3..."
        """
        return self.get(key_path, **kwargs)


# Global instance - can be imported and used across the application
_global_lang_manager: Optional[LanguageManager] = None


def get_language_manager(language: str = None) -> LanguageManager:
    """
    Get or create global language manager instance

    Args:
        language: Language code. Only used on first call to initialize.

    Returns:
        Global LanguageManager instance
    """
    global _global_lang_manager

    if _global_lang_manager is None:
        _global_lang_manager = LanguageManager(language)
    elif language is not None and language != _global_lang_manager.get_current_language():
        _global_lang_manager.set_language(language)

    return _global_lang_manager


def set_global_language(language: str) -> bool:
    """
    Set language for global language manager

    Args:
        language: Language code

    Returns:
        True if changed successfully
    """
    lang_manager = get_language_manager()
    return lang_manager.set_language(language)


# Convenience function for quick translations
def tr(key_path: str, **kwargs) -> str:
    """
    Quick translation function using global language manager

    Args:
        key_path: Dot-separated path to translation
        **kwargs: Format parameters

    Returns:
        Translated string

    Example:
        >>> tr("menu.file")
        "File"
        >>> tr("status.connecting", port="COM3")
        "Connecting to COM3..."
    """
    return get_language_manager().get(key_path, **kwargs)


if __name__ == "__main__":
    # Test the language manager
    print("Testing Language Manager")
    print("=" * 60)

    # Test English
    lang = LanguageManager("en")
    print(f"Current language: {lang.get_current_language()}")
    print(f"App title: {lang['app_title']}")
    print(f"Menu File: {lang['menu.file']}")
    print(f"Status: {lang.get('status.connecting', port='COM3')}")
    print()

    # Test Russian
    lang.set_language("ru")
    print(f"Current language: {lang.get_current_language()}")
    print(f"App title: {lang['app_title']}")
    print(f"Menu File: {lang['menu.file']}")
    print(f"Status: {lang.get('status.connecting', port='COM3')}")
    print()

    # Test global manager
    print("Testing global manager:")
    print(f"Translation: {tr('menu.tools')}")
    set_global_language("en")
    print(f"Translation (EN): {tr('menu.tools')}")
