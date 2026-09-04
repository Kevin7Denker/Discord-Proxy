import unittest
from unittest.mock import MagicMock, patch

from core.startup import RUN_KEY_PATH, RUN_VALUE_NAME, get_startup_command, is_start_with_windows_enabled, set_start_with_windows


class StartupTests(unittest.TestCase):
    def test_packaged_startup_command_uses_current_executable(self):
        command = get_startup_command(executable=r"C:\Local Apps\DiscordProxie.exe", frozen=True)

        self.assertEqual(r'"C:\Local Apps\DiscordProxie.exe" --startup', command)

    def test_dev_startup_command_uses_script_path(self):
        command = get_startup_command(
            executable=r"C:\Python Path\pythonw.exe",
            argv=[r"C:\Repo Path\main.py"],
            frozen=False,
        )

        self.assertEqual(r'"C:\Python Path\pythonw.exe" "C:\Repo Path\main.py" --startup', command)

    @patch("core.startup.os.name", "nt")
    def test_set_start_with_windows_writes_current_user_run_value(self):
        registry = MagicMock()
        key = object()
        registry.HKEY_CURRENT_USER = object()
        registry.KEY_SET_VALUE = 2
        registry.REG_SZ = 1
        registry.CreateKeyEx.return_value.__enter__.return_value = key

        result = set_start_with_windows(True, command="app.exe --startup", registry=registry)

        self.assertTrue(result)
        registry.CreateKeyEx.assert_called_once_with(registry.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, registry.KEY_SET_VALUE)
        registry.SetValueEx.assert_called_once_with(key, RUN_VALUE_NAME, 0, registry.REG_SZ, "app.exe --startup")

    @patch("core.startup.os.name", "nt")
    def test_set_start_with_windows_removes_current_user_run_value(self):
        registry = MagicMock()
        key = object()
        registry.HKEY_CURRENT_USER = object()
        registry.KEY_SET_VALUE = 2
        registry.OpenKey.return_value.__enter__.return_value = key

        result = set_start_with_windows(False, registry=registry)

        self.assertTrue(result)
        registry.OpenKey.assert_called_once_with(registry.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, registry.KEY_SET_VALUE)
        registry.DeleteValue.assert_called_once_with(key, RUN_VALUE_NAME)

    @patch("core.startup.os.name", "nt")
    def test_is_start_with_windows_enabled_matches_saved_command(self):
        registry = MagicMock()
        key = object()
        registry.HKEY_CURRENT_USER = object()
        registry.KEY_READ = 1
        registry.OpenKey.return_value.__enter__.return_value = key
        registry.QueryValueEx.return_value = ("expected", registry.REG_SZ)

        self.assertTrue(is_start_with_windows_enabled(command="expected", registry=registry))
        self.assertFalse(is_start_with_windows_enabled(command="other", registry=registry))


if __name__ == "__main__":
    unittest.main()
