from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from .io import DEFAULT_INPUT_PATH, load_completed_participants


# Known component names for the demographics form in this study
DEMOGRAPHICS_RE = re.compile(r"^(demographics|demographics-custom)$")

# Preferred column order for common demographics fields; any extra keys discovered
# in the data will be appended (sorted) after these.
PREFERRED_FIELDS: List[str] = [
    "gender",
    "gender-other",
    "age",
    "education",
    "education-other",
    "field-of-study",
    "field-of-study-other",
    "chart-reading-frequency",
    "chart-creation-frequency",
    "color-vision",
    "color-vision-type",
]


def _iter_participants(data: Iterable[Dict[str, Any]]):
    for record in data:
        yield record


def _load_id_map(csv_path: Path) -> dict:
    try:
        mapping = {}
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                pid = row.get("participantId")
                rid = row.get("readableId")
                if pid and rid:
                    mapping[str(pid)] = str(rid)
        return mapping
    except Exception:
        return {}


def _collect_fieldnames(data: List[Dict[str, Any]]) -> List[str]:
    seen_keys: Set[str] = set()
    for rec in _iter_participants(data):
        answers: Dict[str, Any] = rec.get("answers", {})
        for _, trial in answers.items():
            if not isinstance(trial, dict):
                continue
            comp = trial.get("componentName")
            if not isinstance(comp, str) or not DEMOGRAPHICS_RE.match(comp):
                continue
            ans = trial.get("answer", {})
            if isinstance(ans, dict):
                # Demographics answers tend to be stored under direct keys or under "form"
                form = ans.get("form") if isinstance(ans.get("form"), dict) else ans
                if isinstance(form, dict):
                    for k in form.keys():
                        if isinstance(k, str) and k:
                            seen_keys.add(k)
    # Order: id columns first, then preferred, then any remaining sorted
    ordered: List[str] = []
    for k in PREFERRED_FIELDS:
        if k in seen_keys:
            ordered.append(k)
            seen_keys.remove(k)
    ordered.extend(sorted(seen_keys))
    return ordered


def _iter_rows(data: List[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    id_map = _load_id_map(DEFAULT_INPUT_PATH.parent / "participants.csv")
    fieldnames_dynamic = _collect_fieldnames(data)

    for rec in _iter_participants(data):
        participant_id = rec.get("participantId")
        answers: Dict[str, Any] = rec.get("answers", {})

        row: Dict[str, Any] = {"participantId": participant_id, "readableId": id_map.get(str(participant_id))}
        # Initialize with None for all dynamic fields to keep a consistent shape
        for k in fieldnames_dynamic:
            row[k] = None

        found = False
        for _, trial in answers.items():
            if not isinstance(trial, dict):
                continue
            comp = trial.get("componentName")
            if not isinstance(comp, str) or not DEMOGRAPHICS_RE.match(comp):
                continue
            ans = trial.get("answer", {})
            if not isinstance(ans, dict):
                continue
            form = ans.get("form") if isinstance(ans.get("form"), dict) else ans
            if not isinstance(form, dict):
                continue
            for k in fieldnames_dynamic:
                if k in form:
                    row[k] = form.get(k)
            found = True
            # Assume a single demographics form per participant; break
            break

        if found:
            yield row


def export_demographics(
    src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
    dst: Path | str = DEFAULT_INPUT_PATH.parent / "demographics.csv",
) -> Path:
    src_path = Path(src)
    dst_path = Path(dst)

    data = load_completed_participants(src_path)

    dynamic_fields = _collect_fieldnames(data)
    fieldnames = ["participantId", "readableId"] + dynamic_fields

    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in _iter_rows(data):
            writer.writerow(row)

    return dst_path


def main() -> None:
    export_demographics()


if __name__ == "__main__":
    main()



