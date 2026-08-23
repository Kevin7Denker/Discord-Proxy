from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import glob
import json
import os
from pathlib import Path
from typing import Dict, Tuple

from .proxy import ProxyEndpoint

CONFIG_FILE_NAME = "config.json"
DEFAULT_PORTS: Dict[str, int] = {"SOCKS5": 1080, "HTTP": 8080}


def find_discord_executable() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    variants = [("Discord", "Discord.exe"), ("DiscordCanary", "DiscordCanary.exe"), ("DiscordPTB", "DiscordPTB.exe")]
    for folder_name, exe_name in variants:
        pattern = os.path.join(local_app_data, folder_name, "app-*", exe_name)
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches)[-1]
    return ""


def sanitize_host_port(host_text: str, port_text: str, proxy_type: str = "SOCKS5") -> Tuple[str, int]:
    host = (host_text or "").strip()
    port_candidate = (port_text or "").strip()
    if host and ":" in host and host.count(":") == 1:
        maybe_host, maybe_port = host.rsplit(":", 1)
        if maybe_port.isdigit():
            host = maybe_host.strip()
            if not port_candidate:
                port_candidate = maybe_port
    if not host:
        raise ValueError("Proxy host is required.")
    if not port_candidate:
        port = DEFAULT_PORTS.get((proxy_type or "SOCKS5").upper(), 1080)
    else:
        try:
            port = int(port_candidate)
        except ValueError as exc:
            raise ValueError("Proxy port must be a valid number.") from exc
    if port < 1 or port > 65535:
        raise ValueError("Proxy port must be between 1 and 65535.")
    return host, port


@dataclass
class AppConfig:
    host: str = ""
    port: int = 1080
    proxy_type: str = "SOCKS5"
    username: str = ""
    password: str = ""
    discord_path: str = ""

    def to_proxy_endpoint(self) -> ProxyEndpoint:
        return ProxyEndpoint(self.host, self.port, self.proxy_type.lower(), self.username, self.password)


class ConfigManager:
    def __init__(self, config_path: str | None = None):
        self.config_path = Path(config_path) if config_path else Path(__file__).resolve().parent.parent / CONFIG_FILE_NAME
        self.config = self.load_config()

    def load_config(self) -> AppConfig:
        if not self.config_path.exists():
            config = AppConfig(discord_path=find_discord_executable())
            self.save_config(config)
            return config
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                raw = json.load(file)
        except Exception:
            config = AppConfig(discord_path=find_discord_executable())
            self.save_config(config)
            return config
        defaults = asdict(AppConfig())
        allowed = {field.name for field in fields(AppConfig)}
        merged = {**defaults, **{key: value for key, value in raw.items() if key in allowed}}
        merged["proxy_type"] = str(merged.get("proxy_type", "SOCKS5")).upper()
        if merged["proxy_type"] not in DEFAULT_PORTS:
            merged["proxy_type"] = "SOCKS5"
        try:
            merged["port"] = int(merged.get("port") or DEFAULT_PORTS[merged["proxy_type"]])
        except Exception:
            merged["port"] = DEFAULT_PORTS[merged["proxy_type"]]
        path = str(merged.get("discord_path") or "")
        merged["discord_path"] = path if os.path.isfile(path) else find_discord_executable()
        return AppConfig(**merged)

    def save_config(self, config: AppConfig | None = None) -> None:
        if config is not None:
            self.config = config
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(asdict(self.config), file, indent=2)

    def update_from_dict(self, updates: dict) -> None:
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.config.proxy_type = (self.config.proxy_type or "SOCKS5").upper()
        if self.config.proxy_type not in DEFAULT_PORTS:
            self.config.proxy_type = "SOCKS5"
        self.save_config()