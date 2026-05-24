from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

REQUIRED_COLUMNS = [
    "Year",
    "Production (000 lbs)",
    "Yield (lbs/acre)",
    "Price (cents/lb)",
    # Farm Value optional
    # Area optional
]

OPTIONAL_COLUMNS = [
    "Farm Value ($'000)",
    "Area (acres)",
]


def check_dataset(file_path: Path):
    result = {
        "dataset": file_path.name,
        "status": "OK",
        "missing": []}