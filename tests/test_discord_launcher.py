import unittest
import socket
import subprocess
from unittest.mock import patch

from core.connection_classifier import ConnectionCategory
from core.config import AppConfig
from core.discord_launcher import DiscordLauncher


class FakeObserver:
    def __init__(self):
        self.events = []

    def emit(self, event, level=None):
        self.events.append(event)


class DiscordLauncherArgsTests(unittest.TestCase):
    def test_default_rtc_mode_blocks_non_proxied_udp(self):
        launcher = DiscordLauncher(observer=FakeObserver())

        args = launcher._build_launch_args("Discord.exe", "socks5", "proxy.example", 1080)

        self.assertIn("--force-webrtc-ip-handling-policy=disable_non_proxied_udp", args)
        self.assertIn("--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1", args)

    def test_media_rtc_mode_allows_discord_video_transport(self):
        launcher = DiscordLauncher()

        args = launcher._build_launch_args(
            "Discord.exe",
            "socks5",
            "proxy.example",
            1080,
            rtc_mode="media",
        )

        self.assertIn("--force-webrtc-ip-handling-policy=default_public_interface_only", args)
        self.assertNotIn("--force-webrtc-ip-handling-policy=disable_non_proxied_udp", args)
        self.assertFalse(any(arg.startswith("--host-resolver-rules=") for arg in args))

    def test_strict_rtc_mode_keeps_previous_anti_leak_flags(self):
        launcher = DiscordLauncher()

        args = launcher._build_launch_args(
            "Discord.exe",
            "socks5",
            "proxy.example",
            1080,
            rtc_mode="strict",
        )

        self.assertIn("--force-webrtc-ip-handling-policy=disable_non_proxied_udp", args)
        self.assertIn("--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1", args)
        self.assertIn("--disable-quic", args)

    def test_railway_proxy_is_treated_as_tcp_only_in_strict_mode(self):
        launcher = DiscordLauncher(observer=FakeObserver())
        config = AppConfig(
            host="altaria.proxy.rlwy.net",
            port=12345,
            proxy_type="SOCKS5",
            discord_path="Discord.exe",
            rtc_mode="strict",
        )

        self.assertFalse(launcher._should_start_udp_tunnel(config))

    def test_non_railway_socks_proxy_can_use_udp_tunnel_in_strict_mode(self):
        launcher = DiscordLauncher(observer=FakeObserver())
        config = AppConfig(
            host="proxy.example",
            port=1080,
            proxy_type="SOCKS5",
            discord_path="Discord.exe",
            rtc_mode="strict",
        )

        self.assertTrue(launcher._should_start_udp_tunnel(config))

    def test_process_monitor_is_a_launcher_method(self):
        self.assertTrue(hasattr(DiscordLauncher, "_monitor_process"))

    def test_launch_policy_is_observed_without_starting_discord(self):
        observer = FakeObserver()
        launcher = DiscordLauncher(observer=observer)

        launcher._observe_launch_policy("socks5", "127.0.0.1", 9050, "media", relay_active=True)

        self.assertEqual(1, len(observer.events))
        event = observer.events[0]
        self.assertEqual(ConnectionCategory.CONTROL, event.category)
        self.assertEqual("SOCKS_TCP", event.transport)
        self.assertEqual("launch_policy", event.result)
        self.assertIsNone(event.error)
        self.assertEqual("media", event.metadata["rtc_mode"])
        self.assertTrue(event.metadata["relay_active"])
        self.assertEqual("127.0.0.1", event.destination_hostname)

    def test_discord_process_output_is_captured_for_diagnostics(self):
        launcher = DiscordLauncher()

        kwargs = launcher._build_discord_process_kwargs()

        self.assertEqual(subprocess.PIPE, kwargs["stdout"])
        self.assertEqual(subprocess.STDOUT, kwargs["stderr"])
        self.assertTrue(kwargs["text"])

    def test_discord_output_line_emits_rtc_diagnostic_event(self):
        observer = FakeObserver()
        launcher = DiscordLauncher(observer=observer)

        launcher._handle_discord_output_line(
            "14:58:02.958 > [RTCConnection(1545493147713405060, stream)] RTC connected to media server: 104.29.156.169:19294"
        )

        self.assertEqual(1, len(observer.events))
        self.assertEqual(ConnectionCategory.SCREEN_SHARE, observer.events[0].category)
        self.assertEqual("rtc_media_server_connected", observer.events[0].result)

    def test_strict_socks_launch_fails_when_udp_tunnel_is_unavailable(self):
        launcher = DiscordLauncher(observer=FakeObserver())
        config = AppConfig(
            host="proxy.example",
            port=1080,
            proxy_type="SOCKS5",
            discord_path="Discord.exe",
            rtc_mode="strict",
        )

        with patch("core.discord_launcher.os.path.isfile", return_value=True), patch.object(launcher.tun_manager, "start", return_value=False):
            result = launcher.start(config)

        self.assertFalse(result.ok)
        self.assertIn("UDP tunnel unavailable", result.message)

    def test_strict_railway_launch_does_not_require_udp_tunnel(self):
        launcher = DiscordLauncher(observer=FakeObserver())
        config = AppConfig(
            host="altaria.proxy.rlwy.net",
            port=12345,
            proxy_type="SOCKS5",
            discord_path="Discord.exe",
            rtc_mode="strict",
        )

        with (
            patch("core.discord_launcher.os.path.isfile", return_value=True),
            patch.object(launcher, "stop_existing_discord_instances"),
            patch.object(launcher.tun_manager, "start", return_value=False) as tun_start,
            patch("core.discord_launcher.subprocess.Popen") as popen,
        ):
            popen.return_value.stdout = []
            popen.return_value.poll.return_value = None
            result = launcher.start(config)

        self.assertTrue(result.ok)
        tun_start.assert_not_called()

    def test_select_relay_port_skips_port_that_is_already_in_use(self):
        launcher = DiscordLauncher(observer=FakeObserver())
        occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)

        try:
            preferred_port = occupied.getsockname()[1]
            selected_port = launcher._select_relay_port(preferred_port)
        finally:
            occupied.close()

        self.assertNotEqual(preferred_port, selected_port)
        self.assertGreater(selected_port, 0)


if __name__ == "__main__":
    unittest.main()
