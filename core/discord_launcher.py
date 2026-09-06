from __future__ import annotations

from dataclasses import dataclass
import os
import socket
import subprocess
from typing import List, Optional
from contextlib import suppress

from .connection_classifier import ConnectionCategory
from .config import AppConfig
from .discord_log_parser import parse_discord_log_line
from .network_service import TunManager
from .local_relay import LocalRelayService, RelayConfig
from .observability import ConnectionEvent, ConnectionObserver, next_connection_id
from .paths import get_user_log_path
from .processes import hidden_subprocess_kwargs
import threading
import sys
import time
from .restart import restart
from .logger import get_logger

BYPASS_LIST = "<-loopback>"
DISCORD_PROCESS_NAMES = {"discord.exe", "update.exe", "discordcanary.exe", "discordptb.exe"}


@dataclass
class LaunchResult:
    ok: bool
    message: str
    relay_active: bool = False


class DiscordLauncher:
    def __init__(self, logger=None, observer: Optional[ConnectionObserver] = None) -> None:
        self.logger = logger or get_logger()
        self.observer = observer or ConnectionObserver(self.logger, sink_path=get_user_log_path())
        self.process: Optional[subprocess.Popen] = None
        self.relay: Optional[LocalRelayService] = None
        self.tun_manager = TunManager(self.logger, self.observer)
        self.monitor_thread: Optional[threading.Thread] = None
        self.output_thread: Optional[threading.Thread] = None

    def start(self, config: AppConfig) -> LaunchResult:
        if not config.discord_path or not os.path.isfile(config.discord_path):
            return LaunchResult(False, "Discord executable not found.")
        self.stop_existing_discord_instances()
        scheme = config.proxy_type.lower()
        host, port, relay_active = config.host, config.port, False
        if config.username or config.password:
            relay_port = self._select_relay_port()
            self.logger.info(f"Authentication detected. Starting local relay on 127.0.0.1:{relay_port}.")
            self.relay = LocalRelayService(config.to_proxy_endpoint(), RelayConfig(scheme, bind_port=relay_port), observer=self.observer)
            self.relay.start()
            host, port, relay_active = "127.0.0.1", relay_port, True
        udp_tunnel_enabled = self._should_start_udp_tunnel(config)
        if scheme == "socks5" and udp_tunnel_enabled:
            tunnel_active = self.tun_manager.start(config.to_proxy_endpoint())
            if config.rtc_mode == "strict" and not tunnel_active:
                return LaunchResult(False, "UDP tunnel unavailable. Screen share requires tun2socks.exe and wintun.dll in strict mode.", relay_active)
        elif scheme == "socks5" and config.rtc_mode == "strict":
            self.logger.info("Railway TCP proxy detected. Using TCP-only RTC fallback policy.")
        if config.rtc_mode == "strict":
            self.logger.info("Applying strict WebRTC anti-leak policy (disable_non_proxied_udp).")
            if udp_tunnel_enabled:
                self.logger.info("DNS resolution forced through proxy tunnel.")
            else:
                self.logger.info("UDP tunnel disabled for this upstream. RTC will use proxy-compatible TCP fallback only.")
        else:
            self.logger.info("Applying media-compatible RTC policy for voice and streams.")
        self._observe_launch_policy(scheme, host, port, config.rtc_mode, relay_active)
        self.logger.info("Starting Discord with proxy configuration.")
        self.process = subprocess.Popen(
            self._build_launch_args(config.discord_path, scheme, host, port, config.rtc_mode),
            **self._build_discord_process_kwargs(),
        )
        self.output_thread = threading.Thread(target=self._read_discord_output, daemon=True)
        self.output_thread.start()
        # Start monitor thread to watch process exit
        self.monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
        self.monitor_thread.start()
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

    def is_active(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def _build_launch_args(self, discord_path: str, proxy_scheme: str, proxy_host: str, proxy_port: int, rtc_mode: str = "strict") -> List[str]:
        args = [
            discord_path,
            f"--proxy-server={proxy_scheme}://{proxy_host}:{proxy_port}",
            f"--proxy-bypass-list={BYPASS_LIST}",
            "--enforce-webrtc-ip-permission-check",
            "--disable-quic",
        ]
        if rtc_mode == "strict":
            args.extend([
                "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
                "--disable-features=WebRtcHideLocalIpsWithMdns",
                "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
            ])
        else:
            args.append("--force-webrtc-ip-handling-policy=default_public_interface_only")
        return args

    def _should_start_udp_tunnel(self, config: AppConfig) -> bool:
        if config.rtc_mode != "strict":
            return False
        if config.proxy_type.lower() != "socks5":
            return False
        return not self._is_railway_tcp_proxy(config.host)

    def _is_railway_tcp_proxy(self, host: str) -> bool:
        normalized = (host or "").strip().lower().rstrip(".")
        return normalized.endswith(".proxy.rlwy.net") or normalized.endswith(".rlwy.net")

    def _select_relay_port(self, preferred_port: int = 9050) -> int:
        if self._can_bind_relay_port(preferred_port):
            return preferred_port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])

    def _can_bind_relay_port(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", int(port)))
            except OSError:
                return False
            return True

    def _build_discord_process_kwargs(self) -> dict:
        kwargs = hidden_subprocess_kwargs()
        kwargs.update(
            {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "encoding": "utf-8",
                "errors": "replace",
            }
        )
        return kwargs

    def _read_discord_output(self) -> None:
        if not self.process or not self.process.stdout:
            return
        with suppress(Exception):
            for line in self.process.stdout:
                self._handle_discord_output_line(line.rstrip())

    def _handle_discord_output_line(self, line: str) -> None:
        event = parse_discord_log_line(line)
        if event:
            self.observer.emit(event)

    def _observe_launch_policy(self, proxy_scheme: str, proxy_host: str, proxy_port: int, rtc_mode: str, relay_active: bool) -> None:
        transport = "SOCKS_TCP" if proxy_scheme == "socks5" else "HTTP_CONNECT"
        self.observer.emit(
            ConnectionEvent(
                connection_id=next_connection_id(),
                process="Discord",
                destination_hostname=proxy_host,
                destination_port=proxy_port,
                protocol="TCP",
                transport=transport,
                category=ConnectionCategory.CONTROL,
                result="launch_policy",
                metadata={"rtc_mode": rtc_mode, "relay_active": relay_active},
            )
        )

    def stop_existing_discord_instances(self) -> None:
        for process_name in DISCORD_PROCESS_NAMES:
            with suppress(Exception):
                subprocess.run(["taskkill", "/IM", process_name, "/F", "/T"], check=False, capture_output=True, text=True, **hidden_subprocess_kwargs())

    def _monitor_process(self) -> None:
        """Monitor Discord process and handle exit codes."""
        if not self.process:
            return
        exit_code = self.process.wait()
        self.logger.info(f"Discord process exited with code {exit_code}")
        self.stop()
        if exit_code == 2012:
            self.logger.warning("Detected 2012 error, restarting launcher.")
            restart()
        else:
            self.logger.info("Discord stopped without fatal error.")
