from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

def get_setting(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

def get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

SETTINGS = {
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
    "GROQ_BASE_URL": get_setting("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
    "OPENAI_API_KEY": get_setting("OPENAI_API_KEY"),
    "OPENAI_MODEL": get_setting("OPENAI_MODEL", "gpt-4.1-mini"),
    "OPENAI_BASE_URL": get_setting("OPENAI_BASE_URL"),
    "EMBEDDING_MODEL": get_setting("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
    "VECTOR_DB_PATH": get_setting("VECTOR_DB_PATH", "data/vector_store"),
    "RAG_TOP_K": get_int("RAG_TOP_K", 6),
    "CHUNK_MAX_ROWS": get_int("CHUNK_MAX_ROWS", 8),
    "ENABLE_AI_ASSISTANT": get_setting("ENABLE_AI_ASSISTANT", "true"),
    "ONTARIO_CKAN_BASE_URL": get_setting("ONTARIO_CKAN_BASE_URL", "https://data.ontario.ca/api/3/action"),
    "CKAN_TIMEOUT": get_int("CKAN_TIMEOUT", 60),
    "DOWNLOAD_TIMEOUT": get_int("DOWNLOAD_TIMEOUT", 180),
}
