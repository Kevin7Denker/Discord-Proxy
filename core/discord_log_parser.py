from __future__ import annotations

import json
import re
from typing import Optional
from urllib.parse import urlparse

from .connection_classifier import ConnectionCategory
from .observability import ConnectionEvent, next_connection_id


_RTC_CONTROL_RE = re.compile(r"\[RTCControlSocket\((?P<context>[^)]+)\)\]\s+\[(?P<state>CONNECT|CONNECTED)\]\s+(?P<url>wss://\S+)")
_MEDIA_LOCAL_RE = re.compile(
    r"\[Connection\((?P<context>[^)]+)\)\]\s+Connected with local address (?P<ip>\[[^\]]+\]|[^:\s]+):(?P<port>\d+) and protocol: (?P<protocol>\w+)"
)
_MEDIA_SERVER_RE = re.compile(
    r"\[RTCConnection\([^,]+,\s*(?P<context>[^)]+)\)\]\s+RTC connected to media server: (?P<ip>\[[^\]]+\]|[^:\s]+):(?P<port>\d+)"
)
_AV_ERROR_RE = re.compile(r"\[AVError\]\s+AV error reported:\s+(?P<name>[a-z0-9-]+)\s+(?P<payload>\{.*\})")


def parse_discord_log_line(line: str) -> Optional[ConnectionEvent]:
    return (
        _parse_rtc_control(line)
        or _parse_media_local_connection(line)
        or _parse_media_server_connection(line)
        or _parse_av_error(line)
    )


def _category_for_context(context: str) -> ConnectionCategory:
    return ConnectionCategory.SCREEN_SHARE if context == "stream" else ConnectionCategory.VOICE


def _parse_rtc_control(line: str) -> Optional[ConnectionEvent]:
    match = _RTC_CONTROL_RE.search(line)
    if not match:
        return None
    parsed = urlparse(match.group("url"))
    context = match.group("context")
    state = match.group("state").lower()
    return ConnectionEvent(
        connection_id=next_connection_id(),
        process="Discord",
        destination_hostname=parsed.hostname,
        destination_port=parsed.port or 443,
        protocol="TCP",
        transport="RTC_CONTROL_WEBSOCKET",
        category=_category_for_context(context),
        result=f"rtc_control_{state.lower()}",
        metadata={"media_context": context, "source": "discord_log"},
    )


def _parse_media_local_connection(line: str) -> Optional[ConnectionEvent]:
    match = _MEDIA_LOCAL_RE.search(line)
    if not match:
        return None
    context = match.group("context")
    protocol = match.group("protocol").upper()
    transport = "DIRECT_UDP" if protocol == "UDP" else "DIRECT_TCP"
    return ConnectionEvent(
        connection_id=next_connection_id(),
        process="Discord",
        destination_ip=match.group("ip").strip("[]"),
        destination_port=int(match.group("port")),
        protocol=protocol,
        transport=transport,
        category=_category_for_context(context),
        result="media_connected",
        metadata={"media_context": context, "source": "discord_log", "address_role": "local"},
    )


def _parse_media_server_connection(line: str) -> Optional[ConnectionEvent]:
    match = _MEDIA_SERVER_RE.search(line)
    if not match:
        return None
    context = match.group("context")
    return ConnectionEvent(
        connection_id=next_connection_id(),
        process="Discord",
        destination_ip=match.group("ip").strip("[]"),
        destination_port=int(match.group("port")),
        protocol="UDP",
        transport="DIRECT_UDP",
        category=_category_for_context(context),
        result="rtc_media_server_connected",
        metadata={"media_context": context, "source": "discord_log", "address_role": "remote"},
    )


def _parse_av_error(line: str) -> Optional[ConnectionEvent]:
    match = _AV_ERROR_RE.search(line)
    if not match:
        return None
    payload = _parse_json_payload(match.group("payload"))
    context = str(payload.get("mediaContext") or "unknown")
    return ConnectionEvent(
        connection_id=next_connection_id(),
        process="Discord",
        protocol="RTC",
        transport="DISCORD_MEDIA_ENGINE",
        category=_category_for_context(context),
        result=match.group("name"),
        error=match.group("name"),
        metadata={
            "media_context": context,
            "source": "discord_log",
            "payload": payload,
        },
    )


def _parse_json_payload(payload: str) -> dict:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
