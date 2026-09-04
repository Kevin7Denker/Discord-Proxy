import tempfile
import unittest
from pathlib import Path

from scripts.build_setup import write_sed


class BuildSetupTests(unittest.TestCase):
    def test_iexpress_launches_install_script_hidden(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sed_path = root / "setup.sed"

            write_sed(sed_path, root, root / "Setup.exe")

            contents = sed_path.read_text(encoding="utf-8")
            self.assertIn("AppLaunched=powershell.exe -WindowStyle Hidden", contents)


if __name__ == "__main__":
    unittest.main()
