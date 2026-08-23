from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    command = [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole", "--clean", "--name", "DiscordProxie"]
    if (root / "assets" / "icon.ico").is_file():
        command.append("--icon=assets/icon.ico")
    command.extend(["--add-data", "assets;assets", "--add-data", "core;core", "--add-data", "ui;ui", "main.py"])
    return subprocess.run(command, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
