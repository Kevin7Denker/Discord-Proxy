import datetime
from typing import Callable, Optional

class Logger:
    def __init__(self):
        self._ui_callback: Optional[Callable[[str], None]] = None

    def set_ui_callback(self, callback: Callable[[str], None]) -> None:
        self._ui_callback = callback

    def _log(self, level: str, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {level}: {message}"
        print(formatted)
        if self._ui_callback:
            self._ui_callback(formatted)

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)

    def warning(self, message: str) -> None:
        self._log("WARN", message)
