from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx


@dataclass
class ProxyEndpoint:
    host: str
    port: int
    proxy_type: str = "socks5"
    username: str = ""
    password: str = ""


def build_proxy_url(endpoint: ProxyEndpoint, include_auth: bool = True) -> str:
    scheme = (endpoint.proxy_type or "socks5").lower()
    if scheme not in {"socks5", "http", "https"}:
        scheme = "socks5"
    auth = ""
    if include_auth and endpoint.username:
        auth = f"{quote(endpoint.username, safe='')}:{quote(endpoint.password or '', safe='')}@"
    return f"{scheme}://{auth}{endpoint.host.strip()}:{int(endpoint.port)}"


async def test_proxy_connectivity(endpoint: ProxyEndpoint, timeout_seconds: float = 12.0) -> Dict[str, Any]:
    if not endpoint.host.strip():
        return {"ok": False, "error": "Proxy host is required."}
    if not endpoint.port:
        return {"ok": False, "error": "Proxy port is required."}
    start = time.perf_counter()
    try:
        timeout = httpx.Timeout(timeout_seconds, connect=min(8.0, timeout_seconds))
        async with httpx.AsyncClient(proxy=build_proxy_url(endpoint), timeout=timeout, follow_redirects=True) as client:
            response = await client.get("http://ip-api.com/json")
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    if payload.get("status") == "fail":
        return {"ok": False, "error": payload.get("message", "Unknown proxy test failure")}
    return {"ok": True, "ip": payload.get("query", "Unknown"), "country": payload.get("country", "Unknown"), "city": payload.get("city", "Unknown"), "latency_ms": int((time.perf_counter() - start) * 1000)}


class TunManager:
    _BINARY_NAME = "tun2socks.exe"
    _CREATE_NO_WINDOW = 0x08000000

    def __init__(self, logger):
        self.logger = logger
        self._process: Optional[subprocess.Popen] = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def find_binary(self) -> Optional[str]:
        locations = [Path(__file__).resolve().parent.parent / self._BINARY_NAME, Path.cwd() / self._BINARY_NAME]
        for location in locations:
            if location.is_file():
                return str(location)
        return shutil.which(self._BINARY_NAME)

    def start(self, endpoint: ProxyEndpoint) -> bool:
        if self.is_running:
            return True
        binary = self.find_binary()
        if not binary:
            self.logger.warning("tun2socks.exe not found. UDP tunneling unavailable.")
            return False
        try:
            self._process = subprocess.Popen([binary, "-device", "tun://tun-discord", "-proxy", build_proxy_url(endpoint)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=self._CREATE_NO_WINDOW)
            self.logger.info("tun2socks active. UDP traffic tunneled through SOCKS5.")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to start tun2socks: {exc}")
            self._process = None
            return False

    def stop(self) -> None:
        if self._process is None:
            return
        try:
            self._process.terminate()
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
        except Exception:
            pass
        finally:
            self._process = None