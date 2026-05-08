from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.dataset_service import get_vegetable

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DATASET_ID = "aggregated_onion_production_and_yields"


def main() -> None:
    csv_path = PROCESSED_DIR / f"{DATASET_ID}.csv"
    print(f"Checking: {csv_path}")

    if not csv_path.exists():
        print("ERROR: processed CSV does not exist")
        return

    df = pd.read_csv(csv_path)
    print("\nColumns:")
    print(df.columns.tolist())

    print("\nShape:")
    print(df.shape)

    print("\nHead:")
    print(df.head(10).to_string())

    if "Year" in df.columns:
        years = pd.to_numeric(df["Year"], errors="coerce")
        print("\nYear stats:")
        print("min:", years.min())
        print("max:", years.max())
        print("null years:", years.isna().sum())
    else:
        print("\nERROR: Year column missing")

    for col in [
        "Harvested Area (acres)",
        "Marketed Production ('000 lbs)",
        "Farm Value ($'000)",
        "Average Price (cents/lb)",
        "Average Yield (lbs/acre)",
    ]:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            print(f"\nColumn check: {col}")
            print("nulls:", vals.isna().sum(), "non_nulls:", vals.notna().sum())
        else:
            print(f"\nMISSING COLUMN: {col}")

    print("\nTrying backend get_vegetable()...\n")
    try:
        result = get_vegetable(DATASET_ID)
        print("SUCCESS")
        print("min_year:", result.get("min_year"))
        print("max_year:", result.get("max_year"))
        print("row_count:", len(result.get("rows", [])))
    except Exception as exc:
        print("BACKEND FAILURE:")
        print(repr(exc))


if __name__ == "__main__":
    main()