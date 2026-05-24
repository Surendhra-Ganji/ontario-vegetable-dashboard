from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
import faiss
from openai import OpenAI

from app.services.config_service import load_vegetable_catalog
from app.services.settings import SETTINGS

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VECTOR_DIR = PROJECT_ROOT / SETTINGS["VECTOR_DB_PATH"]

INDEX_FILE = VECTOR_DIR / "index.faiss"
META_FILE = VECTOR_DIR / "metadata.json"



# =========================================================
# EMBEDDING FUNCTION
# =========================================================

def get_embedding(text: str) -> np.ndarray:
    # Embeddings are configured separately from chat completion provider.
    # This lets us keep Groq for chat while using lightweight hosted OpenAI embeddings
    # instead of heavy local sentence-transformers/PyTorch packages.
    provider = SETTINGS.get("EMBEDDING_PROVIDER", "openai")
    model = SETTINGS.get("EMBEDDING_MODEL", "text-embedding-3-small")

    if provider == "groq":
        api_key = SETTINGS.get("GROQ_API_KEY")
        base_url = SETTINGS.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        emb_client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        api_key = SETTINGS.get("OPENAI_API_KEY")
        base_url = SETTINGS.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        emb_client = OpenAI(api_key=api_key, base_url=base_url)

    # If a local/HuggingFace model name (e.g. 'sentence-transformers/...') is configured,
    # the environment likely needs sentence-transformers and PyTorch. Provide a clear error.
    if "/" in model or model.lower().startswith("sentence-transformers"):
        raise RuntimeError(
            "Configured embedding model appears to be a local/HuggingFace model ('{0}'). "
            "This requires installing 'sentence-transformers' and PyTorch and using a local embedding path, "
            "or change EMBEDDING_MODEL to a provider embedding model and ensure provider keys are set.".format(model)
        )

    try:
        response = emb_client.embeddings.create(
            model=model,
            input=text,
        )
    except Exception as exc:
        # Provide an actionable error message including provider and model
        raise RuntimeError(f"Embedding error (provider={provider}, model={model}): {exc}")

    embedding = response.data[0].embedding

    return np.array(embedding, dtype="float32")


# =========================================================
# BUILD VECTOR INDEX
# =========================================================

def build_index() -> dict:
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    docs = []

    max_rows = SETTINGS["CHUNK_MAX_ROWS"]

    for item in load_vegetable_catalog():

        csv_path = PROCESSED_DIR / f"{item['id']}.csv"

        if not csv_path.exists():
            continue

        df = pd.read_csv(csv_path).sort_values("Year")

        if df.empty:
            continue

        for start in range(0, len(df), max_rows):

            chunk = df.iloc[start:start + max_rows]

            text = _chunk_to_text(item, chunk)

            docs.append({
                "dataset_id": item["id"],
                "vegetable": item.get("display_name", item["name"]),
                "year_start": int(chunk["Year"].min()),
                "year_end": int(chunk["Year"].max()),
                "text": text,
            })

    if not docs:
        raise RuntimeError("No processed CSV files were found for indexing.")

    # ==========================================
    # CREATE EMBEDDINGS
    # ==========================================

    embeddings = []

    for doc in docs:
        emb = get_embedding(doc["text"])
        embeddings.append(emb)

    embeddings = np.vstack(embeddings)

    # normalize
    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)

    index.add(embeddings)

    faiss.write_index(index, str(INDEX_FILE))

    META_FILE.write_text(
        json.dumps(docs, indent=2),
        encoding="utf-8"
    )

    return {
        "chunks_indexed": len(docs),
        "index_path": str(INDEX_FILE),
        "metadata_path": str(META_FILE)
    }


# =========================================================
# SEARCH
# =========================================================

def search(
    query: str,
    top_k: int | None = None,
    dataset_id: str | None = None
) -> dict:

    if top_k is None:
        top_k = SETTINGS["RAG_TOP_K"]

    if not INDEX_FILE.exists() or not META_FILE.exists():
        raise RuntimeError(
            "Vector index not found. "
            "Run python -m scripts.build_vector_index first."
        )

    index = faiss.read_index(str(INDEX_FILE))

    metadata = json.loads(
        META_FILE.read_text(encoding="utf-8")
    )

    query_emb = get_embedding(query).reshape(1, -1)

    if query_emb.shape[1] != index.d:
        raise RuntimeError(
            "Vector index dimension mismatch. "
            f"Index dimension is {index.d}, but current embedding model "
            f"'{SETTINGS.get('EMBEDDING_MODEL')}' returned {query_emb.shape[1]} dimensions. "
            "Rebuild the vector index with: python -m scripts.build_vector_index"
        )

    faiss.normalize_L2(query_emb)

    scores, ids = index.search(
        query_emb,
        min(top_k * 3, len(metadata))
    )

    matches = []

    for score, idx in zip(scores[0], ids[0]):

        if idx < 0 or idx >= len(metadata):
            continue

        m = metadata[idx]

        if dataset_id and m["dataset_id"] != dataset_id:
            continue

        matches.append({
            "score": float(score),
            "dataset_id": m["dataset_id"],
            "vegetable": m["vegetable"],
            "year_start": m["year_start"],
            "year_end": m["year_end"],
            "text": m["text"],
        })

        if len(matches) >= top_k:
            break

    return {"matches": matches}


# =========================================================
# CHUNK TEXT
# =========================================================

def _chunk_to_text(item: dict, chunk: pd.DataFrame) -> str:

    lines = [
        f"Vegetable dataset: {item.get('display_name', item['name'])}",
        f"Dataset id: {item['id']}",
        f"Year range: {int(chunk['Year'].min())} to {int(chunk['Year'].max())}",
        "Data rows:",
    ]

    for _, row in chunk.iterrows():

        parts = [f"Year {int(row['Year'])}"]

        for col in chunk.columns:

            if col == "Year":
                continue

            val = row[col]

            if pd.notna(val):
                parts.append(f"{col}={val}")

        lines.append("; ".join(parts))

    return "\n".join(lines)