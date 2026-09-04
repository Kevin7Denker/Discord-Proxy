from __future__ import annotations

import os
import subprocess
import sys


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "DiscordProxie"


def get_startup_command(executable: str | None = None, argv: list[str] | None = None, frozen: bool | None = None) -> str:
    current_executable = executable or sys.executable
    current_argv = argv if argv is not None else sys.argv
    is_frozen = bool(getattr(sys, "frozen", False) if frozen is None else frozen)

    if is_frozen:
        args = [current_executable, "--startup"]
    else:
        script_path = current_argv[0] if current_argv else "main.py"
        args = [current_executable, os.path.abspath(script_path), "--startup"]

    return subprocess.list2cmdline(args)


def set_start_with_windows(enabled: bool, command: str | None = None, registry=None) -> bool:
    if os.name != "nt":
        return False

    winreg = registry or __import__("winreg")
    if enabled:
        startup_command = command or get_startup_command()
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, startup_command)
        return True

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, RUN_VALUE_NAME)
    except FileNotFoundError:
        pass
    return True


def is_start_with_windows_enabled(command: str | None = None, registry=None) -> bool:
    if os.name != "nt":
        return False

    winreg = registry or __import__("winreg")
    expected_command = command or get_startup_command()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            current_command, _ = winreg.QueryValueEx(key, RUN_VALUE_NAME)
    except FileNotFoundError:
        return False

    return str(current_command) == expected_command
