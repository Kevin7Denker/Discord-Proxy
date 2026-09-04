import os
import sys
from pathlib import Path

def get_base_path() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))

def get_assets_path() -> Path:
    return get_base_path() / "assets"

def get_frontend_path() -> Path:
    return get_base_path() / "frontend"

def get_env_path() -> Path:
    return get_base_path() / ".env"

def get_locales_path() -> Path:
    return get_frontend_path() / "locales"

def get_user_log_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Discord Proxie" / "logs" / "connections.jsonl"
    return get_base_path() / "logs" / "connections.jsonl"
