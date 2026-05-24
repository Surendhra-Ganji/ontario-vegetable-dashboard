import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Admin — App Config", layout="wide")

st.title("Admin — Configuration (hidden)")

pwd = st.text_input("Admin password", type="password")

if not pwd:
    st.info("Enter admin password to view and edit configuration")
    st.stop()

headers = {"X-ADMIN-PASSWORD": pwd}

# Fetch current config
try:
    resp = requests.get(f"{API_BASE_URL}/admin/config", headers=headers, timeout=30)
    if resp.status_code == 401:
        st.error("Unauthorized: incorrect password")
        st.stop()
    resp.raise_for_status()
    cfg = resp.json().get("config", {})
except Exception as exc:
    st.error(f"Could not fetch config: {exc}")
    st.stop()

st.subheader("Editable settings")

llm_provider = st.selectbox("LLM Provider", ["groq", "openai", "openai_compatible"], index=["groq", "openai", "openai_compatible"].index(cfg.get("LLM_PROVIDER", "groq")))
embedding_provider = st.selectbox("Embedding Provider", ["openai", "openai_compatible", "groq"], index=["openai", "openai_compatible", "groq"].index(cfg.get("EMBEDDING_PROVIDER", "openai")))
embedding_model = st.text_input("Embedding model", value=cfg.get("EMBEDDING_MODEL", "text-embedding-3-small"))
rag_top_k = st.number_input("RAG top K", min_value=1, max_value=20, value=int(cfg.get("RAG_TOP_K", 6)))
chunk_max = st.number_input("Chunk max rows", min_value=1, max_value=100, value=int(cfg.get("CHUNK_MAX_ROWS", 8)))

groq_base = st.text_input("GROQ base URL", value=cfg.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
vector_path = st.text_input("Vector DB path", value=cfg.get("VECTOR_DB_PATH", "data/vector_store"))

if st.button("Save configuration"):
    new_cfg = cfg.copy()
    new_cfg.update({
        "LLM_PROVIDER": llm_provider,
        "EMBEDDING_PROVIDER": embedding_provider,
        "EMBEDDING_MODEL": embedding_model,
        "RAG_TOP_K": rag_top_k,
        "CHUNK_MAX_ROWS": chunk_max,
        "GROQ_BASE_URL": groq_base,
        "VECTOR_DB_PATH": vector_path,
    })

    try:
        r = requests.post(f"{API_BASE_URL}/admin/config", json=new_cfg, headers=headers, timeout=30)
        if r.status_code == 401:
            st.error("Unauthorized: incorrect password")
        else:
            r.raise_for_status()
            st.success("Configuration saved. Backend reloaded settings.")
    except Exception as exc:
        st.error(f"Could not save config: {exc}")
