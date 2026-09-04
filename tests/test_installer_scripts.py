import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class InstallerScriptsTests(unittest.TestCase):
    def test_inno_installers_package_complete_onedir_app(self):
        for relative_path in ("scripts/installer.iss", "installer/installer.iss"):
            with self.subTest(relative_path=relative_path):
                contents = (ROOT / relative_path).read_text(encoding="utf-8")

                self.assertIn(r'Source: "..\dist\DiscordProxie\*"', contents)
                self.assertIn("recursesubdirs", contents)
                self.assertNotIn(r'Source: "..\dist\{#MyAppExeName}"', contents)

    def test_release_script_uses_current_artifact_names(self):
        contents = (ROOT / "scripts" / "release.ps1").read_text(encoding="utf-8")

        self.assertIn(r'[string]$AppExe = "dist\DiscordProxie\DiscordProxie.exe"', contents)
        self.assertIn(r'[string]$SetupExe = "dist\DiscordProxie-Setup.exe"', contents)
        self.assertIn(r'& $iscc "scripts\installer.iss"', contents)
        self.assertNotIn("DiscordProxy.exe", contents)
        self.assertNotIn("DiscordProxy-Setup.exe", contents)
        self.assertNotIn(r'& $iscc "installer\installer.iss"', contents)


if __name__ == "__main__":
    unittest.main()
