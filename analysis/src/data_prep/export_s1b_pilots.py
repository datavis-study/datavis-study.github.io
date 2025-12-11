from __future__ import annotations

"""
Utilities to flatten s1b pilot study JSON exports into a single, tidy CSV.

Input format
-----------
The input JSON is a list of participant records, e.g. the files:

    analysis/data/s1b/s1b-badges_all.json
    analysis/data/s1b/s1b-footnotes_all.json

Each record has at least:

    {
        "participantId": "...",
        "participantIndex": 1,
        "completed": true,
        "searchParams": {"PROLIFIC_PID": "...", ...},
        "metadata": {
            "language": "...",
            "userAgent": "...",
            "resolution": {"width": 1920, "height": 1080},
            ...
        },
        "answers": {
            "badge-likert-badges_8": {
                "componentName": "badge-likert-badges",
                "trialOrder": "8",
                "startTime": 1765472777476,
                "endTime": 1765472797979,
                "answer": {
                    "saliency-badges": "1",
                    "saliency-footnotes": "2",
                    ...
                },
                ...
            },
            ...
        }
    }

Output format
-------------
One CSV row per participant.

Columns:
- Core participant metadata:
    - participantId
    - participantIndex
    - completed
    - prolificPid
    - language
    - userAgent
    - resolutionWidth
    - resolutionHeight
- For every question encountered in any component:
    - "<componentName>::<questionId>"
      e.g. "badge-likert-badges::saliency-badges"
- For every component with timing information:
    - "<componentName>::time_ms"
      (sum of durations if the same componentName appears multiple times)

This is intentionally “wide” but very easy to inspect and analyse for a
small pilot sample.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _load_participants(path: Path) -> List[Dict[str, Any]]:
    """Load the list of participant records from a *_all.json file."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of records in {path}, got {type(data)!r}")
    return [r for r in data if isinstance(r, dict)]


def _collect_rows(
    participants: Iterable[Dict[str, Any]],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Flatten participant records into rows and discover all column names.

    Returns (fieldnames, rows).
    """
    rows: List[Dict[str, Any]] = []
    all_columns: set[str] = set()

    # Core metadata columns we always try to include
    base_columns = [
        "participantId",
        "participantIndex",
        "completed",
        "prolificPid",
        "language",
        "userAgent",
        "resolutionWidth",
        "resolutionHeight",
    ]
    all_columns.update(base_columns)

    for rec in participants:
        row: Dict[str, Any] = {}

        # --- Participant‑level metadata ------------------------------------
        row["participantId"] = rec.get("participantId")
        row["participantIndex"] = rec.get("participantIndex")
        row["completed"] = rec.get("completed", False)

        search_params = rec.get("searchParams") or {}
        if isinstance(search_params, dict):
            row["prolificPid"] = search_params.get("PROLIFIC_PID")
        else:
            row["prolificPid"] = None

        metadata = rec.get("metadata") or {}
        if isinstance(metadata, dict):
            row["language"] = metadata.get("language")
            row["userAgent"] = metadata.get("userAgent")
            resolution = metadata.get("resolution") or {}
            if isinstance(resolution, dict):
                row["resolutionWidth"] = resolution.get("width")
                row["resolutionHeight"] = resolution.get("height")
            else:
                row["resolutionWidth"] = None
                row["resolutionHeight"] = None
        else:
            row["language"] = None
            row["userAgent"] = None
            row["resolutionWidth"] = None
            row["resolutionHeight"] = None

        # --- Trial‑level answers and timing --------------------------------
        answers = rec.get("answers") or {}
        if isinstance(answers, dict):
            # We aggregate per componentName, so multiple trials of the same
            # component will have their time_ms summed.
            time_by_component: Dict[str, float] = {}

            for trial in answers.values():
                if not isinstance(trial, dict):
                    continue
                component_name = trial.get("componentName")
                if not isinstance(component_name, str):
                    # Fallback: skip anonymous components
                    continue

                comp_prefix = component_name

                # Question answers
                answer_obj = trial.get("answer") or {}
                if isinstance(answer_obj, dict):
                    for qid, value in answer_obj.items():
                        col = f"{comp_prefix}::{qid}"
                        row[col] = value
                        all_columns.add(col)

                # Timing (endTime - startTime in ms)
                start = trial.get("startTime")
                end = trial.get("endTime")
                if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                    duration = float(end) - float(start)
                    time_by_component[comp_prefix] = time_by_component.get(
                        comp_prefix, 0.0
                    ) + max(0.0, duration)

            # Write timing columns after processing all trials
            for comp_name, duration_ms in time_by_component.items():
                col = f"{comp_name}::time_ms"
                row[col] = duration_ms
                all_columns.add(col)

        rows.append(row)

    # Order columns: base metadata first, then all other columns sorted
    other_columns = sorted(c for c in all_columns if c not in base_columns)
    fieldnames = base_columns + other_columns
    return fieldnames, rows


def export_s1b_pilot(
    src: Path, dst: Path | None = None, *, overwrite: bool = True
) -> Path:
    """
    Flatten a s1b pilot JSON file into a CSV.

    Parameters
    ----------
    src:
        Path to `*_all.json` (e.g. `analysis/data/s1b/s1b-badges_all.json`).
    dst:
        Output CSV path. If omitted, uses the same stem with `.csv` extension.
    overwrite:
        If False and the destination exists, an error is raised.
    """
    src_path = Path(src)
    if dst is None:
        dst_path = src_path.with_suffix(".csv")
    else:
        dst_path = Path(dst)

    if dst_path.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {dst_path}")

    participants = _load_participants(src_path)
    fieldnames, rows = _collect_rows(participants)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with dst_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return dst_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Flatten s1b pilot JSON exports into a single CSV."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to *_all.json (e.g. analysis/data/s1b/s1b-badges_all.json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Optional output CSV path (defaults to <input_stem>.csv)",
    )
    args = parser.parse_args(argv)

    out = export_s1b_pilot(args.input, args.output)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

