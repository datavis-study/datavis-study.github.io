from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .io import DEFAULT_INPUT_PATH, load_completed_participants
from reporting.text_clean import clean_text


_STIMULUS_SUFFIX_RE = re.compile(r"-(badges|footnotes)$")


def _normalize_stimulus(name: str) -> Tuple[str, str | None]:
    m = _STIMULUS_SUFFIX_RE.search(name)
    if m:
        group = "badge" if m.group(1) == "badges" else "footnote"
        base = name[: m.start()]
        return base, group
    return name, None


def _load_id_map(csv_path: Path) -> dict:
    try:
        import csv  # local import to avoid top-level circularities
        mapping = {}
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            for i, row in enumerate(csv.DictReader(f)):
                pid = row.get("participantId")
                rid = row.get("readableId")
                if pid and rid:
                    mapping[str(pid)] = str(rid)
        return mapping
    except Exception:
        return {}


def _iter_rows(data: List[Dict[str, Any]]):
    id_map = _load_id_map(DEFAULT_INPUT_PATH.parent / "participants.csv")
    for rec in data:
        participant_id = rec.get("participantId")
        answers: Dict[str, Any] = rec.get("answers", {})
        participant_group: str | None = None

        for _, trial in answers.items():
            if not isinstance(trial, dict):
                continue
            comp = trial.get("componentName")
            if not isinstance(comp, str):
                continue
            base, grp = _normalize_stimulus(comp)
            if grp:
                participant_group = participant_group or grp

            # Only include stimuli components (those that matched grp)
            if grp is None:
                continue

            answer = trial.get("answer", {})
            if not isinstance(answer, dict):
                continue
            raw = answer.get("main-observations", "")
            # Clean to a single cohesive blob (no newlines, normalized spaces)
            text = clean_text(raw).replace("\n", " ").strip()

            yield {
                "group": participant_group or grp or "unknown",
                "participantId": participant_id,
                "readableId": id_map.get(str(participant_id)),
                "stimulusId": base,
                "speech": text,
            }


def export_speech(
    src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
    dst: Path | str = DEFAULT_INPUT_PATH.parent / "stimulus_notes.csv",
) -> Path:
    import json

    src_path = Path(src)
    dst_path = Path(dst)

    data = load_completed_participants(src_path)

    rows = list(_iter_rows(data))

    fieldnames = ["group", "participantId", "readableId", "stimulusId", "speech"]
    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return dst_path


def main() -> None:
    export_speech()


if __name__ == "__main__":
    main()


