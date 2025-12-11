from __future__ import annotations

"""
Export a compact CSV with preference choices from the s1b pilot studies.

One row per participant, columns:

- group                           ("badges" / "footnotes")
- participantId
- global_understanding_choice
- global_understanding_why
- global_presenting_choice
- global_presenting_why
- co2_understanding_choice
- co2_understanding_why
- co2_presenting_choice
- co2_presenting_why

Each "*_choice" is normalised to:
  - "badges"
  - "footnotes"
  - "no_preference"
  - None  (missing)
The corresponding "*_why" columns contain the raw free‑text explanations.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_BADGES_JSON = BASE_DIR / "data" / "s1b" / "s1b-badges_all.json"
DEFAULT_FOOTNOTES_JSON = BASE_DIR / "data" / "s1b" / "s1b-footnotes_all.json"
DEFAULT_OUTPUT = BASE_DIR / "data" / "s1b" / "preferences.csv"


def _load_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}, got {type(data)!r}")
    return [r for r in data if isinstance(r, dict)]


def _normalise_preference(answer_text: Any) -> str | None:
    """Map the full option text to 'badges' / 'footnotes' / 'no_preference'."""
    if not isinstance(answer_text, str):
        return None
    text = answer_text.lower()
    if "no clear preference" in text:
        return "no_preference"
    if "visualization badges" in text or "visualisation badges" in text or "badges" in text:
        # If both badges and footnotes appear, try to disambiguate via parentheses
        if "version with visualization badges" in text and "version with footnotes" in text:
            # Look for "(left)" / "(right)" hints; fall back to badges
            if "prefer the version with visualization badges" in text:
                return "badges"
            if "prefer the version with footnotes" in text:
                return "footnotes"
        return "badges"
    if "footnotes" in text:
        return "footnotes"
    return None


def _extract_preferences_from_record(
    rec: Dict[str, Any],
    *,
    group: str,
) -> Dict[str, Any]:
    """
    Return a dict with group, participantId and four normalised preferences
    (global/co2 × understanding/presenting) for a single participant.
    """
    row: Dict[str, Any] = {
        "group": group,
        "participantId": rec.get("participantId"),
        "global_understanding_choice": None,
        "global_understanding_why": None,
        "global_presenting_choice": None,
        "global_presenting_why": None,
        "co2_understanding_choice": None,
        "co2_understanding_why": None,
        "co2_presenting_choice": None,
        "co2_presenting_why": None,
    }

    answers = rec.get("answers") or {}
    if not isinstance(answers, dict):
        return row

    for trial in answers.values():
        if not isinstance(trial, dict):
            continue
        comp = trial.get("componentName")
        if comp not in {"badge-global-comparison", "badge-co2-comparison"}:
            continue
        answer_obj = trial.get("answer") or {}
        if not isinstance(answer_obj, dict):
            continue

        if comp == "badge-global-comparison":
            row["global_understanding_choice"] = _normalise_preference(
                answer_obj.get("preferred-condition-global-understanding")
            )
            row["global_understanding_why"] = answer_obj.get(
                "preferred-condition-global-understanding-explanation"
            )

            row["global_presenting_choice"] = _normalise_preference(
                answer_obj.get("preferred-condition-global-presenting")
            )
            row["global_presenting_why"] = answer_obj.get(
                "preferred-condition-global-presenting-explanation"
            )
        elif comp == "badge-co2-comparison":
            row["co2_understanding_choice"] = _normalise_preference(
                answer_obj.get("preferred-condition-co2-understanding")
            )
            row["co2_understanding_why"] = answer_obj.get(
                "preferred-condition-co2-understanding-explanation"
            )

            row["co2_presenting_choice"] = _normalise_preference(
                answer_obj.get("preferred-condition-co2-presenting")
            )
            row["co2_presenting_why"] = answer_obj.get(
                "preferred-condition-co2-presenting-explanation"
            )

    return row


def export_preferences(
    badges_json: Path = DEFAULT_BADGES_JSON,
    footnotes_json: Path = DEFAULT_FOOTNOTES_JSON,
    output_csv: Path = DEFAULT_OUTPUT,
) -> Path:
    """Create preferences.csv combining badges and footnotes pilots."""
    rows: List[Dict[str, Any]] = []

    if badges_json.exists():
        for rec in _load_json(badges_json):
            rows.append(_extract_preferences_from_record(rec, group="badges"))

    if footnotes_json.exists():
        for rec in _load_json(footnotes_json):
            rows.append(_extract_preferences_from_record(rec, group="footnotes"))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "group",
        "participantId",
        "global_understanding_choice",
        "global_understanding_why",
        "global_presenting_choice",
        "global_presenting_why",
        "co2_understanding_choice",
        "co2_understanding_why",
        "co2_presenting_choice",
        "co2_presenting_why",
    ]

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return output_csv


def main() -> None:
    out = export_preferences()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

