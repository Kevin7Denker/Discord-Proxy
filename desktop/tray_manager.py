from __future__ import annotations
from threading import Thread
import pystray
from PIL import Image, ImageDraw

class TrayManager:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self._active = False

    def start(self) -> None:
        if self.icon is not None:
            return
        image = self._generate_icon(False)
        title = self._get_tooltip(False)
        self.icon = pystray.Icon("Discord Proxie", image, title, self._menu())
        Thread(target=self.icon.run, daemon=True).start()

    def update_status(self, active: bool) -> None:
        self._active = active
        if self.icon:
            self.icon.icon = self._generate_icon(active)
            self.icon.title = self._get_tooltip(active)
            self.icon.menu = self._menu()
            self.icon.update_menu()

    def _get_tooltip(self, active: bool) -> str:
        t = self.app.i18n.t
        status_text = t("status_connected") if active else t("status_disconnected")
        return f"Discord Proxie - {status_text}"

    def _generate_icon(self, active: bool) -> Image.Image:
        bg_color = (40, 42, 54, 255)
        outline_color = (80, 250, 123, 255) if active else (255, 85, 85, 255)
        bar_color = (80, 250, 123, 255) if active else (98, 114, 164, 255)
        
        image = Image.new("RGBA", (64, 64), bg_color)
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((8, 8, 56, 56), radius=12, outline=outline_color, width=3)
        draw.line((23, 42, 23, 23), fill=bar_color, width=5)
        draw.line((32, 42, 32, 15), fill=bar_color, width=5)
        draw.line((41, 42, 41, 20), fill=bar_color, width=5)
        return image

    def _menu(self):
        t = self.app.i18n.t
        status_text = t("status_connected") if self._active else t("status_disconnected")
        return pystray.Menu(
            pystray.MenuItem("Show / Restore", lambda: self.app.show_window(), default=True),
            pystray.MenuItem(f"Status: {status_text}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t("tray_disconnect"), lambda: self.app.disconnect_from_tray()),
            pystray.MenuItem("Exit", lambda: self.app.exit_application()),
        )

    def stop(self) -> None:
        if self.icon:
            self.icon.stop()
            self.icon = None
