from __future__ import annotations

from openai import OpenAI
from app.services.settings import SETTINGS


def generate_answer(question: str, retrieved_context: str) -> str:
    provider = SETTINGS["LLM_PROVIDER"]

    if provider == "groq":
        if not SETTINGS.get("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY is not configured.")
        client = OpenAI(
            api_key=SETTINGS["GROQ_API_KEY"],
            base_url=SETTINGS.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        )
        model = SETTINGS.get("GROQ_MODEL", "llama3-70b-8192")

    elif provider in ("openai", "openai_compatible"):
        if not SETTINGS.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        kwargs = {
            "api_key": SETTINGS["OPENAI_API_KEY"],
            "base_url": SETTINGS.get("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        }

        client = OpenAI(**kwargs)
        model = SETTINGS.get("OPENAI_MODEL", "gpt-4o-mini")

    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")

    system_prompt = """
You are an Ontario vegetable data analyst.

You must follow these rules:
1. Use only the retrieved context and computed trend summaries.
2. Do not invent facts.
3. If the data does not prove a cause, say that clearly.
4. Keep the wording simple, direct, and business-friendly.
5. Explain changes using the dataset's own numbers and trends.

Always respond exactly in this structure:

Summary:
<one short direct answer>

Key Insights:
- <bullet 1>
- <bullet 2>
- <bullet 3>

Likely Explanation:
<one short paragraph based only on the data patterns>

Confidence:
<High / Medium / Low - with one short reason>

Recommendation:
<one short practical next step for the user>
""".strip()

    user_prompt = f"""
Question:
{question}

Retrieved context:
{retrieved_context}
""".strip()

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=float(SETTINGS.get("TEMPERATURE", 0.2)),
            max_tokens=int(SETTINGS.get("MAX_TOKENS", 800)),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.choices[0].message.content or ""
    except Exception as exc:
        # Provide a clearer error for the API layer and log full exception
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Connection error: {exc}")