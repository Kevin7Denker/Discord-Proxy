import os
import subprocess
from pathlib import Path

import sys

def prepare_release_env(root: Path, announce: bool = False) -> Path | None:
    env_source = root / ".env"
    fallback_source = root / ".env.example"
    source = env_source if env_source.is_file() else fallback_source
    if not source.is_file():
        return None

    dist_env = root / "build" / "release-env" / ".env"
    dist_env.parent.mkdir(parents=True, exist_ok=True)
    dist_env.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    if announce:
        source_label = ".env" if source == env_source else ".env.example"
        print(f"Release env prepared from {source_label}.")
        if source == fallback_source:
            print("Warning: setup will use fallback proxy settings from .env.example.")
    return dist_env


def build() -> None:
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    dist_env = prepare_release_env(root, announce=True)
    
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
