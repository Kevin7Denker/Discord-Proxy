import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


dotenv_stub = types.ModuleType("dotenv")


def load_dotenv_stub(path, override=False):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if override or key not in os.environ:
            os.environ[key] = value


dotenv_stub.load_dotenv = load_dotenv_stub
sys.modules.setdefault("dotenv", dotenv_stub)

network_service_stub = types.ModuleType("core.network_service")


class ProxyEndpoint:
    def __init__(self, host, port, proxy_type, username, password):
        self.host = host
        self.port = port
        self.proxy_type = proxy_type
        self.username = username
        self.password = password


network_service_stub.ProxyEndpoint = ProxyEndpoint
sys.modules.setdefault("core.network_service", network_service_stub)

from core.config import ConfigManager


class ConfigManagerProxyPreferenceTests(unittest.TestCase):
    def build_manager(self, env_text: str, prefs: dict | None = None) -> tuple[ConfigManager, Path]:
        temp_context = tempfile.TemporaryDirectory()
        self.addCleanup(temp_context.cleanup)
        base_path = Path(temp_context.name)
        env_path = base_path / ".env"
        env_path.write_text(env_text, encoding="utf-8")
        if prefs is not None:
            (base_path / "prefs.json").write_text(json.dumps(prefs), encoding="utf-8")

        patches = [
            patch("core.config.get_base_path", return_value=base_path),
            patch("core.config.get_env_path", return_value=env_path),
            patch("core.config.find_discord_executable", return_value=""),
            patch.dict(os.environ, {}, clear=True),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

        return ConfigManager(), base_path

    def test_env_proxy_is_used_when_custom_proxy_is_disabled(self):
        manager, _ = self.build_manager(
            "PROXY_HOST=env.proxy.local\nPROXY_PORT=1081\nPROXY_TYPE=SOCKS5\n",
            {
                "custom_proxy_enabled": False,
                "custom_proxy": {
                    "host": "custom.proxy.local",
                    "port": 8080,
                    "proxy_type": "HTTP",
                    "username": "user",
                    "password": "pass",
                },
            },
        )

        self.assertFalse(manager.config.custom_proxy_enabled)
        self.assertEqual(manager.config.host, "env.proxy.local")
        self.assertEqual(manager.config.port, 1081)
        self.assertEqual(manager.config.proxy_type, "SOCKS5")
        self.assertEqual(manager.config.username, "")
        self.assertEqual(manager.config.password, "")

    def test_enabled_custom_proxy_overrides_env_proxy(self):
        manager, _ = self.build_manager(
            "PROXY_HOST=env.proxy.local\nPROXY_PORT=1081\nPROXY_TYPE=SOCKS5\nPROXY_USER=env-user\nPROXY_PASS=env-pass\n",
            {
                "custom_proxy_enabled": True,
                "custom_proxy": {
                    "host": "custom.proxy.local",
                    "port": 8080,
                    "proxy_type": "HTTP",
                    "username": "custom-user",
                    "password": "custom-pass",
                },
            },
        )

        self.assertTrue(manager.config.custom_proxy_enabled)
        self.assertEqual(manager.config.host, "custom.proxy.local")
        self.assertEqual(manager.config.port, 8080)
        self.assertEqual(manager.config.proxy_type, "HTTP")
        self.assertEqual(manager.config.username, "custom-user")
        self.assertEqual(manager.config.password, "custom-pass")

    def test_reset_custom_proxy_returns_to_env_and_clears_saved_proxy(self):
        manager, base_path = self.build_manager(
            "PROXY_HOST=env.proxy.local\nPROXY_PORT=1081\nPROXY_TYPE=SOCKS5\n",
            {
                "language": "pt-BR",
                "theme": "light",
                "custom_proxy_enabled": True,
                "custom_proxy": {
                    "host": "custom.proxy.local",
                    "port": 8080,
                    "proxy_type": "HTTP",
                    "username": "custom-user",
                    "password": "custom-pass",
                },
            },
        )

        manager.reset_custom_proxy()

        self.assertFalse(manager.config.custom_proxy_enabled)
        self.assertEqual(manager.config.host, "env.proxy.local")
        self.assertEqual(manager.config.port, 1081)
        saved_prefs = json.loads((base_path / "prefs.json").read_text(encoding="utf-8"))
        self.assertEqual(saved_prefs["language"], "pt-BR")
        self.assertEqual(saved_prefs["theme"], "light")
        self.assertFalse(saved_prefs["custom_proxy_enabled"])
        self.assertNotIn("custom_proxy", saved_prefs)


if __name__ == "__main__":
    unittest.main()
