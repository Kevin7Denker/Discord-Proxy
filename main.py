import asyncio
import signal
import sys
import tkinter as tk

from core.config import ConfigManager
from ui.dashboard import DiscordProxyApp
from ui.splash import SplashScreen
from utils import Logger


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    splash = SplashScreen(root)
    logger = Logger()
    config_manager = ConfigManager()

    def open_dashboard() -> None:
        splash.close()
        root.destroy()
        app = DiscordProxyApp(config_manager, logger)

        def shutdown(_signum=None, _frame=None) -> None:
            app.cleanup()
            config_manager.update_from_dict(app.get_current_config())
            app.destroy()

        for event in (signal.SIGINT, signal.SIGTERM):
            signal.signal(event, shutdown)
        app.protocol("WM_DELETE_WINDOW", shutdown)
        app.mainloop()

    root.after(1800, open_dashboard)
    root.mainloop()


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    main()
