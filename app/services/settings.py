from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

# The OpenAI SDK reads OPENAI_BASE_URL directly from environment variables.
# An empty OPENAI_BASE_URL= line in .env makes the SDK build malformed URLs.
if os.getenv("OPENAI_BASE_URL", "").strip() == "":
    os.environ.pop("OPENAI_BASE_URL", None)

# Optional JSON config file to store non-sensitive configuration values
CONFIG_FILE_PATH = PROJECT_ROOT / "config" / "app_config.json"
_CONFIG_FILE: dict | None = None
if CONFIG_FILE_PATH.exists():
    try:
        _CONFIG_FILE = json.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        _CONFIG_FILE = None


def reload_config_file() -> None:
    """Reload the JSON config file into memory."""
    global _CONFIG_FILE
    if CONFIG_FILE_PATH.exists():
        try:
            _CONFIG_FILE = json.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            _CONFIG_FILE = None
    else:
        _CONFIG_FILE = None

def get_setting(name: str, default: str | None = None) -> str | None:
    # Preference order: config file -> environment variable -> default
    if _CONFIG_FILE and name in _CONFIG_FILE:
        value = _CONFIG_FILE.get(name)
        if isinstance(value, str) and not value.strip():
            return default
        return value
    value = os.getenv(name, default)
    if isinstance(value, str) and not value.strip():
        return default
    return value

def get_int(name: str, default: int) -> int:
    try:
        value = get_setting(name, str(default))
        return int(value) if value is not None else default
    except Exception:
        return default

def get_float(name: str, default: float) -> float:
    try:
        value = get_setting(name, str(default))
        return float(value) if value is not None else default
    except Exception:
        return default


def get_base_url(name: str, default: str) -> str:
    value = get_setting(name, default)
    if not value or not str(value).strip():
        return default
    value = str(value).strip()
    if not value.startswith(("http://", "https://")):
        return default
    return value

def build_settings() -> dict:
    return {
        "APP_ENV": get_setting("APP_ENV", "local"),
        "APP_NAME": get_setting("APP_NAME", "Ontario Vegetable Dashboard"),
        "API_BASE_URL": get_setting("API_BASE_URL", "http://127.0.0.1:8000"),
        "ADMIN_USERNAME": get_setting("ADMIN_USERNAME", "admin"),
        "ADMIN_PASSWORD": get_setting("ADMIN_PASSWORD", "ChangeMe123!"),
        "LLM_PROVIDER": get_setting("LLM_PROVIDER", "groq"),
        "TEMPERATURE": get_float("TEMPERATURE", 0.2),
        "MAX_TOKENS": get_int("MAX_TOKENS", 700),
        "GROQ_API_KEY": get_setting("GROQ_API_KEY"),
        "GROQ_MODEL": get_setting("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "GROQ_BASE_URL": get_base_url("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        "OPENAI_API_KEY": get_setting("OPENAI_API_KEY"),
        "OPENAI_MODEL": get_setting("OPENAI_MODEL", "gpt-4.1-mini"),
        "OPENAI_BASE_URL": get_base_url("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "EMBEDDING_PROVIDER": get_setting("EMBEDDING_PROVIDER", "openai"),
        "EMBEDDING_MODEL": get_setting("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "VECTOR_DB_PATH": get_setting("VECTOR_DB_PATH", "data/vector_store"),
        "RAG_TOP_K": get_int("RAG_TOP_K", 6),
        "CHUNK_MAX_ROWS": get_int("CHUNK_MAX_ROWS", 8),
        "ENABLE_AI_ASSISTANT": get_setting("ENABLE_AI_ASSISTANT", "true"),
        "ONTARIO_CKAN_BASE_URL": get_setting("ONTARIO_CKAN_BASE_URL", "https://data.ontario.ca/api/3/action"),
        "CKAN_TIMEOUT": get_int("CKAN_TIMEOUT", 60),
        "DOWNLOAD_TIMEOUT": get_int("DOWNLOAD_TIMEOUT", 180),
    }


SETTINGS = build_settings()


def reload_settings() -> None:
    """Reload settings from environment and config file into the global SETTINGS."""
    reload_config_file()
    global SETTINGS
    SETTINGS = build_settings()
