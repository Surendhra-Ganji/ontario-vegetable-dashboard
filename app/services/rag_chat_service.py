from __future__ import annotations

from app.services.vector_service import search
from app.services.llm_service import generate_answer
from app.services.analysis_service import summarize_dataset_trends, classify_question


def rag_answer(question: str, dataset_id: str | None = None) -> dict:
    question_type = classify_question(question)

    search_result = search(question, dataset_id=dataset_id)
    matches = search_result.get("matches", [])

    if not matches:
        return {
            "answer": (
                "Summary:\n"
                "I could not find relevant context in the processed vegetable data.\n\n"
                "Key Insights:\n"
                "- No matching data chunks were retrieved.\n"
                "- Try a more specific crop, year, or metric.\n"
                "- Rebuild the vector index if ETL changed recently.\n\n"
                "Likely Explanation:\n"
                "The question may be too broad, or the data for that crop may not be available in the current processed files.\n\n"
                "Confidence:\n"
                "Low - no relevant retrieved context was available.\n\n"
                "Recommendation:\n"
                "Try naming a crop and year range directly."
            ),
            "sources": [],
        }

    sources = []
    context_parts = []
    seen_dataset_ids: list[str] = []

    for m in matches:
        dataset = m["dataset_id"]
        if dataset not in seen_dataset_ids:
            seen_dataset_ids.append(dataset)

        sources.append(
            {
                "vegetable": m["vegetable"],
                "dataset_id": m["dataset_id"],
                "year_range": f"{m['year_start']}-{m['year_end']}",
                "score": round(float(m["score"]), 4),
            }
        )
        context_parts.append(m["text"])

    # Add deterministic trend summaries for every retrieved dataset
    trend_summaries = []
    for dsid in seen_dataset_ids:
        try:
            trend_summaries.append(summarize_dataset_trends(dsid))
        except Exception:
            continue

    trend_text_blocks = []
    for ts in trend_summaries:
        trend_text_blocks.append(
            f"Computed trend summary for dataset {ts['dataset_id']}: {ts}"
        )

    enriched_question = f"""
Question type: {question_type}
Original question: {question}
""".strip()

    combined_context = "\n\n".join(context_parts + trend_text_blocks)

    answer = generate_answer(
        question=enriched_question,
        retrieved_context=combined_context,
    )

    return {
        "answer": answer,
        "sources": sources,
    }