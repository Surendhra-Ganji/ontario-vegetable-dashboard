from __future__ import annotations
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "vegetables.json"

def load_vegetable_catalog():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def vegetable_lookup():
    return {item["id"]: item for item in load_vegetable_catalog()}
