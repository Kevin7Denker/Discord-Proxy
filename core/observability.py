from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from itertools import count
from pathlib import Path
import ipaddress
import json
import threading
from typing import Any, Dict, Optional

from .connection_classifier import ConnectionCategory


class LogLevel(IntEnum):
    ERROR = 40
    WARN = 30
    INFO = 20
    DEBUG = 10
    TRACE = 5


_connection_counter = count(1)


def next_connection_id() -> str:
    return f"conn:{next(_connection_counter):06d}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def detect_ip_version(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return None
    return "IPv6" if address.version == 6 else "IPv4"


@dataclass
class ConnectionEvent:
    connection_id: str
    process: str
    protocol: str
    transport: str
    category: ConnectionCategory
    result: str
    timestamp: str = field(default_factory=utc_now)
    destination_hostname: Optional[str] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    dns_resolver: Optional[str] = None
    dns_result: Optional[str] = None
    latency_ms: Optional[int] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    connection_duration_ms: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "connection_id": self.connection_id,
            "process": self.process,
            "destination_hostname": self.destination_hostname,
            "destination_ip": self.destination_ip,
            "destination_port": self.destination_port,
            "ip_version": detect_ip_version(self.destination_ip),
            "protocol": self.protocol,
            "transport": self.transport,
            "category": self.category.value,
            "dns_resolver": self.dns_resolver,
            "dns_result": self.dns_result,
            "latency_ms": self.latency_ms,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "connection_duration_ms": self.connection_duration_ms,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    def to_compact_log_line(self) -> str:
        target = self.destination_hostname or self.destination_ip or "unknown"
        if self.destination_port:
            target = f"{target}:{self.destination_port}"
        parts = [
            f"[{self.connection_id}]",
            f"protocol={self.protocol}",
            f"transport={self.transport}",
            f"category={self.category.value}",
            f"target={target}",
            f"result={self.result}",
        ]
        ip_version = detect_ip_version(self.destination_ip)
        if ip_version:
            parts.append(f"ip_version={ip_version}")
        if self.latency_ms is not None:
            parts.append(f"latency_ms={self.latency_ms}")
        if self.connection_duration_ms is not None:
            parts.append(f"duration_ms={self.connection_duration_ms}")
        if self.error:
            parts.append(f"error={self.error}")
        return " ".join(parts)


class ConnectionObserver:
    def __init__(self, logger, level: LogLevel = LogLevel.INFO, sink_path: Optional[Path] = None) -> None:
        self.logger = logger
        self.level = level
        self.sink_path = sink_path
        self._lock = threading.Lock()

    def emit(self, event: ConnectionEvent, level: LogLevel = LogLevel.INFO) -> None:
        if level < self.level:
            return
        line = event.to_compact_log_line()
        self._log(level, line)
        self._write_jsonl(event)

    def _log(self, level: LogLevel, line: str) -> None:
        if level >= LogLevel.ERROR and hasattr(self.logger, "error"):
            self.logger.error(line)
        elif level >= LogLevel.WARN and hasattr(self.logger, "warning"):
            self.logger.warning(line)
        elif level <= LogLevel.DEBUG and hasattr(self.logger, "debug"):
            self.logger.debug(line)
        elif hasattr(self.logger, "info"):
            self.logger.info(line)

    def _write_jsonl(self, event: ConnectionEvent) -> None:
        if self.sink_path is None:
            return
        with self._lock:
            self.sink_path.parent.mkdir(parents=True, exist_ok=True)
            with self.sink_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(event.to_dict(), ensure_ascii=True) + "\n")
