from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from .connection_classifier import ConnectionCategory
from .observability import ConnectionEvent, next_connection_id


class ScreenShareDiagnostics:
    def __init__(self, history_size: int = 80) -> None:
        self._events: Deque[ConnectionEvent] = deque(maxlen=history_size)

    def record(self, event: ConnectionEvent) -> Optional[ConnectionEvent]:
        self._events.append(event)
        if not self._is_screen_share_timeout(event):
            return None
        return self._build_timeout_summary(event)

    def _is_screen_share_timeout(self, event: ConnectionEvent) -> bool:
        return (
            event.category == ConnectionCategory.SCREEN_SHARE
            and event.result == "video-stream-receiver-ready-timeout"
            and event.metadata.get("media_context") == "stream"
        )

    def _build_timeout_summary(self, failure_event: ConnectionEvent) -> ConnectionEvent:
        rtc_control = self._latest("rtc_control_connected")
        media_server = self._latest("rtc_media_server_connected")
        local_udp = self._latest("media_connected")
        low_fps = self._latest("stream-view-low-fps")

        return ConnectionEvent(
            connection_id=next_connection_id(),
            process="Discord",
            protocol="RTC",
            transport="DIAGNOSTIC",
            category=ConnectionCategory.SCREEN_SHARE,
            result="screen_share_diagnostic",
            error=failure_event.error,
            metadata={
                "failure": failure_event.result,
                "failure_connection_id": failure_event.connection_id,
                "rtc_control_endpoint": self._format_endpoint(rtc_control),
                "media_server_endpoint": self._format_endpoint(media_server),
                "local_udp_endpoint": self._format_endpoint(local_udp),
                "low_fps_seen": low_fps is not None,
                "diagnosis": self._diagnosis(rtc_control, media_server, local_udp),
            },
        )

    def _latest(self, result: str) -> Optional[ConnectionEvent]:
        for event in reversed(self._events):
            if event.category != ConnectionCategory.SCREEN_SHARE:
                continue
            if event.metadata.get("media_context") != "stream":
                continue
            if event.result == result:
                return event
        return None

    def _format_endpoint(self, event: Optional[ConnectionEvent]) -> Optional[str]:
        if event is None:
            return None
        host = event.destination_hostname or event.destination_ip
        if not host:
            return None
        return f"{host}:{event.destination_port}" if event.destination_port else host

    def _diagnosis(
        self,
        rtc_control: Optional[ConnectionEvent],
        media_server: Optional[ConnectionEvent],
        local_udp: Optional[ConnectionEvent],
    ) -> str:
        if not rtc_control:
            return "screen share timed out before RTC control websocket connected"
        if not media_server:
            return "screen share timed out before remote media server was reported connected"
        if not local_udp:
            return "screen share timed out before local UDP endpoint was reported connected"
        return "screen share timed out after RTC control and UDP media were reported connected"
