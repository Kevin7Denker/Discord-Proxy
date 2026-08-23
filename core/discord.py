from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import List, Optional

from .config import AppConfig
from .proxy import TunManager
from .relay import LocalRelayService, RelayConfig

BYPASS_LIST = "<-loopback>"
DISCORD_PROCESS_NAMES = {"discord.exe", "update.exe", "discordcanary.exe", "discordptb.exe"}


@dataclass
class LaunchResult:
    ok: bool
    message: str
    relay_active: bool = False


class DiscordLauncher:
    def __init__(self, logger):
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
        self.relay: Optional[LocalRelayService] = None
        self.tun_manager = TunManager(logger)

    def start(self, config: AppConfig) -> LaunchResult:
        if not config.discord_path or not os.path.isfile(config.discord_path):
            return LaunchResult(False, "Discord executable not found.")
        self.stop_existing_discord_instances()
        scheme = config.proxy_type.lower()
        host, port, relay_active = config.host, config.port, False
        if config.username or config.password:
            self.logger.info("Authentication detected. Starting local relay on 127.0.0.1:9050.")
            self.relay = LocalRelayService(config.to_proxy_endpoint(), RelayConfig(scheme))
            self.relay.start()
            host, port, relay_active = "127.0.0.1", 9050, True
        if scheme == "socks5":
            self.tun_manager.start(config.to_proxy_endpoint())
        self.logger.info("Applying WebRTC anti-leak policy (disable_non_proxied_udp)...")
        self.logger.info("DNS resolution forced through proxy tunnel.")
        self.logger.info("Starting Discord with proxy + WebRTC isolation flags.")
        self.process = subprocess.Popen(self._build_launch_args(config.discord_path, scheme, host, port))
        return LaunchResult(True, "Discord started successfully.", relay_active)

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            with suppress(Exception):
                self.process.terminate()
        self.stop_existing_discord_instances()
        self.tun_manager.stop()
        if self.relay:
            self.relay.stop()
            self.relay = None
        self.process = None

    def _build_launch_args(self, discord_path: str, proxy_scheme: str, proxy_host: str, proxy_port: int) -> List[str]:
        return [discord_path, f"--proxy-server={proxy_scheme}://{proxy_host}:{proxy_port}", f"--proxy-bypass-list={BYPASS_LIST}", "--force-webrtc-ip-handling-policy=disable_non_proxied_udp", "--enforce-webrtc-ip-permission-check", "--disable-features=WebRtcHideLocalIpsWithMdns", "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"]

    def stop_existing_discord_instances(self) -> None:
        for process_name in DISCORD_PROCESS_NAMES:
            with suppress(Exception):
                subprocess.run(["taskkill", "/IM", process_name, "/F", "/T"], check=False, capture_output=True, text=True)


from contextlib import suppress