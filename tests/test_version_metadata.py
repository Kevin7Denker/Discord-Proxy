import unittest
from pathlib import Path

from scripts.build_setup import APP_VERSION


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "1.2"


class VersionMetadataTests(unittest.TestCase):
    def test_app_shows_release_version(self):
        contents = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

        self.assertIn(f"v{EXPECTED_VERSION}", contents)

    def test_installer_metadata_uses_release_version(self):
        for relative_path in ("scripts/installer.iss", "installer/installer.iss"):
            with self.subTest(relative_path=relative_path):
                contents = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn(f'#define MyAppVersion "{EXPECTED_VERSION}"', contents)

    def test_iexpress_metadata_uses_release_version(self):
        self.assertEqual(EXPECTED_VERSION, APP_VERSION)


if __name__ == "__main__":
    unittest.main()
