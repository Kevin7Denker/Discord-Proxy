import unittest

from core.discord_launcher import DiscordLauncher


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


if __name__ == "__main__":
    unittest.main()
