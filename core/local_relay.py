from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import ipaddress
import socket
import threading
import time
from typing import Optional, Tuple

from python_socks.async_.asyncio import Proxy

from .connection_classifier import classify_connection
from .network_service import ProxyEndpoint, build_proxy_url
from .observability import ConnectionEvent, ConnectionObserver, LogLevel, next_connection_id


@dataclass
class RelayConfig:
    mode: str
    bind_host: str = "127.0.0.1"
    bind_port: int = 9050


class LocalRelayService:
    def __init__(self, upstream: ProxyEndpoint, config: Optional[RelayConfig] = None, observer: Optional[ConnectionObserver] = None):
        self.upstream = upstream
        self.config = config or RelayConfig(mode=upstream.proxy_type.lower())
        self.observer = observer
        self._loop = None
        self._server = None
        self._thread = None
        self._started = threading.Event()
        self._startup_error = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._started.clear()
        self._startup_error = None
        self._thread = threading.Thread(target=self._run_loop, name="local-relay", daemon=True)
        self._thread.start()
        self._started.wait(timeout=5)
        if self._startup_error is not None:
            raise RuntimeError(f"Failed to start local relay: {self._startup_error}") from self._startup_error

    def stop(self) -> None:
        if not self._loop:
            return
        self._loop.call_soon_threadsafe(self._shutdown)
        if self._thread:
            self._thread.join(timeout=5)
        self._loop = None
        self._thread = None

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def boot() -> None:
            handler = self._handle_socks5_client if self.config.mode.lower() == "socks5" else self._handle_http_client
            self._server = await asyncio.start_server(handler, self.config.bind_host, self.config.bind_port)

        try:
            self._loop.run_until_complete(boot())
        except Exception as exc:
            self._startup_error = exc
            self._started.set()
            return
        self._started.set()
        self._loop.run_forever()
        with suppress(Exception):
            if self._server:
                self._server.close()
                self._loop.run_until_complete(self._server.wait_closed())
        self._loop.close()

    def _shutdown(self) -> None:
        if self._server:
            self._server.close()
        if self._loop:
            self._loop.stop()

    async def _open_upstream_stream(self, host: str, port: int) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        sock = await Proxy.from_url(build_proxy_url(self.upstream)).connect(dest_host=host, dest_port=port)
        return await asyncio.open_connection(sock=sock)

    async def _bridge(self, left_reader, left_writer, right_reader, right_writer) -> Tuple[int, int]:
        counters = {"sent": 0, "received": 0}

        async def pipe(reader, writer, counter_key: str) -> None:
            try:
                while data := await reader.read(65536):
                    counters[counter_key] += len(data)
                    writer.write(data)
                    await writer.drain()
            except Exception:
                pass
            finally:
                with suppress(Exception):
                    writer.close()
                    await writer.wait_closed()
        tasks = [
            asyncio.create_task(pipe(left_reader, right_writer, "sent")),
            asyncio.create_task(pipe(right_reader, left_writer, "received")),
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            with suppress(Exception):
                task.result()
        return counters["sent"], counters["received"]

    def _build_connect_event(
        self,
        connection_id: str,
        host: str,
        port: int,
        protocol: str,
        transport: str,
        result: str,
        latency_ms: Optional[int] = None,
        bytes_sent: Optional[int] = None,
        bytes_received: Optional[int] = None,
        connection_duration_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> ConnectionEvent:
        destination_hostname = host
        destination_ip = None
        with suppress(ValueError):
            ipaddress.ip_address(host)
            destination_hostname = None
            destination_ip = host
        classification = classify_connection(destination_hostname, destination_ip, port, protocol)
        return ConnectionEvent(
            connection_id=connection_id,
            process="Discord",
            destination_hostname=destination_hostname,
            destination_ip=destination_ip,
            destination_port=port,
            protocol=protocol,
            transport=transport,
            category=classification.category,
            result=result,
            latency_ms=latency_ms,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
            connection_duration_ms=connection_duration_ms,
            error=error,
        )

    def _observe_connect(self, event: ConnectionEvent, level: LogLevel = LogLevel.INFO) -> None:
        if self.observer:
            self.observer.emit(event, level=level)

    async def _handle_http_client(self, reader, writer) -> None:
        connection_id = next_connection_id()
        started = time.perf_counter()
        host = None
        port = None
        try:
            parts = (await reader.readline()).decode("utf-8", errors="replace").strip().split()
            while await reader.readline() not in (b"\r\n", b"\n", b""):
                pass
            if len(parts) != 3 or parts[0].upper() != "CONNECT" or ":" not in parts[1]:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                await writer.drain()
                return
            host, port_text = parts[1].rsplit(":", 1)
            port = int(port_text)
            connect_started = time.perf_counter()
            up_reader, up_writer = await self._open_upstream_stream(host, port)
            latency_ms = int((time.perf_counter() - connect_started) * 1000)
            self._observe_connect(self._build_connect_event(connection_id, host, port, "TCP", "HTTP_CONNECT", "connected", latency_ms=latency_ms))
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()
            bytes_sent, bytes_received = await self._bridge(reader, writer, up_reader, up_writer)
            self._observe_connect(
                self._build_connect_event(
                    connection_id,
                    host,
                    port,
                    "TCP",
                    "HTTP_CONNECT",
                    "closed",
                    bytes_sent=bytes_sent,
                    bytes_received=bytes_received,
                    connection_duration_ms=int((time.perf_counter() - started) * 1000),
                ),
                level=LogLevel.DEBUG,
            )
        except Exception as exc:
            if host and port:
                self._observe_connect(self._build_connect_event(connection_id, host, port, "TCP", "HTTP_CONNECT", "error", error=str(exc)), level=LogLevel.ERROR)
            with suppress(Exception):
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain()
        finally:
            with suppress(Exception):
                writer.close()
                await writer.wait_closed()

    async def _handle_socks5_client(self, reader, writer) -> None:
        connection_id = next_connection_id()
        started = time.perf_counter()
        host = None
        port = None
        try:
            version, method_count = await reader.readexactly(2)
            if version != 5:
                return
            await reader.readexactly(method_count)
            writer.write(b"\x05\x00")
            await writer.drain()
            version, command, _, address_type = await reader.readexactly(4)
            if version != 5 or command != 1:
                writer.write(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00")
                await writer.drain()
                return
            if address_type == 1:
                host = socket.inet_ntoa(await reader.readexactly(4))
            elif address_type == 3:
                host = (await reader.readexactly((await reader.readexactly(1))[0])).decode("utf-8", errors="replace")
            elif address_type == 4:
                host = socket.inet_ntop(socket.AF_INET6, await reader.readexactly(16))
            else:
                return
            port = int.from_bytes(await reader.readexactly(2), "big")
            connect_started = time.perf_counter()
            up_reader, up_writer = await self._open_upstream_stream(host, port)
            latency_ms = int((time.perf_counter() - connect_started) * 1000)
            self._observe_connect(self._build_connect_event(connection_id, host, port, "TCP", "SOCKS_TCP", "connected", latency_ms=latency_ms))
            writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()
            bytes_sent, bytes_received = await self._bridge(reader, writer, up_reader, up_writer)
            self._observe_connect(
                self._build_connect_event(
                    connection_id,
                    host,
                    port,
                    "TCP",
                    "SOCKS_TCP",
                    "closed",
                    bytes_sent=bytes_sent,
                    bytes_received=bytes_received,
                    connection_duration_ms=int((time.perf_counter() - started) * 1000),
                ),
                level=LogLevel.DEBUG,
            )
        except Exception as exc:
            if host and port:
                self._observe_connect(self._build_connect_event(connection_id, host, port, "TCP", "SOCKS_TCP", "error", error=str(exc)), level=LogLevel.ERROR)
            with suppress(Exception):
                writer.write(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
                await writer.drain()
        finally:
            with suppress(Exception):
                writer.close()
                await writer.wait_closed()
