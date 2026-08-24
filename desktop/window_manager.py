from __future__ import annotations
import asyncio
import threading
import time
import ctypes
from collections import deque

import webview

from core.config import ConfigManager
from core.discord_launcher import DiscordLauncher
from core.i18n import I18n
from core.paths import get_frontend_path
from desktop.api_bridge import ApiBridge
from desktop.tray_manager import TrayManager

class WindowManager:
    def __init__(self, config_manager: ConfigManager, logger, i18n: I18n):
        self.config_manager = config_manager
        self.logger = logger
        self.i18n = i18n
        self.launcher = DiscordLauncher(logger)
        self.window = None
        self.current_city = None
        self.current_country = None
        
        self.log_buffer = deque(maxlen=500)
        self.pending_logs = []
        self._log_lock = threading.Lock()
        
        self.tray = TrayManager(self)
        self.tray.start()
        
        self.logger.set_ui_callback(self._enqueue_log)
        
        self._bg_thread = threading.Thread(target=self._log_flusher_loop, daemon=True)
        self._bg_thread.start()

    def run(self) -> None:
        self.window = webview.create_window(
            "Discord Proxie", 
            (get_frontend_path() / "index.html").as_uri(), 
            js_api=ApiBridge(self), 
            width=800, 
            height=600, 
            min_size=(800, 600), 
            frameless=True, 
            easy_drag=False,
            transparent=True
        )
        self.window.events.closing += self.on_closing
        self.window.events.shown += self._on_shown
        webview.start(debug=False)

    def _on_shown(self) -> None:
        try:
            hwnd = self.window.native.Handle.ToInt32()
            self._enable_mica_effect(hwnd)
        except Exception:
            pass

    def _enable_mica_effect(self, hwnd: int) -> None:
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(ctypes.c_int(1)), 
                ctypes.sizeof(ctypes.c_int)
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_SYSTEMBACKDROP_TYPE, 
                ctypes.byref(ctypes.c_int(2)), 
                ctypes.sizeof(ctypes.c_int)
            )
        except Exception as e:
            self.logger.warning(f"Could not apply Mica effect: {e}")

    def _enqueue_log(self, message: str) -> None:
        with self._log_lock:
            self.log_buffer.append(message)
            self.pending_logs.append(message)

    def _log_flusher_loop(self) -> None:
        while True:
            time.sleep(0.150)
            with self._log_lock:
                if not self.pending_logs:
                    continue
                logs_to_send = list(self.pending_logs)
                self.pending_logs.clear()
            
            if self.window:
                try:
                    import json
                    json_logs = json.dumps(logs_to_send)
                    self.window.evaluate_js(f"window.discordProxy && window.discordProxy.appendLogs({json_logs})")
                except Exception:
                    pass

    def push_state(self) -> None:
        if self.window:
            state = {
                "active": self.launcher.is_active(),
                "lang": self.i18n.current_lang,
                "theme": self.config_manager.config.theme,
                "geo": self.current_city,
                "country": self.current_country
            }
            import json
            json_state = json.dumps(state)
            try:
                self.window.evaluate_js(f"window.discordProxy && window.discordProxy.updateState({json_state})")
            except Exception:
                pass
        self.tray.update_status(self.launcher.is_active())

    def cleanup(self) -> None:
        self.launcher.stop()
        if self.tray:
            self.tray.stop()

    def on_closing(self) -> bool:
        if self.launcher.is_active():
            self.window.hide()
            return False
        return True

    def show_window(self) -> None:
        if self.window:
            self.window.restore()
            self.window.show()

    def disconnect_from_tray(self) -> None:
        if self.launcher.is_active():
            asyncio.run(asyncio.to_thread(self.launcher.stop))
            self.push_state()

    def exit_application(self) -> None:
        self.cleanup()
        if self.window:
            self.window.destroy()
