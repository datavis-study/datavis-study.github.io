from __future__ import annotations

"""
Export a compact "quick_reminder" CSV for the s1b pilot studies.

The CSV has one row per participant and columns:

- group               (\"badges\" or \"footnotes\")
- participantId
- rememberStudy       (answer to \"Do you remember taking part in this study?\")
- rememberStimuli     (answer to \"Do you remember reading visualizations with ...?\")

It reads from the two pilot JSON exports:

  analysis/data/s1b/s1b-badges_all.json
  analysis/data/s1b/s1b-footnotes_all.json
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_BADGES_JSON = BASE_DIR / "data" / "s1b" / "s1b-badges_all.json"
DEFAULT_FOOTNOTES_JSON = BASE_DIR / "data" / "s1b" / "s1b-footnotes_all.json"
DEFAULT_OUTPUT = BASE_DIR / "data" / "s1b" / "quick_reminder.csv"


def _load_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}, got {type(data)!r}")
    return [r for r in data if isinstance(r, dict)]


def _extract_reminder_row(
    rec: Dict[str, Any],
    *,
    group: str,
    component_name: str,
    qid_study: str,
    qid_stimuli: str,
) -> Dict[str, Any]:
    """Extract quick‑reminder answers for a single participant record."""
    answers = rec.get("answers") or {}
    component_trial: Dict[str, Any] | None = None

    if isinstance(answers, dict):
        for trial in answers.values():
            if not isinstance(trial, dict):
                continue
            if trial.get("componentName") == component_name:
                component_trial = trial
                break

    answer_obj = component_trial.get("answer") if component_trial else {}
    if not isinstance(answer_obj, dict):
        answer_obj = {}

    return {
        "group": group,
        "participantId": rec.get("participantId"),
        "rememberStudy": answer_obj.get(qid_study),
        "rememberStimuli": answer_obj.get(qid_stimuli),
    }


def export_quick_reminder(
    badges_json: Path = DEFAULT_BADGES_JSON,
    footnotes_json: Path = DEFAULT_FOOTNOTES_JSON,
    output_csv: Path = DEFAULT_OUTPUT,
) -> Path:
    """Create quick_reminder.csv combining badges and footnotes pilots."""
    rows: List[Dict[str, Any]] = []

    # s1b-badges pilot: reminder-original-study-badges component
    if badges_json.exists():
        for rec in _load_json(badges_json):
            rows.append(
                _extract_reminder_row(
                    rec,
                    group="badges",
                    component_name="reminder-original-study-badges",
                    qid_study="remember-original-study-badges",
                    qid_stimuli="remember-badge-stimuli",
                )
            )

    # s1b-footnotes pilot: reminder-original-study component
    if footnotes_json.exists():
        for rec in _load_json(footnotes_json):
            rows.append(
                _extract_reminder_row(
                    rec,
                    group="footnotes",
                    component_name="reminder-original-study",
                    qid_study="remember-original-study",
                    qid_stimuli="remember-footnote-stimuli",
                )
            )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["group", "participantId", "rememberStudy", "rememberStimuli"]

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return output_csv


def main() -> None:
    out = export_quick_reminder()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

