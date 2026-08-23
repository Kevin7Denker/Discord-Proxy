from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import socket
import threading
from typing import Optional, Tuple

from python_socks.async_.asyncio import Proxy

from .proxy import ProxyEndpoint, build_proxy_url


@dataclass
class RelayConfig:
    mode: str
    bind_host: str = "127.0.0.1"
    bind_port: int = 9050


class LocalRelayService:
    def __init__(self, upstream: ProxyEndpoint, config: Optional[RelayConfig] = None):
        self.upstream = upstream
        self.config = config or RelayConfig(mode=upstream.proxy_type.lower())
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

    async def _bridge(self, left_reader, left_writer, right_reader, right_writer) -> None:
        async def pipe(reader, writer) -> None:
            try:
                while data := await reader.read(65536):
                    writer.write(data)
                    await writer.drain()
            except Exception:
                pass
            finally:
                with suppress(Exception):
                    writer.close()
                    await writer.wait_closed()
        tasks = [asyncio.create_task(pipe(left_reader, right_writer)), asyncio.create_task(pipe(right_reader, left_writer))]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            with suppress(Exception):
                task.result()

    async def _handle_http_client(self, reader, writer) -> None:
        try:
            parts = (await reader.readline()).decode("utf-8", errors="replace").strip().split()
            while await reader.readline() not in (b"\r\n", b"\n", b""):
                pass
            if len(parts) != 3 or parts[0].upper() != "CONNECT" or ":" not in parts[1]:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                await writer.drain()
                return
            host, port_text = parts[1].rsplit(":", 1)
            up_reader, up_writer = await self._open_upstream_stream(host, int(port_text))
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()
            await self._bridge(reader, writer, up_reader, up_writer)
        except Exception:
            with suppress(Exception):
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain()
        finally:
            with suppress(Exception):
                writer.close()
                await writer.wait_closed()

    async def _handle_socks5_client(self, reader, writer) -> None:
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
            up_reader, up_writer = await self._open_upstream_stream(host, port)
            writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()
            await self._bridge(reader, writer, up_reader, up_writer)
        except Exception:
            with suppress(Exception):
                writer.write(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
                await writer.drain()
        finally:
            with suppress(Exception):
                writer.close()
                await writer.wait_closed()