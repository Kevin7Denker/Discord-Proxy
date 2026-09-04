# Discord Transport Audit

## Scope

This document records the current Discord Proxie transport architecture before any media-plane transport changes. It separates confirmed behavior from hypotheses that still require runtime capture.

## Current Architecture

```text
pywebview UI
  -> desktop.api_bridge.ApiBridge.start_discord()
  -> core.network_service.test_proxy_connectivity()
      -> HTTP request to ip-api.com through configured upstream proxy
  -> core.discord_launcher.DiscordLauncher.start()
      -> optional core.local_relay.LocalRelayService on 127.0.0.1:9050
      -> optional tun2socks.exe start when proxy type is SOCKS5
      -> Discord.exe with Chromium proxy and WebRTC flags
```

## Confirmed Behavior

- Proxy configuration is loaded from `.env`, with optional custom proxy preferences in `prefs.json`.
- The Discord process is launched with `--proxy-server=<scheme>://<host>:<port>`.
- The proxy bypass list is `<-loopback>`.
- When upstream authentication is configured, the app starts a local relay on `127.0.0.1:9050`.
- The local relay supports HTTP `CONNECT` and SOCKS5 `CONNECT`.
- The local relay does not implement SOCKS5 `UDP ASSOCIATE`.
- `tun2socks.exe` is optional. If it is absent, UDP tunneling is unavailable and the app continues.
- `media` RTC mode uses `--force-webrtc-ip-handling-policy=default_public_interface_only`.
- `strict` RTC mode uses `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` and `--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1`.
- Runtime logs before this phase were UI/status lines, not structured connection telemetry.

## Current Gaps

- No per-connection `connection_id`.
- No structured event for destination hostname, destination IP, port, protocol, transport, category, DNS result, latency, bytes, duration, or error.
- No process-level runtime capture for Discord TCP/UDP sockets.
- No classification layer for control plane vs media plane.
- No central routing policy engine.
- No proven evidence yet that screen share error `2012` is caused by UDP, TCP fallback, DNS, signaling, or Discord-side policy.
- No UDP relay is implemented in the Python local relay.
- No guarantees that subprocesses or Discord media internals obey Chromium proxy flags.

## Old Diagram

```text
Discord/Electron
  -> Chromium proxy flags
      -> HTTP/SOCKS CONNECT
      -> upstream proxy or local authenticated TCP relay
  -> WebRTC/RTC media behavior
      -> controlled only by Chromium/WebRTC flags
      -> no local classification
      -> no per-connection telemetry
```

## Proposed Direction

```text
Discord Launcher
  -> Observability
  -> Connection Classifier
  -> Routing Policy Engine
  -> TransportManager
      -> Socks5TcpTransport
      -> DirectTransport
      -> DirectUdpTransport
      -> Socks5UdpTransport or TunnelUdpTransport only if telemetry proves need
```

## Phase 2 Implemented Observability

Phase 2 introduces:

- `ConnectionEvent` for structured telemetry.
- `ConnectionObserver` for compact UI logs and optional JSONL sink.
- `connection_id` generation.
- Basic hostname-based classification for API, gateway, media, telemetry, and unknown traffic.
- IP version detection for IPv4 and IPv6.
- DNS error classification for NXDOMAIN, SERVFAIL, timeout, DNS unavailable, network unavailable, and generic error.
- Instrumentation hooks in the Discord launcher, local TCP relay, and optional `tun2socks` manager.

## Runtime Capture Still Required

The following must be captured during real Discord startup, voice, and screen share sessions:

- DNS resolver used by the Discord process.
- TCP destinations created by Discord and child processes.
- UDP endpoints opened by Discord and child processes.
- Whether `discord.media` and `latency.discord.media` are involved before error `2012`.
- Whether screen share failure happens before media UDP, during ICE/RTC negotiation, during TCP fallback, or after signaling.
- Whether broadcaster and viewer use different endpoint/protocol sequences.

## Safety Notes

- The local relay remains bound to `127.0.0.1`.
- No new UDP relay was added in this phase.
- No fixed Cloudflare or Discord IP route was added.
- Unknown traffic is classified as `UNKNOWN` and is not blocked by classification.
