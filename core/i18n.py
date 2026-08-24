import json
import locale
from core.paths import get_locales_path

class I18n:
    def __init__(self, default_lang: str = "en-US"):
        self.locales: dict[str, dict[str, str]] = {}
        self.current_lang = default_lang
        self._load_locales()
        self._auto_detect(default_lang)

    def _load_locales(self) -> None:
        path = get_locales_path()
        if not path.exists():
            return
        
        mapping = {
            "en": "en-US",
            "pt": "pt-BR",
            "es": "es-ES"
        }
        
        for file in path.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    locale_code = file.stem
                    locale_key = mapping.get(locale_code, locale_code)
                    self.locales[locale_key] = data
            except Exception:
                pass

    def _auto_detect(self, default_lang: str) -> None:
        try:
            sys_lang, _ = locale.getdefaultlocale()
            if sys_lang:
                sys_lang = sys_lang.replace("_", "-")
                if sys_lang in self.locales:
                    self.current_lang = sys_lang
                    return
                lang_code = sys_lang.split("-")[0]
                for key in self.locales:
                    if key.startswith(lang_code):
                        self.current_lang = key
                        return
        except Exception:
            pass
        self.current_lang = default_lang

    def set_language(self, lang: str) -> None:
        if lang in self.locales:
            self.current_lang = lang

    def t(self, key: str) -> str:
        return self.locales.get(self.current_lang, {}).get(key, key)

    def get_all_translations(self) -> dict:
        return self.locales.get(self.current_lang, {})
