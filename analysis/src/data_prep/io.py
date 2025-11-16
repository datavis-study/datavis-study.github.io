from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_INPUT_PATH: Path = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "db.json"
)


def load_study_json(path: Path | str = DEFAULT_INPUT_PATH) -> Dict[str, Any]:
    """Load the study JSON into a Python dictionary."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_completed_participants(path: Path | str = DEFAULT_INPUT_PATH):
    """Return only participant records with completed == True."""
    data = load_study_json(path)
    if not isinstance(data, list):
        return []
    return [rec for rec in data if isinstance(rec, dict) and rec.get("completed") is True]



