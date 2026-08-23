import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

proxy_stub = types.ModuleType("core.proxy")


class ProxyEndpoint:
    def __init__(self, host, port, proxy_type, username, password):
        self.host = host
        self.port = port
        self.proxy_type = proxy_type
        self.username = username
        self.password = password


proxy_stub.ProxyEndpoint = ProxyEndpoint
sys.modules.setdefault("core.proxy", proxy_stub)

from core.config import ConfigManager  # noqa: E402


class ConfigManagerPathTests(unittest.TestCase):
    def test_default_config_path_uses_local_app_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir}, clear=False):
                manager = ConfigManager()

        expected = Path(temp_dir) / "Discord Proxy" / "config.json"
        self.assertEqual(manager.config_path, expected)


if __name__ == "__main__":
    unittest.main()
