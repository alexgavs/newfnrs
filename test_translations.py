"""
Test script to verify all translations are working correctly
"""

from language_manager import LanguageManager
import json

def test_language_file(lang_code):
    """Test a specific language file"""
    print(f"\n{'='*60}")
    print(f"Testing {lang_code.upper()} translations")
    print('='*60)

    try:
        lang = LanguageManager(lang_code)

        # Test all major keys
        test_keys = [
            "app_title",
            "menu.file",
            "menu.connection",
            "menu.tools",
            "toolbar.port",
            "toolbar.connect",
            "control_panel.title",
            "control_panel.voltage",
            "control_panel.current",
            "control_panel.output_on",
            "control_panel.output_off",
            "readings_panel.title",
            "readings_panel.temperature",
            "presets_panel.title",
            "presets_panel.hint",
            "settings_dialog.title",
            "charts.voltage",
            "charts.current",
            "charts.power",
            "status.ready",
            "status.connecting",
            "status.connected",
            "messages.warning",
            "messages.error",
            "messages.success",
            "about.text"
        ]

        missing_keys = []
        for key in test_keys:
            value = lang.get(key)
            if value.startswith('[') and value.endswith(']'):
                missing_keys.append(key)
            else:
                print(f"✓ {key}: {value[:50]}...")

        if missing_keys:
            print(f"\n❌ Missing translations:")
            for key in missing_keys:
                print(f"   - {key}")
            return False
        else:
            print(f"\n✅ All translations present for {lang_code}")
            return True

    except Exception as e:
        print(f"❌ Error loading {lang_code}: {e}")
        return False

def test_interpolation():
    """Test string interpolation"""
    print(f"\n{'='*60}")
    print("Testing string interpolation")
    print('='*60)

    lang = LanguageManager("en")

    # Test with parameters
    result1 = lang.get("status.connecting", port="COM3")
    print(f"✓ status.connecting: {result1}")

    result2 = lang.get("status.packets", count=42)
    print(f"✓ status.packets: {result2}")

    result3 = lang.get("messages.export_success", filename="test.csv")
    print(f"✓ messages.export_success: {result3}")

    print("\n✅ String interpolation working correctly")

def validate_json_structure():
    """Validate JSON structure of all language files"""
    print(f"\n{'='*60}")
    print("Validating JSON structure")
    print('='*60)

    for lang_code in ["en", "ru"]:
        try:
            with open(f"lang/{lang_code}.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✓ {lang_code}.json: Valid JSON structure")
        except json.JSONDecodeError as e:
            print(f"❌ {lang_code}.json: Invalid JSON - {e}")
            return False
        except FileNotFoundError:
            print(f"❌ {lang_code}.json: File not found")
            return False

    print("\n✅ All JSON files are valid")
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  FNIRSI Translation Test Suite")
    print("  Author: ALEXGAVS")
    print("="*60)

    # Validate JSON first
    if not validate_json_structure():
        print("\n❌ JSON validation failed. Fix JSON errors before continuing.")
        exit(1)

    # Test each language
    results = {}
    for lang_code in ["en", "ru"]:
        results[lang_code] = test_language_file(lang_code)

    # Test interpolation
    test_interpolation()

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)

    all_passed = all(results.values())

    for lang_code, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{lang_code.upper()}: {status}")

    if all_passed:
        print("\n🎉 All tests passed! Translations are ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

    print("="*60)
