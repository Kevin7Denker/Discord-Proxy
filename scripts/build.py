import os
import subprocess
from pathlib import Path

import sys

def build() -> None:
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    env_example = root / ".env.example"
    dist_env = root / "build" / "release-env" / ".env"
    if env_example.is_file():
        dist_env.parent.mkdir(parents=True, exist_ok=True)
        dist_env.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
    
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--icon=assets/icon.ico",
        "--name=DiscordProxie",
        "--add-data=frontend;frontend/",
        "--add-data=assets;assets/",
        "main.py"
    ]

    if dist_env.is_file():
        command.insert(-1, f"--add-data={dist_env};.")
    if (root / "tun2socks.exe").is_file():
        command.insert(-1, "--add-data=tun2socks.exe;.")
    
    subprocess.run(command, check=True)
    print("Build complete!")

if __name__ == "__main__":
    build()
