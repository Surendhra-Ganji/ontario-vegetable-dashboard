from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.services.dataset_service import list_vegetables, get_vegetable, get_kpis
from app.services.compare_service import compare_datasets
from app.services.rag_chat_service import rag_answer

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