from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .io import DEFAULT_INPUT_PATH, load_completed_participants


QUESTIONNAIRE_RE = re.compile(r"^(badge|footnote)-questionn?aire-(\d+)$")

# Open-ended fields from *-questionaire-1 and *-questionaire-2
OPEN_TEXT_KEYS: List[str] = [
    "notice-comments",
    "experience-with-badges",
    "ease-of-understanding",
    "considered-in-notes",
    "most-least-useful",
    "overall-help",
    "final-comments",
]


def _iter_participants(data: Iterable[Dict[str, Any]]):
    for record in data:
        yield record


def _iter_open_rows(data: List[Dict[str, Any]]):
    for rec in _iter_participants(data):
        participant_id = rec.get("participantId")
        answers: Dict[str, Any] = rec.get("answers", {})

        group: str | None = None
        open_values: Dict[str, str | None] = {k: None for k in OPEN_TEXT_KEYS}

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
            for key in OPEN_TEXT_KEYS:
                if key in ans and (ans[key] or ans[key] == ""):
                    open_values[key] = ans[key]

        if group is None:
            continue

        row: Dict[str, Any] = {"group": group, "participantId": participant_id}
        row.update(open_values)
        yield row


def export_questionnaire_open(
    src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
    dst: Path | str = DEFAULT_INPUT_PATH.parent / "questionnaire_open_responses.csv",
) -> Path:
    import json

    src_path = Path(src)
    dst_path = Path(dst)

    data = load_completed_participants(src_path)

    fieldnames = ["group", "participantId"] + OPEN_TEXT_KEYS
    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in _iter_open_rows(data):
            writer.writerow(row)

    return dst_path


def main() -> None:
    export_questionnaire_open()


if __name__ == "__main__":
    main()


