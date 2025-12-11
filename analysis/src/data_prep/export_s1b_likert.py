from __future__ import annotations

"""
Export a compact CSV with final Likert-scale responses from the s1b pilots.

One row per participant, columns:

- group           ("badges" / "footnotes")
- participantId
- participantIndex
- prolificPid

- saliency_badges
- saliency_footnotes
- clutter_badges
- clutter_footnotes
- interpretability_badges
- interpretability_footnotes
- usefulness_badges
- usefulness_footnotes
- trust_badges
- trust_footnotes
- standardization_badges
- standardization_footnotes
- final_comments   (free text)
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parents[2]
BADGES_JSON = BASE_DIR / "data" / "s1b" / "s1b-badges_all.json"
FOOTNOTES_JSON = BASE_DIR / "data" / "s1b" / "s1b-footnotes_all.json"
OUTPUT_CSV = BASE_DIR / "data" / "s1b" / "likert.csv"


def _load_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data)!r}")
    return [r for r in data if isinstance(r, dict)]


LIKERT_KEYS_MAP = {
    "saliency-badges": "saliency_badges",
    "saliency-footnotes": "saliency_footnotes",
    "clutter-badges": "clutter_badges",
    "clutter-footnotes": "clutter_footnotes",
    "interpretability-badges": "interpretability_badges",
    "interpretability-footnotes": "interpretability_footnotes",
    "usefulness-badges": "usefulness_badges",
    "usefulness-footnotes": "usefulness_footnotes",
    "trust-badges": "trust_badges",
    "trust-footnotes": "trust_footnotes",
    "standardization-badges": "standardization_badges",
    "standardization-footnotes": "standardization_footnotes",
    "final-comments-badges": "final_comments",
}


def _extract_likert_row(rec: Dict[str, Any], group: str) -> Dict[str, Any]:
    """Get identifiers and final Likert answers for a single participant."""
    row: Dict[str, Any] = {
        "group": group,
        "participantId": rec.get("participantId"),
        "participantIndex": rec.get("participantIndex"),
        "prolificPid": None,
    }

    # Classic identifier from searchParams
    search_params = rec.get("searchParams") or {}
    if isinstance(search_params, dict):
        row["prolificPid"] = search_params.get("PROLIFIC_PID")

    # Initialise all likert columns to None
    for col in LIKERT_KEYS_MAP.values():
        row[col] = None

    answers = rec.get("answers") or {}
    if not isinstance(answers, dict):
        return row

    trial = None
    for t in answers.values():
        if isinstance(t, dict) and t.get("componentName") == "badge-likert-badges":
            trial = t
            break

    answer_obj = trial.get("answer") if trial else {}
    if not isinstance(answer_obj, dict):
        return row

    for raw_key, col_name in LIKERT_KEYS_MAP.items():
        row[col_name] = answer_obj.get(raw_key)

    return row


def export_likert(
    badges_json: Path = BADGES_JSON,
    footnotes_json: Path = FOOTNOTES_JSON,
    output_csv: Path = OUTPUT_CSV,
) -> Path:
    rows: List[Dict[str, Any]] = []

    if badges_json.exists():
        for rec in _load_json(badges_json):
            rows.append(_extract_likert_row(rec, group="badges"))

    if footnotes_json.exists():
        for rec in _load_json(footnotes_json):
            rows.append(_extract_likert_row(rec, group="footnotes"))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "group",
        "participantId",
        "participantIndex",
        "prolificPid",
        *LIKERT_KEYS_MAP.values(),
    ]

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return output_csv


def main() -> None:
    out = export_likert()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

