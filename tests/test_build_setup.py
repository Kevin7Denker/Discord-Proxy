import tempfile
import unittest
from pathlib import Path

from scripts.build_setup import write_install_script, write_sed


class BuildSetupTests(unittest.TestCase):
    def test_install_script_stops_old_app_and_validates_python_dll(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script_path = root / "install.ps1"

            write_install_script(script_path)

            contents = script_path.read_text(encoding="utf-8")
            self.assertIn("Get-Process -Name \"DiscordProxie\"", contents)
            self.assertIn("Wait-Process", contents)
            self.assertIn("_internal\\python312.dll", contents)
            self.assertIn("_internal\\pythonnet\\runtime\\Python.Runtime.dll", contents)
            self.assertIn("throw \"Install validation failed", contents)

    def test_install_script_launches_app_from_install_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script_path = root / "install.ps1"

            write_install_script(script_path)

            contents = script_path.read_text(encoding="utf-8")
            self.assertIn("Start-Process -FilePath $exePath -WorkingDirectory $installRoot", contents)

    def test_iexpress_launches_install_script_hidden(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sed_path = root / "setup.sed"

            write_sed(sed_path, root, root / "Setup.exe")

            contents = sed_path.read_text(encoding="utf-8")
            self.assertIn("AppLaunched=powershell.exe -WindowStyle Hidden", contents)


if __name__ == "__main__":
    unittest.main()
