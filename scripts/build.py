import os
import shutil
import subprocess
from pathlib import Path

import sys

def build() -> None:
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--icon=assets/branding/icon.ico",
        "--name=DiscordProxie",
        "--add-data=frontend;frontend/",
        "--add-data=assets;assets/",
        "--add-data=tun2socks.exe;.",
        "main.py"
    ]
    
    subprocess.run(command, check=True)
    print("Build complete!")

if __name__ == "__main__":
    build()
