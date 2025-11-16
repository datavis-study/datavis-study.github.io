from __future__ import annotations

import csv
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from .io import DEFAULT_INPUT_PATH, load_completed_participants


def _iter_participants(data: Iterable[Dict[str, Any]]):
    for record in data:
        yield record


_STIMULUS_SUFFIX_RE = re.compile(r"-(badges|footnotes)$")
_QUESTIONNAIRE_RE = re.compile(r"^(?:badge|footnote)-questionna?ire-(\d+)$")


def _normalize_component_name(name: str) -> Tuple[str, str | None]:
    """Return (normalized_name, group or None).

    - For stimulus components ending with -badges/-footnotes, strip the suffix
      so that both map to the same normalized column, and return group.
    - For all others, keep the original name and group None.
    """
    # Merge stimuli variants into a single column with " (s)" suffix
    m = _STIMULUS_SUFFIX_RE.search(name)
    if m:
        group = "badge" if m.group(1) == "badges" else "footnote"
        base = name[: m.start()]
        return f"{base} (s)", group

    # Merge questionnaire variants (badge/footnote-questionnaire-1/2 → questionnaire-1 (s))
    mq = _QUESTIONNAIRE_RE.match(name)
    if mq:
        num = mq.group(1)
        return f"questionnaire-{num} (s)", None
    return name, None


def _collect_time_spent_rows(data: List[Dict[str, Any]]):
    # Build a stable ordered set of all normalized component names encountered
    component_order: List[str] = []
    component_seen: Set[str] = set()
    rows: List[Dict[str, Any]] = []

    for rec in _iter_participants(data):
        participant_id = rec.get("participantId")
        answers: Dict[str, Any] = rec.get("answers", {})

        participant_group: str | None = None
        timings_ms: Dict[str, int] = OrderedDict()
        for _, trial in answers.items():
            if not isinstance(trial, dict):
                continue
            name = trial.get("componentName")
            start = trial.get("startTime")
            end = trial.get("endTime")
            if name is None or start is None or end is None:
                continue

            norm_name, group = _normalize_component_name(str(name))
            if group and participant_group is None:
                participant_group = group

            try:
                duration_ms = int(end) - int(start)
            except Exception:
                continue
            timings_ms[norm_name] = timings_ms.get(norm_name, 0) + max(0, duration_ms)

            if norm_name not in component_seen:
                component_seen.add(norm_name)
                component_order.append(norm_name)

        # Convert to seconds (float)
        timings_sec = {k: (v / 1000.0) for k, v in timings_ms.items()}

        row = {"participantId": participant_id, "group": participant_group or "unknown"}
        row.update({name: timings_sec.get(name, 0.0) for name in component_order})
        rows.append(row)

    return component_order, rows


def export_time_spent(
    src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
    dst: Path | str = DEFAULT_INPUT_PATH.parent / "participant_time_per_component.csv",
) -> Path:
    import json

    src_path = Path(src)
    dst_path = Path(dst)

    data = load_completed_participants(src_path)

    component_order, rows = _collect_time_spent_rows(data)

    fieldnames = ["participantId", "group"] + component_order + ["total (s)"]
    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Ensure all fields present
            for name in component_order:
                row.setdefault(name, 0.0)
            # Compute total seconds across all normalized components
            row["total (s)"] = sum(float(row.get(name, 0.0)) for name in component_order)
            writer.writerow(row)

    return dst_path


def main() -> None:
    export_time_spent()


if __name__ == "__main__":
    main()


from __future__ import annotations

import csv
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from .io import DEFAULT_INPUT_PATH, load_completed_participants


def _iter_participants(data: Iterable[Dict[str, Any]]):
	for record in data:
		yield record


_STIMULUS_SUFFIX_RE = re.compile(r"-(badges|footnotes)$")
_QUESTIONNAIRE_RE = re.compile(r"^(?:badge|footnote)-questionna?ire-(\d+)$")


def _normalize_component_name(name: str) -> Tuple[str, str | None]:
	"""Return (normalized_name, group or None).

	- For stimulus components ending with -badges/-footnotes, strip the suffix
	  so that both map to the same normalized column, and return group.
	- For all others, keep the original name and group None.
	"""
	# Merge stimuli variants into a single column with " (s)" suffix
	m = _STIMULUS_SUFFIX_RE.search(name)
	if m:
		group = "badge" if m.group(1) == "badges" else "footnote"
		base = name[: m.start()]
		return f"{base} (s)", group

	# Merge questionnaire variants (badge/footnote-questionnaire-1/2 → questionnaire-1 (s))
	mq = _QUESTIONNAIRE_RE.match(name)
	if mq:
		num = mq.group(1)
		return f"questionnaire-{num} (s)", None
	return name, None


def _collect_time_spent_rows(data: List[Dict[str, Any]]):
	# Build a stable ordered set of all normalized component names encountered
	component_order: List[str] = []
	component_seen: Set[str] = set()
	rows: List[Dict[str, Any]] = []

	for rec in _iter_participants(data):
		participant_id = rec.get("participantId")
		answers: Dict[str, Any] = rec.get("answers", {})

		participant_group: str | None = None
		timings_ms: Dict[str, int] = OrderedDict()
		for _, trial in answers.items():
			if not isinstance(trial, dict):
				continue
			name = trial.get("componentName")
			start = trial.get("startTime")
			end = trial.get("endTime")
			if name is None or start is None or end is None:
				continue

			norm_name, group = _normalize_component_name(str(name))
			if group and participant_group is None:
				participant_group = group

			try:
				duration_ms = int(end) - int(start)
			except Exception:
				continue
			timings_ms[norm_name] = timings_ms.get(norm_name, 0) + max(0, duration_ms)

			if norm_name not in component_seen:
				component_seen.add(norm_name)
				component_order.append(norm_name)

		# Convert to seconds (float)
		timings_sec = {k: (v / 1000.0) for k, v in timings_ms.items()}

		row = {"participantId": participant_id, "group": participant_group or "unknown"}
		row.update({name: timings_sec.get(name, 0.0) for name in component_order})
		rows.append(row)

	return component_order, rows


def export_time_spent(
	src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
	dst: Path | str = DEFAULT_INPUT_PATH.parent / "participant_time_per_component.csv",
) -> Path:
	import json

	src_path = Path(src)
	dst_path = Path(dst)

	data = load_completed_participants(src_path)

	component_order, rows = _collect_time_spent_rows(data)

	fieldnames = ["participantId", "group"] + component_order + ["total (s)"]
	with open(dst_path, "w", encoding="utf-8", newline="") as f:
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		for row in rows:
			# Ensure all fields present
			for name in component_order:
				row.setdefault(name, 0.0)
			# Compute total seconds across all normalized components
			row["total (s)"] = sum(float(row.get(name, 0.0)) for name in component_order)
			writer.writerow(row)

	return dst_path


def main() -> None:
	export_time_spent()


if __name__ == "__main__":
	main()



