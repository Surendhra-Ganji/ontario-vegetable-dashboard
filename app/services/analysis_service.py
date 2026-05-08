from __future__ import annotations

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TREND_METRICS = [
    "Harvested Area (acres)",
    "Marketed Production ('000 lbs)",
    "Average Price (cents/lb)",
    "Average Yield (lbs/acre)",
    "Farm Value ($'000)",
]


def summarize_dataset_trends(dataset_id: str) -> dict:
    csv_path = PROCESSED_DIR / f"{dataset_id}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Processed file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    if df.empty:
        raise ValueError(f"Processed file is empty for dataset: {dataset_id}")

    if "Year" not in df.columns:
        raise ValueError(f"Year column missing for dataset: {dataset_id}")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"]).copy()

    if df.empty:
        raise ValueError(f"No usable Year values for dataset: {dataset_id}")

    df["Year"] = df["Year"].astype(int)

    for metric in TREND_METRICS:
        if metric in df.columns:
            df[metric] = pd.to_numeric(df[metric], errors="coerce")

    df = df.sort_values("Year").reset_index(drop=True)

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest

    metric_summary: dict[str, dict] = {}

    for metric in TREND_METRICS:
        if metric not in df.columns:
            continue

        latest_val = latest.get(metric)
        previous_val = previous.get(metric)

        if pd.isna(latest_val):
            continue

        latest_val = float(latest_val)
        previous_val = None if pd.isna(previous_val) else float(previous_val)

        pct_change = None
        if previous_val is not None and previous_val != 0:
            pct_change = round(((latest_val - previous_val) / previous_val) * 100, 2)

        metric_summary[metric] = {
            "latest": latest_val,
            "previous": previous_val,
            "pct_change_vs_previous_year": pct_change,
        }

    biggest_move_metric = None
    biggest_move_value = None

    for metric, payload in metric_summary.items():
        pct = payload.get("pct_change_vs_previous_year")
        if pct is None:
            continue
        if biggest_move_value is None or abs(pct) > abs(biggest_move_value):
            biggest_move_metric = metric
            biggest_move_value = pct

    return {
        "dataset_id": dataset_id,
        "year_min": int(df["Year"].min()),
        "year_max": int(df["Year"].max()),
        "row_count": int(len(df)),
        "latest_year": int(df["Year"].max()),
        "metrics": metric_summary,
        "largest_year_over_year_move": {
            "metric": biggest_move_metric,
            "pct_change": biggest_move_value,
        },
    }


def summarize_multiple_datasets(dataset_ids: list[str]) -> list[dict]:
    summaries: list[dict] = []

    for dataset_id in dataset_ids:
        try:
            summaries.append(summarize_dataset_trends(dataset_id))
        except Exception:
            continue

    return summaries


def classify_question(question: str) -> str:
    q = (question or "").lower()

    if "why" in q:
        return "explain"
    if "compare" in q:
        return "compare"
    if "summary" in q or "summarize" in q:
        return "summary"
    if "trend" in q or "changed" in q or "change" in q:
        return "trend"
    if "highest" in q or "lowest" in q or "top" in q:
        return "ranking"
    return "general"