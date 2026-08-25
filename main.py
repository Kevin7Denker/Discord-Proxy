import asyncio
import signal
import sys
import ctypes

from core.config import ConfigManager
from core.i18n import I18n
from core.logger import Logger
from desktop.window_manager import WindowManager

def main() -> None:
    logger = Logger()
    config_manager = ConfigManager()
    i18n = I18n(default_lang=config_manager.config.language or "en-US")
    app = WindowManager(config_manager, logger, i18n)

    def shutdown(_signum=None, _frame=None) -> None:
        app.cleanup()

    for event in (signal.SIGINT, signal.SIGTERM):
        signal.signal(event, shutdown)
    app.run()

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KevinDenker.DiscordProxie")
    main()
