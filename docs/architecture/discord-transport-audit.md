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
      -> optional core.local_relay.LocalRelayService on 127.0.0.1:<available-port>
      -> optional tun2socks.exe start for strict SOCKS5 upstreams that are not Railway TCP proxies
      -> Discord.exe with Chromium proxy and WebRTC flags
```

## Confirmed Behavior

- Proxy configuration is loaded from `.env`, with optional custom proxy preferences in `prefs.json`.
- The Discord process is launched with `--proxy-server=<scheme>://<host>:<port>`.
- The proxy bypass list is `<-loopback>`.
- When upstream authentication is configured, the app starts a local relay on `127.0.0.1` using `9050` when available or another free ephemeral port when `9050` is already busy.
- The local relay supports HTTP `CONNECT` and SOCKS5 `CONNECT`.
- The local relay does not implement SOCKS5 `UDP ASSOCIATE`.
- `tun2socks.exe` plus `wintun.dll` are required for strict SOCKS5 upstreams that can use a local UDP tunnel. Railway hosts (`*.rlwy.net`) are treated as TCP-only upstreams and do not start the UDP tunnel.
- `strict` RTC mode is the default and uses `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` plus `--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1`.
- `strict` mode also disables QUIC to avoid Chromium opening HTTP/3/QUIC paths outside the TCP proxy route.
- `media` RTC mode is a legacy opt-in mode and uses `--force-webrtc-ip-handling-policy=default_public_interface_only`, allowing direct UDP media.
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

## 2026-09-04 Runtime Evidence

The pasted Discord runtime log showed the following screen-share sequence:

```text
RTCControlSocket(stream) CONNECT wss://c-ewr11-eb153ce8.discord.media:443/
RTCControlSocket(stream) CONNECTED in 1133 ms
Connection(stream) Creating connection to 104.29.156.169:19294
Connection(stream) Connected with local address 45.179.29.128:13236 and protocol: udp
RTCConnection(stream) RTC connected to media server: 104.29.156.169:19294
AVError video-stream-receiver-ready-timeout
RTCConnectionStore No VOICE_STATE_UPDATE received within 30000ms of VOICE_CHANNEL_SELECT
```

This proves the failure is not simply "Discord cannot reach `discord.media`". The RTC control websocket reached a `discord.media` endpoint, the media engine reported a UDP media connection, and the observed failure occurred later as `video-stream-receiver-ready-timeout`.

The current strongest hypothesis is a media-plane receive/readiness failure after RTC control and UDP setup, not an initial HTTPS, gateway, or control-plane failure. This still needs a paired broadcaster/viewer capture before changing routing.

## Discord Log Parser

The launcher now captures Discord stdout/stderr without opening extra console windows and parses RTC-related lines into structured connection events:

- `RTCControlSocket(<context>) [CONNECT|CONNECTED] wss://...`
- `Connection(<context>) Connected with local address ... protocol: udp`
- `RTCConnection(..., <context>) RTC connected to media server: ...`
- `AVError ... video-stream-receiver-ready-timeout`

These parsed events are emitted through the same `ConnectionObserver` path as relay events and are written to the JSONL connection log.

## Screen Share Diagnostic Summary

When `video-stream-receiver-ready-timeout` appears for `mediaContext=stream`, the observer now emits a derived `screen_share_diagnostic` event. This event summarizes the latest related screen-share events:

- RTC control endpoint.
- Remote media server endpoint.
- Local UDP endpoint.
- Whether `stream-view-low-fps` was observed before the timeout.
- A short diagnostic sentence describing whether the timeout happened before RTC control, before remote media server connection, before local UDP connection, or after RTC control plus UDP media were reported connected.

The summary is derived from observed events only. It does not rewrite routing decisions and does not assume UDP relay is required.

## Safety Notes

- The local relay remains bound to `127.0.0.1`.
- No new UDP relay was added in this phase.
- No fixed Cloudflare or Discord IP route was added.
- Unknown traffic is classified as `UNKNOWN` and is not blocked by classification.

## Railway TCP-Only Mode

Railway TCP Proxy can carry the upstream SOCKS5 TCP service, but it is not a reliable public UDP media path. For `*.rlwy.net` upstreams, strict mode therefore:

- skips `tun2socks` startup;
- keeps `disable_non_proxied_udp` to avoid direct local UDP leakage;
- disables QUIC;
- relies on Discord/Chromium proxy-compatible TCP fallback for RTC/media.

This is the best supported strategy when Railway is the only available host. It cannot override Discord-side regional or account policy decisions for video/screen-share availability.
