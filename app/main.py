from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from app.services.dataset_service import list_vegetables, get_vegetable, get_kpis
from app.services.compare_service import compare_datasets
from app.services.rag_chat_service import rag_answer
from app.services.vector_service import get_embedding
from app.services.settings import SETTINGS
from app.services.settings import CONFIG_FILE_PATH, reload_settings
import json

app = FastAPI(title="Ontario Vegetable Dashboard API")


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    question: str
    dataset_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/login")
def login(payload: LoginRequest):
    # simple placeholder login
    if payload.username == "admin" and payload.password == "ChangeMe123!":
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.get("/vegetables")
def vegetables():
    return {"vegetables": list_vegetables()}


@app.get("/vegetables/kpis")
def vegetable_kpis():
    return {"kpis": get_kpis()}


@app.get("/vegetables/compare")
def vegetable_compare(
    dataset_ids: str = Query(...),
    metric: str = Query("yield"),
    year_start: int | None = Query(None),
    year_end: int | None = Query(None),
):
    try:
        ids = [x.strip() for x in dataset_ids.split(",") if x.strip()]
        return compare_datasets(ids, metric, year_start, year_end)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"vegetable_compare failed: {str(exc)}")


@app.get("/vegetables/{dataset_id}")
def vegetable_detail(dataset_id: str):
    print(f"Fetching details for dataset_id in main: {dataset_id}")
    try:
        return get_vegetable(dataset_id)
    except Exception as exc:
        import traceback
        traceback.print_exc()   # 👈 prints full error in terminal
        raise HTTPException(
            status_code=500, detail=f"vegetable_detail failed for {dataset_id}: {str(exc)}"
        )


@app.get("/ai/status")
def ai_status():
    return {
        "enabled": True,
        "mode": "rag",
    }


@app.post("/chat/rag")
def chat_rag(payload: ChatRequest):
    try:
        return rag_answer(payload.question, payload.dataset_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"rag_chat failed: {str(exc)}")


@app.get("/debug/llm")
def debug_llm(force: bool = False):
    """Run a low-cost embedding to verify LLM connectivity.

    This endpoint is intended for local/debug use. It is blocked in production
    unless `force=true` is provided.
    """
    if SETTINGS.get("APP_ENV") == "production" and not force:
        raise HTTPException(status_code=403, detail="Not allowed in production")

    try:
        emb = get_embedding("debug ping")
        return {
            "ok": True,
            "llm_provider": SETTINGS.get("LLM_PROVIDER"),
            "embedding_provider": SETTINGS.get("EMBEDDING_PROVIDER"),
            "embedding_model": SETTINGS.get("EMBEDDING_MODEL"),
            "openai_base_url": SETTINGS.get("OPENAI_BASE_URL"),
            "embedding_length": len(emb) if emb is not None else 0,
        }
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"llm debug failed: {exc}")


@app.get("/admin/config")
def admin_get_config(x_admin_password: str | None = Header(None)):
    # simple header-based protection
    if x_admin_password != SETTINGS.get("ADMIN_PASSWORD"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not CONFIG_FILE_PATH.exists():
        return {"config": {}}

    try:
        cfg = json.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
        return {"config": cfg}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"could not read config: {exc}")


@app.post("/admin/config")
def admin_post_config(payload: dict, x_admin_password: str | None = Header(None)):
    if x_admin_password != SETTINGS.get("ADMIN_PASSWORD"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        # reload settings into memory
        reload_settings()
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"could not write config: {exc}")