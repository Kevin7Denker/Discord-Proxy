import tempfile
import unittest
from pathlib import Path

from scripts.build import prepare_release_env


class BuildReleaseEnvTests(unittest.TestCase):
    def test_local_env_is_packaged_when_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("PROXY_HOST=real.proxy.local\n", encoding="utf-8")
            (root / ".env.example").write_text("PROXY_HOST=127.0.0.1\n", encoding="utf-8")

            release_env = prepare_release_env(root)

            self.assertIsNotNone(release_env)
            self.assertEqual("PROXY_HOST=real.proxy.local\n", release_env.read_text(encoding="utf-8"))

    def test_env_example_is_only_used_as_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.example").write_text("PROXY_HOST=127.0.0.1\n", encoding="utf-8")

            release_env = prepare_release_env(root)

            self.assertIsNotNone(release_env)
            self.assertEqual("PROXY_HOST=127.0.0.1\n", release_env.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
