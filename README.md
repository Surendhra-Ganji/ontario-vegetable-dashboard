# Ontario Vegetable Dashboard — v4.0 RAG Enhanced

This version enhances the earlier dashboard with a real RAG workflow over the **processed folder**.

## What’s new

- live Ontario Open Data ETL remains supported
- processed CSV files in `data/processed` are converted into text chunks
- embeddings are created with `sentence-transformers`
- vector search is stored in **FAISS**
- chat answers are generated with:
  - **Groq**
  - **OpenAI**
  - **any OpenAI-compatible endpoint**

## Flow

1. Run ETL to populate `data/processed`
2. Build the vector index
3. Start FastAPI
4. Start Streamlit
5. Ask questions in the AI Assistant tab

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
copy .env.example .env
python -m scripts.run_etl
python -m scripts.build_vector_index
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
.\.venv\Scripts\activate
streamlit run app/frontend/streamlit_app.py
```

## Example questions

- Why was radish production low in 2020?
- Why were pepper prices high in 2024?
- Summarize tomato trends in the last 10 years
- Compare cucumber and lettuce
- What changed in pumpkin yield versus the previous year?

## Environment variables

Use `.env` for local development. For production, inject the same values as real environment variables.

### Provider options

- `LLM_PROVIDER=groq`
- `LLM_PROVIDER=openai`
- `LLM_PROVIDER=openai_compatible`

### Required values

For Groq:
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `GROQ_BASE_URL`

For OpenAI:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

For OpenAI-compatible:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`

## Important note

The RAG system answers based on retrieved processed data. It can explain likely reasons from the data patterns, but it does **not** prove external causes like weather, policy, or supply-chain events unless that evidence exists in the indexed context.
