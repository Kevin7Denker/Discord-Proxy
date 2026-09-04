from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ConnectionCategory(str, Enum):
    CONTROL = "CONTROL"
    GATEWAY = "GATEWAY"
    API = "API"
    SIGNALING = "SIGNALING"
    MEDIA = "MEDIA"
    VOICE = "VOICE"
    VIDEO = "VIDEO"
    SCREEN_SHARE = "SCREEN_SHARE"
    TELEMETRY = "TELEMETRY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ClassificationResult:
    category: ConnectionCategory
    reason: str


def classify_connection(
    destination_hostname: Optional[str],
    destination_ip: Optional[str],
    destination_port: Optional[int],
    protocol: str,
) -> ClassificationResult:
    host = (destination_hostname or "").strip().lower().rstrip(".")

    if host:
        if host == "gateway.discord.gg":
            return ClassificationResult(ConnectionCategory.GATEWAY, "hostname")
        if host == "discord.com" or host.endswith(".discord.com"):
            return ClassificationResult(ConnectionCategory.API, "hostname")
        if host == "discord.media" or host.endswith(".discord.media"):
            return ClassificationResult(ConnectionCategory.MEDIA, "hostname")
        if "telemetry" in host or host.endswith(".dc-telemetry.net"):
            return ClassificationResult(ConnectionCategory.TELEMETRY, "hostname")

    return ClassificationResult(ConnectionCategory.UNKNOWN, "fallback")
