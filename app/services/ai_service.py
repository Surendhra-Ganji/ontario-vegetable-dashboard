from __future__ import annotations
from app.services.settings import SETTINGS

def ai_status() -> dict:
    provider = SETTINGS["LLM_PROVIDER"]
    if provider == "groq":
        configured = bool(SETTINGS["GROQ_API_KEY"])
        model = SETTINGS["GROQ_MODEL"]
    else:
        configured = bool(SETTINGS["OPENAI_API_KEY"])
        model = SETTINGS["OPENAI_MODEL"]
    return {
        "provider": provider,
        "model": model,
        "configured": configured,
        "enabled": SETTINGS["ENABLE_AI_ASSISTANT"],
        "mode": "rag_llm"
    }
