import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.network_service import ProxyEndpoint, TunManager


class FakeLogger:
    def __init__(self):
        self.messages = []

    def warning(self, message):
        self.messages.append(("WARN", message))

    def info(self, message):
        self.messages.append(("INFO", message))

    def error(self, message):
        self.messages.append(("ERROR", message))


class TunManagerTests(unittest.TestCase):
    def test_requires_tun2socks_and_wintun_side_by_side(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "tun2socks.exe").write_text("", encoding="utf-8")
            logger = FakeLogger()
            manager = TunManager(logger)

            with patch("core.network_service.get_base_path", return_value=base), patch("core.network_service.shutil.which", return_value=None):
                self.assertIsNone(manager.find_runtime())

            self.assertIn(("WARN", "wintun.dll not found next to tun2socks.exe. UDP tunneling unavailable."), logger.messages)

    def test_builds_windows_wintun_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            binary = base / "tun2socks.exe"
            binary.write_text("", encoding="utf-8")
            (base / "wintun.dll").write_text("", encoding="utf-8")
            manager = TunManager(FakeLogger())

            command = manager.build_command(str(binary), ProxyEndpoint("proxy.example", 1080, "SOCKS5", "u", "p"))

            self.assertEqual(str(binary), command[0])
            self.assertIn("--device", command)
            self.assertIn("wintun", command)
            self.assertIn("--proxy", command)
            self.assertIn("socks5://u:p@proxy.example:1080", command)
            self.assertIn("--udp-timeout", command)


if __name__ == "__main__":
    unittest.main()
