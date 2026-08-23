from datetime import datetime
from typing import Callable, Optional


class Logger:
    def __init__(self):
        self._callback: Optional[Callable[[str], None]] = None

    def set_ui_callback(self, callback: Callable[[str], None]) -> None:
        self._callback = callback

    def _log(self, level: str, message: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}"
        print(line)
        if self._callback:
            self._callback(line)

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)

    def warning(self, message: str) -> None:
        self._log("WARN", message)
