import tempfile
import unittest
from pathlib import Path

from scripts.build import REQUIRED_RUNTIME_FILES, validate_onedir_app


class BuildValidationTests(unittest.TestCase):
    def test_validate_onedir_app_requires_pythonnet_runtime(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            for relative_path in REQUIRED_RUNTIME_FILES:
                target = app_dir / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("", encoding="utf-8")

            (app_dir / "_internal" / "pythonnet" / "runtime" / "Python.Runtime.dll").unlink()

            with self.assertRaises(FileNotFoundError) as error:
                validate_onedir_app(app_dir)

            self.assertIn("Python.Runtime.dll", str(error.exception))


if __name__ == "__main__":
    unittest.main()
