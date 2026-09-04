from __future__ import annotations
import asyncio
import time
from dataclasses import asdict

from core.network_service import test_proxy_connectivity
from core.startup import set_start_with_windows

class ApiBridge:
    def __init__(self, manager):
        self._manager = manager

    def start_discord(self) -> dict:
        config = self._manager.config_manager.config
        self._manager.logger.info(self._manager.i18n.t("status_validating"))
        validation = asyncio.run(test_proxy_connectivity(config.to_proxy_endpoint()))
        if not validation.get("ok"):
            message = validation.get("error", "Unknown error")
            self._manager.logger.error(f"Validation failed: {message}")
            return {"ok": False, "message": message}
            
        self._manager.current_city = validation.get("city", "Unknown")
        self._manager.current_country = validation.get("country", "Unknown")
        
        result = self._manager.launcher.start(config)
        self._manager.logger.info(result.message)
        self._manager.push_state()
        return asdict(result)

    def stop_discord(self) -> dict:
        self._manager.logger.info("Stopping Discord and local relay...")
        self._manager.launcher.stop()
        self._manager.logger.info("Discord and relay stopped.")
        self._manager.push_state()
        return {"ok": True}
        
    def restart_discord(self) -> dict:
        self._manager.logger.info("Restarting Discord and local relay...")
        self._manager.launcher.stop()
        time.sleep(1.0)
        return self.start_discord()

    def hide_window(self) -> None:
        self._manager.window.hide()

    def get_translations(self) -> dict:
        return self._manager.i18n.get_all_translations()

    def set_language(self, lang: str) -> None:
        self._manager.i18n.set_language(lang)
        self._manager.config_manager.update_pref("language", lang)
        self._manager.tray.update_status(self._manager.launcher.is_active())

    def set_theme(self, theme: str) -> None:
        if theme in {"light", "dark"}:
            self._manager.config_manager.update_pref("theme", theme)

    def set_start_with_windows(self, enabled: bool) -> dict:
        requested = bool(enabled)
        applied = set_start_with_windows(requested)
        if not applied and requested:
            self._manager.logger.error("Start with Windows is only available on Windows.")
            return {"ok": False, "message": "Start with Windows is only available on Windows."}

        self._manager.config_manager.update_pref("start_with_windows", requested)
        mode = "enabled" if requested else "disabled"
        self._manager.logger.info(f"Start with Windows {mode}.")
        self._manager.push_state()
        return {"ok": True, "start_with_windows": requested}

    def set_custom_proxy(self, settings: dict) -> dict:
        self._manager.config_manager.set_custom_proxy(settings)
        self._manager.logger.info("Custom proxy settings saved.")
        self._manager.push_state()
        return {"ok": True, "proxy_preferences": self._manager.config_manager.get_proxy_preferences()}

    def set_custom_proxy_enabled(self, enabled: bool) -> dict:
        self._manager.config_manager.set_custom_proxy_enabled(enabled)
        mode = "custom proxy" if self._manager.config_manager.config.custom_proxy_enabled else ".env proxy"
        self._manager.logger.info(f"Proxy mode set to {mode}.")
        self._manager.push_state()
        return {"ok": True, "proxy_preferences": self._manager.config_manager.get_proxy_preferences()}

    def reset_custom_proxy(self) -> dict:
        self._manager.config_manager.reset_custom_proxy()
        self._manager.logger.info("Custom proxy reset. Using .env proxy settings.")
        self._manager.push_state()
        return {"ok": True, "proxy_preferences": self._manager.config_manager.get_proxy_preferences()}

    def get_recent_logs(self) -> list:
        return list(self._manager.log_buffer)

    def close_window(self) -> None:
        if self._manager.launcher.is_active():
            self._manager.window.hide()
        else:
            self._manager.cleanup()
            self._manager.window.destroy()

    def get_initial_state(self) -> dict:
        return {
            "active": self._manager.launcher.is_active(),
            "lang": self._manager.i18n.current_lang,
            "theme": self._manager.config_manager.config.theme,
            "start_with_windows": self._manager.config_manager.config.start_with_windows,
            "proxy_preferences": self._manager.config_manager.get_proxy_preferences(),
            "logs": list(self._manager.log_buffer)
        }

    def force_exit(self) -> None:
        self._manager.cleanup()
        self._manager.window.destroy()

    def open_support_link(self) -> None:
        self._manager.logger.info("Opening support link...")
        try:
            import webbrowser
            webbrowser.open("https://buymeacoffee.com/denker")
        except Exception as e:
            self._manager.logger.error(f"Failed to open link: {e}")
