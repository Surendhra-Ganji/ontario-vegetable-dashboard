from __future__ import annotations

from pathlib import Path
import pandas as pd
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
dataset_names = [v["id"] for v in load_vegetable_catalog()]
print(dataset_names)
for dataset_id in dataset_names:
    
    dataset_id = "aggregated_carrot_production_and_yields"
    path = PROCESSED_DIR / f"{dataset_id}.csv"

    if not path.exists():
        raise FileNotFoundError(f"{dataset_id} not found")

    df = pd.read_csv(path)

    # 🔥 Clean column names early
    df.columns = [c.strip() for c in df.columns]


    if df.empty:
        print({"rows": [], "dataset_id": dataset_id})

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Safe column mapping
    col_map = {
        "Year": "Year",
        "Production (000 lbs)": "Production",
        "Yield (lbs/acre)": "Yield",
        "Price (cents/lb)": "Price",
        "Farm Value ($'000)": "Farm Value",
        "Area (acres)": "Area",
    }

    safe_df = df.copy()

    for col in col_map:
        if col not in safe_df.columns:
            safe_df[col] = None  # 🔥 prevent crash

    # Keep only needed columns
    safe_df = safe_df[list(col_map.keys())]

    # Rename nicely
    safe_df = safe_df.rename(columns=col_map)

    # Convert numeric safely
    for c in ["Production", "Yield", "Price", "Farm Value", "Area"]:
        safe_df[c] = pd.to_numeric(safe_df[c], errors="coerce")

    safe_df = safe_df.sort_values("Year")

    print({
            "dataset_id": dataset_id,
            "rows": safe_df.to_dict(orient="records"),
        })