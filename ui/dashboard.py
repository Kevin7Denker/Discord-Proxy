from __future__ import annotations

import asyncio
from dataclasses import asdict
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.config import AppConfig, ConfigManager, DEFAULT_PORTS, sanitize_host_port
from core.discord import DiscordLauncher
from core.proxy import test_proxy_connectivity


class DiscordProxyApp(ctk.CTk):
    def __init__(self, config_manager: ConfigManager, logger):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.title("DISCORD PROXY")
        self.geometry("920x700")
        self.minsize(860, 640)
        self.config_manager = config_manager
        self.logger = logger
        self.launcher = DiscordLauncher(logger)
        self._disconnect_in_progress = False
        self.type_var = tk.StringVar(value="SOCKS5")
        self._build_ui()
        self._load_config()
        self.logger.set_ui_callback(lambda message: self.after(0, lambda: self._append_log(message)))

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=0, column=0, padx=24, pady=(22, 10), sticky="ew")
        form.grid_columnconfigure(1, weight=1)
        fields = [("Proxy Host / IP", "host_entry", "proxy.example.com"), ("Port", "port_entry", "1080"), ("Username", "user_entry", "Optional"), ("Password", "pass_entry", "Optional")]
        for row, (label, name, placeholder) in enumerate(fields):
            ctk.CTkLabel(form, text=label).grid(row=row, column=0, padx=14, pady=8, sticky="w")
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, show="*" if name == "pass_entry" else None)
            entry.grid(row=row, column=1, padx=14, pady=8, sticky="ew")
            setattr(self, name, entry)
        ctk.CTkLabel(form, text="Type").grid(row=4, column=0, padx=14, pady=8, sticky="w")
        self.type_option = ctk.CTkOptionMenu(form, values=["SOCKS5", "HTTP"], variable=self.type_var, command=self._on_type_change)
        self.type_option.grid(row=4, column=1, padx=14, pady=8, sticky="ew")
        ctk.CTkLabel(form, text="Discord executable").grid(row=5, column=0, padx=14, pady=8, sticky="w")
        path_row = ctk.CTkFrame(form, fg_color="transparent")
        path_row.grid(row=5, column=1, padx=14, pady=8, sticky="ew")
        path_row.grid_columnconfigure(0, weight=1)
        self.discord_path_entry = ctk.CTkEntry(path_row, placeholder_text="Auto-detected Discord.exe")
        self.discord_path_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(path_row, text="Browse", width=100, command=self._browse).grid(row=0, column=1)
        ctk.CTkButton(form, text="Test connection", command=self._test).grid(row=6, column=0, columnspan=2, pady=(12, 16))
        status = ctk.CTkFrame(self, fg_color="transparent")
        status.grid(row=1, column=0, padx=24, pady=6, sticky="ew")
        status.grid_columnconfigure(4, weight=1)
        self.proxy_status = ctk.CTkLabel(status, text="Proxy: OFF", text_color="#ff647c")
        self.proxy_status.grid(row=0, column=0, padx=8)
        self.discord_status = ctk.CTkLabel(status, text="Discord: OFF", text_color="#ff647c")
        self.discord_status.grid(row=0, column=1, padx=8)
        self.latency = ctk.CTkLabel(status, text="Latency: -- ms")
        self.latency.grid(row=0, column=2, padx=8)
        ctk.CTkButton(status, text="Connect & start", command=self._connect).grid(row=0, column=3, padx=8)
        ctk.CTkButton(status, text="Disconnect", fg_color="#8b1e3f", hover_color="#701732", command=self._disconnect).grid(row=0, column=4, padx=8, sticky="e")
        log_frame = ctk.CTkFrame(self, corner_radius=12)
        log_frame.grid(row=2, column=0, padx=24, pady=(6, 22), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        self.log_text = ctk.CTkTextbox(log_frame, state="disabled", wrap="word")
        self.log_text.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

    def _load_config(self) -> None:
        config = self.config_manager.config
        for name, value in (("host_entry", config.host), ("port_entry", str(config.port)), ("user_entry", config.username), ("pass_entry", config.password), ("discord_path_entry", config.discord_path)):
            field = getattr(self, name)
            field.insert(0, value)
        self.type_var.set(config.proxy_type.upper())

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _config(self) -> AppConfig:
        host, port = sanitize_host_port(self.host_entry.get(), self.port_entry.get(), self.type_var.get())
        return AppConfig(host, port, self.type_var.get().upper(), self.user_entry.get().strip(), self.pass_entry.get().strip(), self.discord_path_entry.get().strip())

    def _on_type_change(self, selected: str) -> None:
        if not self.port_entry.get().strip():
            self.port_entry.insert(0, str(DEFAULT_PORTS[selected.upper()]))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            self.discord_path_entry.delete(0, tk.END)
            self.discord_path_entry.insert(0, path)

    def _background(self, action) -> None:
        Thread(target=action, daemon=True).start()

    def _test(self) -> None:
        try:
            config = self._config()
        except ValueError as exc:
            messagebox.showerror("Invalid proxy", str(exc))
            return
        self.logger.info("Testing proxy connectivity...")
        def worker() -> None:
            result = asyncio.run(test_proxy_connectivity(config.to_proxy_endpoint()))
            if result.get("ok"):
                self.after(0, lambda: self.proxy_status.configure(text="Proxy: ON", text_color="#54d6a0"))
                self.after(0, lambda: self.latency.configure(text=f"Latency: {result['latency_ms']} ms"))
                self.logger.info(f"Proxy OK | IP={result['ip']} | Country={result['country']} | City={result['city']}")
            else:
                self.after(0, lambda: self.proxy_status.configure(text="Proxy: OFF", text_color="#ff647c"))
                self.logger.error(f"Proxy test failed: {result.get('error', 'Unknown error')}")
        self._background(worker)

    def _connect(self) -> None:
        try:
            config = self._config()
        except ValueError as exc:
            messagebox.showerror("Invalid proxy", str(exc))
            return
        self.config_manager.save_config(config)
        def worker() -> None:
            validation = asyncio.run(test_proxy_connectivity(config.to_proxy_endpoint()))
            if not validation.get("ok"):
                self.logger.error(f"Validation failed: {validation.get('error', 'Unknown error')}")
                return
            result = self.launcher.start(config)
            self.after(0, lambda: self.discord_status.configure(text="Discord: ON" if result.ok else "Discord: OFF", text_color="#54d6a0" if result.ok else "#ff647c"))
            self.logger.info(result.message)
        self._background(worker)

    def _disconnect(self) -> None:
        if self._disconnect_in_progress:
            return
        self._disconnect_in_progress = True
        self.logger.info("Stopping Discord and local relay...")
        def worker() -> None:
            try:
                self.launcher.stop()
            finally:
                self._disconnect_in_progress = False
                self.after(0, lambda: self.discord_status.configure(text="Discord: OFF", text_color="#ff647c"))
                self.logger.info("Discord and relay stopped.")
        self._background(worker)

    def get_current_config(self) -> dict:
        try:
            return asdict(self._config())
        except ValueError:
            return asdict(self.config_manager.config)

    def cleanup(self) -> None:
        self.launcher.stop()