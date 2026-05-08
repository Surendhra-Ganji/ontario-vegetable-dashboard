from __future__ import annotations

from pathlib import Path
import re
import requests
import pandas as pd

from app.services.config_service import load_vegetable_catalog
from app.services.ontario_ckan_service import OntarioCKANService
from app.services.settings import SETTINGS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
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

ALL_OUTPUT_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS + ["Vegetable", "Dataset"]


CANONICAL_MAP = {
    "year": "Year",
    "harvested area (acres)": "Harvested Area (acres)",
    "harvested area acres": "Harvested Area (acres)",
    "harvested area (ha)": "Harvested Area (ha)",

    "marketed production ('000 lbs)": "Marketed Production ('000 lbs)",
    "marketed production ('000 lb)": "Marketed Production ('000 lbs)",
    "marketed production (000 lbs)": "Marketed Production ('000 lbs)",
    "marketed production ('000lbs)": "Marketed Production ('000 lbs)",
    "marketed production (tonnes)": "Marketed Production (tonnes)",

    "average price (cents/lb)": "Average Price (cents/lb)",
    "average price cents/lb": "Average Price (cents/lb)",
    "average price (cents per lb)": "Average Price (cents/lb)",
    "average price ($/tonne)": "Average Price ($/tonne)",

    "average yield (lbs/acre)": "Average Yield (lbs/acre)",
    "average yield lbs/acre": "Average Yield (lbs/acre)",
    "average yield (tonnes/ha)": "Average Yield (tonnes/ha)",

    "farm value ($'000)": "Farm Value ($'000)",
    "farm value ($000)": "Farm Value ($'000)",
    "farm value ('000 $)": "Farm Value ($'000)",
    "farm value": "Farm Value ($'000)",
}


class ETLService:
    def __init__(self):
        self.ckan = OntarioCKANService()
        self.download_timeout = SETTINGS["DOWNLOAD_TIMEOUT"]

    def run(self) -> dict:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        processed = 0
        errors: list[dict] = []

        for item in load_vegetable_catalog():
            dataset_id = item["id"]
            display_name = item.get("display_name", item["name"])
            dataset_slug = item["dataset_slug"]

            try:
                package = self.ckan.package_show(dataset_slug)
                download_url = self.ckan.resolve_download_url(package)

                raw_path = RAW_DIR / f"{dataset_id}.xlsx"
                self._download_file(download_url, raw_path)

                raw_df = self._read_ontario_excel(raw_path)
                final_df = self._standardize_dataframe(
                    raw_df,
                    dataset_id=dataset_id,
                    display_name=display_name,
                )
                self._validate_processed_dataframe(final_df, dataset_id)

                out_csv = PROCESSED_DIR / f"{dataset_id}.csv"
                final_df.to_csv(out_csv, index=False)

                processed += 1

            except Exception as exc:
                errors.append(
                    {
                        "dataset_id": dataset_id,
                        "error": str(exc),
                    }
                )

        return {
            "datasets_processed": processed,
            "errors": errors,
        }

    def _download_file(self, url: str, target_path: Path) -> None:
        response = requests.get(url, timeout=self.download_timeout)
        response.raise_for_status()
        target_path.write_bytes(response.content)

    def _read_ontario_excel(self, path: Path) -> pd.DataFrame:
        raw = pd.read_excel(path, header=None, engine="openpyxl")

        header_row_idx = self._detect_header_row(raw)
        if header_row_idx is None:
            raise RuntimeError(f"Could not detect header row in {path.name}")

        headers = [self._normalize_header(x) for x in raw.iloc[header_row_idx].tolist()]

        data = raw.iloc[header_row_idx + 1 :].copy()
        data.columns = headers
        data = data.dropna(how="all")
        data = data.loc[:, ~pd.Index(data.columns).duplicated()]
        data = self._clean_dataframe(data)

        return data.reset_index(drop=True)

    def _detect_header_row(self, raw: pd.DataFrame) -> int | None:
        max_scan_rows = min(len(raw), 20)

        for idx in range(max_scan_rows):
            row_vals = [
                str(x).strip().lower()
                for x in raw.iloc[idx].tolist()
                if pd.notna(x)
            ]
            if any(v == "year" for v in row_vals):
                return idx

        return None

    def _normalize_header(self, value) -> str:
        if pd.isna(value):
            return ""

        text = str(value).replace("\n", " ").strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        blank_tokens = {"", "-", "—", "na", "n/a", "nan", "none"}

        cleaned = df.copy()

        for col in cleaned.columns:
            series = cleaned[col]
            series = series.map(lambda x: None if pd.isna(x) else x)
            series = series.map(
                lambda x: None
                if isinstance(x, str) and x.strip().lower() in blank_tokens
                else x
            )
            cleaned[col] = series

        return cleaned

    def _standardize_dataframe(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        display_name: str,
    ) -> pd.DataFrame:
        working = df.copy()

        rename_map: dict[str, str] = {}
        for col in working.columns:
            normalized_key = self._normalize_header(col).lower()
            normalized_key = re.sub(r"\s+", " ", normalized_key).strip()

            if normalized_key in CANONICAL_MAP:
                rename_map[col] = CANONICAL_MAP[normalized_key]

        working = working.rename(columns=rename_map)

        # Add missing required/optional columns so downstream schema stays stable
        for col in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
            if col not in working.columns:
                working[col] = pd.NA

        # Numeric conversion
        working["Year"] = pd.to_numeric(working["Year"], errors="coerce")

        for col in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
            if col != "Year":
                working[col] = pd.to_numeric(working[col], errors="coerce")

        # Drop rows without usable year
        working = working.dropna(subset=["Year"]).copy()
        if not working.empty:
            working["Year"] = working["Year"].astype(int)

        # Keep only canonical columns first
        ordered_present = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
        working = working[ordered_present].copy()

        # Sort by year
        if "Year" in working.columns and not working.empty:
            working = working.sort_values("Year").reset_index(drop=True)

        # Add metadata columns
        working["Vegetable"] = display_name
        working["Dataset"] = dataset_id

        # Final output order
        working = working[ALL_OUTPUT_COLUMNS].copy()

        return working

    def _validate_processed_dataframe(self, df: pd.DataFrame, dataset_id: str) -> None:
        if df.empty:
            raise ValueError(f"{dataset_id}: dataframe is empty after processing")

        missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing_required:
            raise ValueError(
                f"{dataset_id}: missing required columns: {missing_required}"
            )

        year_values = pd.to_numeric(df["Year"], errors="coerce")
        if year_values.isna().all():
            raise ValueError(f"{dataset_id}: Year column has no usable numeric values")

        # Required metric columns must have at least some usable data
        required_metric_columns = [c for c in REQUIRED_COLUMNS if c != "Year"]
        missing_usable_metrics = []

        for col in required_metric_columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            if vals.notna().sum() == 0:
                missing_usable_metrics.append(col)

        if missing_usable_metrics:
            raise ValueError(
                f"{dataset_id}: required columns have no usable numeric values: {missing_usable_metrics}"
            )