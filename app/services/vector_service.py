from __future__ import annotations
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from app.services.config_service import load_vegetable_catalog
from app.services.settings import SETTINGS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VECTOR_DIR = PROJECT_ROOT / SETTINGS["VECTOR_DB_PATH"]

INDEX_FILE = VECTOR_DIR / "index.faiss"
META_FILE = VECTOR_DIR / "metadata.json"

def build_index() -> dict:
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(SETTINGS["EMBEDDING_MODEL"])

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
            chunk = df.iloc[start:start+max_rows]
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

    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_FILE))
    META_FILE.write_text(json.dumps(docs, indent=2), encoding="utf-8")

    return {"chunks_indexed": len(docs), "index_path": str(INDEX_FILE), "metadata_path": str(META_FILE)}

def search(query: str, top_k: int | None = None, dataset_id: str | None = None) -> dict:
    if top_k is None:
        top_k = SETTINGS["RAG_TOP_K"]
    if not INDEX_FILE.exists() or not META_FILE.exists():
        raise RuntimeError("Vector index not found. Run python -m scripts.build_vector_index first.")

    model = SentenceTransformer(SETTINGS["EMBEDDING_MODEL"])
    index = faiss.read_index(str(INDEX_FILE))
    metadata = json.loads(META_FILE.read_text(encoding="utf-8"))

    query_emb = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    scores, ids = index.search(query_emb, min(top_k * 3, len(metadata)))

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
