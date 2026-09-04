import unittest

from core.connection_classifier import ConnectionCategory
from core.discord_launcher import DiscordLauncher


class FakeObserver:
    def __init__(self):
        self.events = []

    def emit(self, event, level=None):
        self.events.append(event)


class DiscordLauncherArgsTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
