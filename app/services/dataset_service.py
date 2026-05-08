from __future__ import annotations

from pathlib import Path
import pandas as pd
import math
from app.services.config_service import load_vegetable_catalog, vegetable_lookup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

METRIC_LABELS = {
    "production": "Marketed Production ('000 lbs)",
    "price": "Average Price (cents/lb)",
    "yield": "Average Yield (lbs/acre)",
    "farm_value": "Farm Value ($'000)",
    "area": "Harvested Area (acres)",
}

MIN_REQUIRED_COLUMNS = [
    "Year",
]

PREFERRED_DATA_COLUMNS = [
    "Harvested Area (acres)",
    "Marketed Production ('000 lbs)",
    "Average Price (cents/lb)",
    "Average Yield (lbs/acre)",
    "Farm Value ($'000)",
]


def list_vegetables() -> list[dict]:
    return load_vegetable_catalog()


def load_dataset(dataset_id: str) -> pd.DataFrame:
    path = PROCESSED_DIR / f"{dataset_id}.csv"

    if not path.exists():
        raise FileNotFoundError(f"{dataset_id} not found")

    df = pd.read_csv(path)

    # Clean column names early
    df.columns = [c.strip() for c in df.columns]

    return df


def safe_float(x):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return None
        return float(x)
    except:
        return None


def get_vegetable(dataset_id: str):
    # Validate dataset id exists in the catalog
    lookup = vegetable_lookup()
    if dataset_id not in lookup:
        raise KeyError(f"{dataset_id} not found in catalog")

    path = PROCESSED_DIR / f"{dataset_id}.csv"

    if not path.exists():
        raise FileNotFoundError(f"{dataset_id} not found")

    df = pd.read_csv(path)

    # Keep original metric labels (trim only)
    df.columns = df.columns.str.strip()

    # Ensure Year exists
    if "Year" not in df.columns:
        raise ValueError("Year column missing")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])

    # Convert all numeric safely
    for col in df.columns:
        if col != "Year":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("Year")
    rows = df.to_dict(orient="records")

    clean_rows = []
    for r in rows:
        clean_row = {}
        for k, v in r.items():
            if k == "Year":
                clean_row[k] = int(v) if v is not None else None
            else:
                clean_row[k] = safe_float(v)
        clean_rows.append(clean_row)

    # Provide metadata the frontend expects: metric mapping and year bounds
    min_year = int(df["Year"].min()) if not df["Year"].isna().all() else None
    max_year = int(df["Year"].max()) if not df["Year"].isna().all() else None

    meta = lookup[dataset_id].copy()
    meta.setdefault("id", dataset_id)

    return {
        "meta": meta,
        "dataset_id": dataset_id,
        "rows": clean_rows,
        "columns": [c for c in df.columns],
        "metrics": METRIC_LABELS,
        "min_year": min_year,
        "max_year": max_year,
    }


def get_kpis() -> list[dict]:
    rows: list[dict] = []

    for item in load_vegetable_catalog():
        csv_path = PROCESSED_DIR / f"{item['id']}.csv"
        if not csv_path.exists():
            continue

        try:
            df = pd.read_csv(csv_path)

            if df.empty or "Year" not in df.columns:
                continue

            df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
            df = df.dropna(subset=["Year"]).copy()
            if df.empty:
                continue

            df["Year"] = df["Year"].astype(int)

            for col in PREFERRED_DATA_COLUMNS:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.sort_values("Year").reset_index(drop=True)
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            rows.append(
                {
                    "dataset_id": item["id"],
                    "vegetable": item.get("display_name", item["name"]),
                    "year": int(latest["Year"]),
                    "production": _safe_float(latest.get("Marketed Production ('000 lbs)")),
                    "price": _safe_float(latest.get("Average Price (cents/lb)")),
                    "yield": _safe_float(latest.get("Average Yield (lbs/acre)")),
                    "farm_value": _safe_float(latest.get("Farm Value ($'000)")),
                    "area": _safe_float(latest.get("Harvested Area (acres)")),
                    "production_delta_pct": _pct_change(
                        prev.get("Marketed Production ('000 lbs)"),
                        latest.get("Marketed Production ('000 lbs)"),
                    ),
                    "price_delta_pct": _pct_change(
                        prev.get("Average Price (cents/lb)"),
                        latest.get("Average Price (cents/lb)"),
                    ),
                    "yield_delta_pct": _pct_change(
                        prev.get("Average Yield (lbs/acre)"),
                        latest.get("Average Yield (lbs/acre)"),
                    ),
                }
            )
        except Exception:
            continue

    return rows


def _safe_float(value) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _pct_change(prev, curr) -> float:
    try:
        prev = _safe_float(prev)
        curr = _safe_float(curr)
        if prev == 0:
            return 0.0
        return round(((curr - prev) / prev) * 100, 2)
    except Exception:
        return 0.0
