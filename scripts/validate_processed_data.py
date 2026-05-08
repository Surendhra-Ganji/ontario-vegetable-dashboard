from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

REQUIRED_COLUMNS = [
    "Year",
    "Harvested Area (acres)",
    "Marketed Production ('000 lbs)",
    "Average Price (cents/lb)",
    "Average Yield (lbs/acre)",
]

OPTIONAL_COLUMNS = [
    "Farm Value ($'000)",
]


def validate_file(path: Path) -> list[str]:
    issues: list[str] = []
    df = pd.read_csv(path)

    if df.empty:
        issues.append("file is empty")
        return issues

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        issues.append(f"missing required columns: {missing_required}")

    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in df.columns]
    if missing_optional:
        issues.append(f"missing optional columns: {missing_optional}")

    if "Year" in df.columns:
        year = pd.to_numeric(df["Year"], errors="coerce")
        if year.isna().all():
            issues.append("Year column has no usable numeric values")
    else:
        issues.append("Year column missing")

    for col in REQUIRED_COLUMNS:
        if col == "Year":
            continue
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            if vals.notna().sum() == 0:
                issues.append(f"{col} has no usable numeric values")

    return issues


def main() -> None:
    if not PROCESSED_DIR.exists():
        print("No processed directory found")
        return

    files = sorted(PROCESSED_DIR.glob("*.csv"))
    if not files:
        print("No processed CSV files found")
        return

    failed = 0
    warned = 0

    for file in files:
        issues = validate_file(file)

        required_errors = [x for x in issues if "missing required" in x or "no usable" in x or "file is empty" in x]
        optional_warnings = [x for x in issues if "missing optional" in x]

        if required_errors:
            failed += 1
            print(f"\nFAIL: {file.name}")
            for issue in issues:
                print(" -", issue)
        elif optional_warnings:
            warned += 1
            print(f"\nWARN: {file.name}")
            for issue in issues:
                print(" -", issue)
        else:
            print(f"PASS: {file.name}")

    print(f"\nValidation complete. Failed files: {failed} / {len(files)}, Warnings: {warned}")
    

if __name__ == "__main__":
    main()