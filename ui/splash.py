from __future__ import annotations

import tkinter as tk


class SplashScreen(tk.Toplevel):
    def __init__(self, master: tk.Misc):
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(bg="#10141c")
        self.attributes("-alpha", 0.0)
        self._place_window()
        tk.Label(self, text="DISCORD PROXY", font=("Segoe UI Semibold", 24), fg="#f3f7ff", bg="#10141c").pack(pady=(40, 5))
        tk.Label(self, text="By Denker", font=("Segoe UI", 10), fg="#7e8da6", bg="#10141c").pack(pady=(0, 24))
        self.progress = tk.Canvas(self, width=260, height=3, bg="#10141c", highlightthickness=0)
        self.progress.pack(pady=(0, 34))
        self.progress.create_rectangle(0, 0, 260, 3, fill="#202b3d", outline="")
        self.bar = self.progress.create_rectangle(0, 0, 48, 3, fill="#54d6a0", outline="")
        self._phase = 0
        self._animation_id = None
        self._animate()

    def _place_window(self) -> None:
        width, height = 460, 220
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _animate(self) -> None:
        if not self.winfo_exists():
            return
        self._phase = (self._phase + 5) % 308
        self.progress.coords(self.bar, self._phase - 48, 0, self._phase, 3)
        alpha = min(1.0, float(self._phase) / 45) if self._phase < 45 else 1.0
        self.attributes("-alpha", alpha)
        self._animation_id = self.after(32, self._animate)

    def close(self) -> None:
        if self.winfo_exists():
            if self._animation_id is not None:
                self.after_cancel(self._animation_id)
                self._animation_id = None
            self.destroy()