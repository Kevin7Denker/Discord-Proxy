import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, Tuple

from dotenv import load_dotenv
from core.paths import get_env_path, get_base_path
from core.network_service import ProxyEndpoint

DEFAULT_PORTS: Dict[str, int] = {"SOCKS5": 1080, "HTTP": 8080}

def find_discord_executable() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    import glob
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
        host = "127.0.0.1"
    if not port_candidate:
        port = DEFAULT_PORTS.get((proxy_type or "SOCKS5").upper(), 1080)
    else:
        try:
            port = int(port_candidate)
        except ValueError:
            port = DEFAULT_PORTS.get((proxy_type or "SOCKS5").upper(), 1080)
    if port < 1 or port > 65535:
        port = DEFAULT_PORTS.get((proxy_type or "SOCKS5").upper(), 1080)
    return host, port

@dataclass
class AppConfig:
    host: str = ""
    port: int = 1080
    proxy_type: str = "SOCKS5"
    username: str = ""
    password: str = ""
    discord_path: str = ""
    language: str = "en-US"
    theme: str = "dark"

    def to_proxy_endpoint(self) -> ProxyEndpoint:
        return ProxyEndpoint(
            host=self.host,
            port=self.port,
            proxy_type=self.proxy_type,
            username=self.username,
            password=self.password
        )

class ConfigManager:
    def __init__(self):
        self.env_path = get_env_path()
        self.prefs_path = get_base_path() / "prefs.json"
        load_dotenv(self.env_path, override=True)
        self.config = self.load_config()

    def load_config(self) -> AppConfig:
        raw_prefs = {}
        if self.prefs_path.exists():
            try:
                with open(self.prefs_path, "r", encoding="utf-8") as file:
                    raw_prefs = json.load(file)
            except Exception:
                pass

        defaults = asdict(AppConfig())
        allowed_ui_prefs = {"language", "theme"}
        merged = {**defaults, **{k: v for k, v in raw_prefs.items() if k in allowed_ui_prefs}}

        env_values = {
            "host": os.environ.get("PROXY_HOST", ""),
            "port": os.environ.get("PROXY_PORT", ""),
            "proxy_type": os.environ.get("PROXY_TYPE", "SOCKS5"),
            "username": os.environ.get("PROXY_USER", ""),
            "password": os.environ.get("PROXY_PASS", ""),
            "discord_path": os.environ.get("DISCORD_PATH", ""),
        }
        
        for k, v in env_values.items():
            if v:
                merged[k] = v

        merged["proxy_type"] = str(merged.get("proxy_type", "SOCKS5")).upper()
        if merged["proxy_type"] not in DEFAULT_PORTS:
            merged["proxy_type"] = "SOCKS5"
            
        merged["host"], merged["port"] = sanitize_host_port(merged.get("host", ""), str(merged.get("port", "")), merged["proxy_type"])
        
        path = str(merged.get("discord_path") or "")
        merged["discord_path"] = path if os.path.isfile(path) else find_discord_executable()

        return AppConfig(**merged)

    def save_ui_prefs(self) -> None:
        prefs = {
            "language": self.config.language,
            "theme": self.config.theme
        }
        try:
            with open(self.prefs_path, "w", encoding="utf-8") as file:
                json.dump(prefs, file, indent=2)
        except Exception:
            pass

    def update_pref(self, key: str, value: str) -> None:
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save_ui_prefs()