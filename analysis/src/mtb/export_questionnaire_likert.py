from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .io import DEFAULT_INPUT_PATH, load_completed_participants


QUESTIONNAIRE_RE = re.compile(r"^(badge|footnote)-questionn?aire-(\d+)$")

# Likert question IDs as defined in config for *-questionaire-2
LIKERT_KEYS: List[str] = [
    "saliency",
    "clutter",
    "interpretability",
    "usefulness",
    "trust",
    "standardization",
]


def _iter_participants(data: Iterable[Dict[str, Any]]):
    for record in data:
        yield record


def _iter_likert_rows(data: List[Dict[str, Any]]):
    for rec in _iter_participants(data):
        participant_id = rec.get("participantId")
        answers: Dict[str, Any] = rec.get("answers", {})

        group: str | None = None
        likert_values: Dict[str, Any] = {k: None for k in LIKERT_KEYS}

        for _, trial in answers.items():
            if not isinstance(trial, dict):
                continue
            comp = trial.get("componentName")
            if not isinstance(comp, str):
                continue
            m = QUESTIONNAIRE_RE.match(comp)
            if not m:
                continue
            grp = "badge" if m.group(1) == "badge" else "footnote"
            group = group or grp

            ans = trial.get("answer", {})
            if not isinstance(ans, dict):
                continue
            for key in LIKERT_KEYS:
                if key in ans:
                    likert_values[key] = ans[key]

        if group is None:
            continue

        row = {"group": group, "participantId": participant_id}
        for key in LIKERT_KEYS:
            val = likert_values.get(key)
            # try numeric cast
            try:
                if val is not None and val != "":
                    val = int(val)
            except Exception:
                pass
            row[key] = val
        yield row


def export_questionnaire_likert(
    src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
    dst: Path | str = DEFAULT_INPUT_PATH.parent / "questionnaire_likert_scores.csv",
) -> Path:
    import json

    src_path = Path(src)
    dst_path = Path(dst)

    data = load_completed_participants(src_path)

    fieldnames = ["group", "participantId"] + LIKERT_KEYS
    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in _iter_likert_rows(data):
            writer.writerow(row)

    return dst_path


def main() -> None:
    export_questionnaire_likert()


if __name__ == "__main__":
    main()


