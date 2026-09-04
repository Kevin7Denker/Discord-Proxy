import subprocess
import unittest

from core.processes import hidden_subprocess_kwargs


class ProcessesTests(unittest.TestCase):
    def test_hidden_subprocess_kwargs_disable_windows_console(self):
        kwargs = hidden_subprocess_kwargs()

        self.assertEqual(subprocess.CREATE_NO_WINDOW, kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW)
        self.assertEqual(subprocess.STARTF_USESHOWWINDOW, kwargs["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW)
        self.assertEqual(0, kwargs["startupinfo"].wShowWindow)


if __name__ == "__main__":
    unittest.main()
