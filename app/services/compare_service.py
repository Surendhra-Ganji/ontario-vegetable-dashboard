from __future__ import annotations

from pathlib import Path
import pandas as pd
from app.services.config_service import vegetable_lookup
from app.services.dataset_service import METRIC_LABELS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def compare_datasets(
    dataset_ids: list[str],
    metric_key: str,
    year_start: int | None = None,
    year_end: int | None = None,
) -> dict:
    catalog = vegetable_lookup()
    metric_col = METRIC_LABELS.get(metric_key, METRIC_LABELS["yield"])

    valid_rows = []
    skipped = []

    for dataset_id in dataset_ids:
        meta = catalog.get(dataset_id)
        if not meta:
            skipped.append(
                {"dataset_id": dataset_id, "reason": "Unknown vegetable id"}
            )
            continue

        csv_path = PROCESSED_DIR / f"{dataset_id}.csv"
        if not csv_path.exists():
            skipped.append(
                {"dataset_id": dataset_id, "reason": "Processed file not found"}
            )
            continue

        try:
            df = pd.read_csv(csv_path)

            if df.empty:
                skipped.append(
                    {"dataset_id": dataset_id, "reason": "Processed file is empty"}
                )
                continue

            if "Year" not in df.columns:
                skipped.append(
                    {"dataset_id": dataset_id, "reason": "Missing Year column"}
                )
                continue

            if metric_col not in df.columns:
                skipped.append(
                    {
                        "dataset_id": dataset_id,
                        "reason": f"Missing metric column: {metric_col}",
                    }
                )
                continue

            df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
            df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce")
            df = df.dropna(subset=["Year", metric_col])

            if df.empty:
                skipped.append(
                    {
                        "dataset_id": dataset_id,
                        "reason": f"No usable values for Year and {metric_col}",
                    }
                )
                continue

            df["Year"] = df["Year"].astype(int)

            if year_start is not None:
                df = df[df["Year"] >= int(year_start)]
            if year_end is not None:
                df = df[df["Year"] <= int(year_end)]

            if df.empty:
                skipped.append(
                    {
                        "dataset_id": dataset_id,
                        "reason": f"No rows in selected year range {year_start} to {year_end}",
                    }
                )
                continue

            df = df.sort_values("Year").reset_index(drop=True)

            temp = df[["Year", metric_col]].copy()
            temp["dataset_id"] = dataset_id
            temp["vegetable"] = meta.get("display_name", meta["name"])

            valid_rows.extend(temp.to_dict(orient="records"))

        except Exception as exc:
            skipped.append(
                {
                    "dataset_id": dataset_id,
                    "reason": f"Compare failed: {str(exc)}",
                }
            )

    return {
        "comparison_metric_key": metric_key,
        "comparison_metric_label": metric_col,
        "valid_rows": valid_rows,
        "skipped_datasets": skipped,
    }