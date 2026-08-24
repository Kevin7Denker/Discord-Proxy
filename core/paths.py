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
