from __future__ import annotations

from enum import Enum
import socket


class DnsResult(str, Enum):
    OK = "OK"
    NXDOMAIN = "NXDOMAIN"
    SERVFAIL = "SERVFAIL"
    TIMEOUT = "TIMEOUT"
    DNS_UNAVAILABLE = "DNS_UNAVAILABLE"
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE"
    ERROR = "ERROR"


def classify_dns_error(error: BaseException) -> DnsResult:
    if isinstance(error, TimeoutError):
        return DnsResult.TIMEOUT

    if isinstance(error, socket.gaierror):
        code = error.errno
        if code in {getattr(socket, "EAI_NONAME", object()), getattr(socket, "EAI_NODATA", object())}:
            return DnsResult.NXDOMAIN
        if code == getattr(socket, "EAI_AGAIN", object()):
            return DnsResult.SERVFAIL
        if code == getattr(socket, "EAI_FAIL", object()):
            return DnsResult.DNS_UNAVAILABLE

    if isinstance(error, OSError) and getattr(error, "errno", None) in {10051, 101}:
        return DnsResult.NETWORK_UNAVAILABLE

    return DnsResult.ERROR
