from __future__ import annotations

import csv
import json
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .io import DEFAULT_INPUT_PATH, load_completed_participants
from reporting.name_pool import NAMES as NAME_POOL


def _load_db(path: Path | str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    raise ValueError("Expected a list of participant records in db.json")


def _find_group_in_sequence(seq_obj: Any) -> Optional[str]:
    """Return the assigned group id under the 'group-assignment' node in sequence.

    The sequence structure can nest dicts and strings. We traverse until we find a dict
    whose id is 'group-assignment'; then we look at its 'components' and return the id
    of the immediate child dict (e.g., 'badge-group', 'footnote-group').
    """
    if isinstance(seq_obj, dict):
        if seq_obj.get("id") == "group-assignment":
            components = seq_obj.get("components")
            if isinstance(components, list):
                for item in components:
                    if isinstance(item, dict) and item.get("id"):
                        return str(item.get("id"))
            return None
        # Recurse into children
        for key in ("components",):
            child = seq_obj.get(key)
            if isinstance(child, list):
                for item in child:
                    group = _find_group_in_sequence(item)
                    if group is not None:
                        return group
        return None
    elif isinstance(seq_obj, list):
        for item in seq_obj:
            group = _find_group_in_sequence(item)
            if group is not None:
                return group
        return None
    else:
        return None


_ip_country_cache: Dict[str, Optional[str]] = {}


def _http_get_text(url: str, timeout: float = 1.5) -> Optional[str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="ignore").strip()
            return data or None
    except (urllib.error.URLError, socket.timeout, ValueError):
        return None


def _lookup_country(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    if ip in _ip_country_cache:
        return _ip_country_cache[ip]

    # Try ipapi.co first (simple text endpoint)
    country = _http_get_text(f"https://ipapi.co/{ip}/country_name/")
    if not country:
        # Fallback to ipinfo.io (returns JSON; but try text country first)
        two_letter = _http_get_text(f"https://ipinfo.io/{ip}/country")
        country = two_letter
    _ip_country_cache[ip] = country
    return country


def export_participant_meta(
    src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
    dst: Path | str = DEFAULT_INPUT_PATH.parent / "participants.csv",
) -> Path:
    src_path = Path(src)
    dst_path = Path(dst)

    participants = load_completed_participants(src_path)

    # Build stable mapping participantId -> readableId like U001, U002 (by participantIndex if available)
    def _build_mapping(recs: Iterable[Dict[str, Any]]) -> Dict[str, str]:
        # Deterministic assignment from a fixed name pool.
        # Order by participantIndex if available; otherwise by participantId.
        items: list[tuple[int | None, str]] = []
        for r in recs:
            pid = r.get("participantId")
            if not pid:
                continue
            try:
                idx = int(r.get("participantIndex")) if r.get("participantIndex") is not None else None
            except Exception:
                idx = None
            items.append((idx, str(pid)))
        items.sort(key=lambda t: (t[0] is None, -1 if t[0] is None else t[0], t[1]))
        mapping: Dict[str, str] = {}
        used: set[str] = set()
        for i, (_, pid) in enumerate(items):
            base = NAME_POOL[i % len(NAME_POOL)]
            # If pool wraps, append a small numeric suffix starting from 2
            suffix = (i // len(NAME_POOL)) + 1
            name = base if (suffix == 1 and base not in used) else f"{base}{suffix if suffix > 1 else ''}"
            used.add(name)
            mapping[pid] = name
        return mapping

    id_map = _build_mapping(participants)

    fieldnames = [
        "readableId",
        "participantGroup",
        "participantId",
        "isProlific",
        "participantIndex",
        "completed",
        "ip",
        "country",
        "language",
        "userAgent",
        "resolutionWidth",
        "resolutionHeight",
    ]

    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rec in participants:
            seq = rec.get("sequence", {})
            participant_group = _find_group_in_sequence(seq)

            participant_id = rec.get("participantId")
            participant_index = rec.get("participantIndex")
            completed = rec.get("completed", False)

            # Mark whether this participant came via Prolific (True/False)
            search_params = rec.get("searchParams", {})
            if isinstance(search_params, dict):
                is_prolific = bool(search_params.get("PROLIFIC_PID"))
            else:
                is_prolific = False

            metadata = rec.get("metadata", {}) if isinstance(rec.get("metadata"), dict) else {}
            language = metadata.get("language")
            user_agent = metadata.get("userAgent")
            resolution = metadata.get("resolution", {}) if isinstance(metadata.get("resolution"), dict) else {}
            width = resolution.get("width")
            height = resolution.get("height")
            ip = metadata.get("ip")

            country = _lookup_country(ip)

            writer.writerow(
                {
                    "readableId": id_map.get(participant_id),
                    "participantGroup": participant_group,
                    "participantId": participant_id,
                    "isProlific": is_prolific,
                    "participantIndex": participant_index,
                    "completed": completed,
                    "ip": ip,
                    "country": country,
                    "language": language,
                    "userAgent": user_agent,
                    "resolutionWidth": width,
                    "resolutionHeight": height,
                }
            )

    # Also write a standalone mapping CSV for convenience
    map_path = dst_path.parent / "participant_id_map.csv"
    with open(map_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["participantId", "readableId", "isProlific"])
        writer.writeheader()
        # Build a lookup from participantId to a simple True/False flag for Prolific
        is_prolific_by_pid: Dict[str, bool] = {}
        for rec in participants:
            pid = rec.get("participantId")
            if not pid:
                continue
            search_params = rec.get("searchParams", {})
            if isinstance(search_params, dict):
                is_prolific = bool(search_params.get("PROLIFIC_PID"))
            else:
                is_prolific = False
            is_prolific_by_pid[str(pid)] = is_prolific

        for pid, rid in id_map.items():
            writer.writerow(
                {
                    "participantId": pid,
                    "readableId": rid,
                    "isProlific": is_prolific_by_pid.get(pid, False),
                }
            )

    return dst_path


def main() -> None:
    export_participant_meta()


if __name__ == "__main__":
    main()


