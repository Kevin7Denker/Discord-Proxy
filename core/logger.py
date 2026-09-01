import logging
from logging.handlers import NTEventLogHandler
from typing import Callable, Optional

# Shared Windows Event Log logger instance
def _create_event_logger(name: str = "discord_proxy") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        try:
            handler = NTEventLogHandler(appname="DiscordProxy")
        except Exception as e:
            # Fallback to console handler if Windows Event Log is unavailable
            handler = logging.StreamHandler()
            logger.debug(f"NTEventLogHandler unavailable ({e}), using StreamHandler fallback.")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

_event_logger = _create_event_logger()

class Logger:
    """Legacy logger used by UI components.
    It forwards log messages to a UI callback (if set) and also writes to the
    Windows Event Log via the shared event logger.
    """
    def __init__(self) -> None:
        self._ui_callback: Optional[Callable[[str], None]] = None

    def set_ui_callback(self, callback: Callable[[str], None]) -> None:
        self._ui_callback = callback

    def _log(self, level: str, message: str) -> None:
        # Write to Windows Event Log
        if level == "INFO":
            _event_logger.info(message)
        elif level in ("WARN", "WARNING"):
            _event_logger.warning(message)
        elif level == "ERROR":
            _event_logger.error(message)
        else:
            _event_logger.debug(message)
        # Forward to UI callback if present
        if self._ui_callback:
            self._ui_callback(message)

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        self._log("WARN", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)

def get_logger(name: str = "discord_proxy") -> logging.Logger:
    """Return the shared Windows Event Log logger instance."""
    return _event_logger