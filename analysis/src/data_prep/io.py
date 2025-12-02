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


def _is_not_rejected(rec: Dict[str, Any]) -> bool:
    """Return True if the record should NOT be considered rejected.

    In the raw `db.json`, the `rejected` field can be:
    - `false` (bool) for a normal, non-rejected participant
    - an object/dict with a reason/timestamp for rejected participants

    We treat any truthy value or dict as "rejected" and exclude such records.
    """
    rejected = rec.get("rejected", False)

    # Explicit non-rejected values
    if rejected is False or rejected is None:
        return True

    # If it's a dict (e.g. {"reason": "...", "timestamp": ...}), consider it rejected
    if isinstance(rejected, dict):
        return False

    # Any other truthy value is treated as rejected
    return not bool(rejected)


def load_completed_participants(path: Path | str = DEFAULT_INPUT_PATH):
    """Return participant records that are completed and not rejected.

    - `completed` must be `True`
    - `rejected` must be absent, `False`, or `None`
    """
    data = load_study_json(path)
    if not isinstance(data, list):
        return []

    filtered: list[Dict[str, Any]] = []
    for rec in data:
        if not isinstance(rec, dict):
            continue
        if rec.get("completed") is True and _is_not_rejected(rec):
            filtered.append(rec)
    return filtered



