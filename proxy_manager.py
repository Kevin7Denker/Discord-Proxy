from dataclasses import dataclass
from typing import Optional

from core.config import AppConfig
from core.discord import DiscordLauncher
from core.proxy import ProxyEndpoint, test_proxy_connectivity


@dataclass
class ProxyConfig:
    host: str
    port: int
    proxy_type: str = "socks5"
    username: Optional[str] = None
    password: Optional[str] = None

    def to_endpoint(self) -> ProxyEndpoint:
        return ProxyEndpoint(self.host, self.port, self.proxy_type, self.username or "", self.password or "")


async def test_proxy(config: ProxyConfig) -> dict:
    return await test_proxy_connectivity(config.to_endpoint())


def launch_discord(config: ProxyConfig, discord_path: str):
    launcher = DiscordLauncher(_NoopLogger())
    app_config = AppConfig(config.host, config.port, config.proxy_type.upper(), config.username or "", config.password or "", discord_path)
    result = launcher.start(app_config)
    if not result.ok:
        raise RuntimeError(result.message)
    return launcher.process


def terminate_discord(_proc) -> None:
    DiscordLauncher(_NoopLogger()).stop_existing_discord_instances()


class _NoopLogger:
    def info(self, _message: str) -> None:
        pass

    def error(self, _message: str) -> None:
        pass

    def warning(self, _message: str) -> None:
        pass
