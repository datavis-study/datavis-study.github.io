from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from .io import DEFAULT_INPUT_PATH, load_completed_participants


_BADGE_STIMULUS_RE = re.compile(r"^(?P<base>.+)-badges$")


def _iter_participants(data: Iterable[Dict[str, Any]]):
    for record in data:
        yield record


def _seconds(ms: Any) -> float | None:
    if ms is None:
        return None
    try:
        val = float(ms)
    except (TypeError, ValueError):
        return None
    return val / 1000.0


def export_badge_stats(
    src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
    dst: Path | str = DEFAULT_INPUT_PATH.parent / "stimulus_badge_metrics.csv",
) -> Path:
    import json

    src_path = Path(src)
    dst_path = Path(dst)

    data = load_completed_participants(src_path)

    # Aggregation keyed by (stimulusId, badgeId)
    rows: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for rec in _iter_participants(data):
        answers: Dict[str, Any] = rec.get("answers", {})
        for _, trial in answers.items():
            if not isinstance(trial, dict):
                continue
            name = trial.get("componentName")
            if not isinstance(name, str):
                continue
            m = _BADGE_STIMULUS_RE.match(name)
            stimulus_id = m.group("base") if m else name

            ans = trial.get("answer", {}) if isinstance(trial.get("answer", {}), dict) else {}

            # Ensure all available badges have an entry (even without interactions)
            available = ans.get("availableBadges")
            if isinstance(available, list):
                for b in available:
                    if not isinstance(b, dict):
                        continue
                    badge_id = str(b.get("id", "")).strip()
                    badge_label = str(b.get("label", "")).strip()
                    if not badge_id and not badge_label:
                        continue
                    key = (stimulus_id, badge_id or badge_label)
                    if key not in rows:
                        rows[key] = {
                            "stimulusId": stimulus_id,
                            "badgeId": badge_id or None,
                            "badgeLabel": badge_label or None,
                            # Counters (sums across participants)
                            "clickCount": 0,
                            "hoverCount": 0,
                            "totalHoverTime": 0.0,  # seconds
                            "maxHoverTime": None,   # seconds
                            "minHoverTime": None,   # seconds
                            "drawerOpenCount": 0,
                            "totalDrawerOpenTime": 0.0,  # seconds
                            "maxDrawerOpenTime": None,    # seconds
                            "minDrawerOpenTime": None,    # seconds
                            # First-click aggregation (count trials where this badge was first clicked)
                            "firstBadgeClickCount": 0,
                        }

            aggregates = ans.get("badgeAggregates", {})
            tracking = ans.get("badgeTrackingData", {}).get("badgeInteractions", {})
            coverage = ans.get("badgeCoverage", {}) if isinstance(ans.get("badgeCoverage", {}), dict) else {}

            first_click_latency_by_badge: Dict[str, float] = {}
            if isinstance(aggregates, dict):
                for agg_id, agg in aggregates.items():
                    if not isinstance(agg, dict):
                        continue
                    badge_id = str(agg.get("badgeId", agg_id)).strip()
                    badge_label = str(agg.get("badgeLabel", "")).strip() or None
                    key = (stimulus_id, badge_id)
                    if key not in rows:
                        rows[key] = {
                            "stimulusId": stimulus_id,
                            "badgeId": badge_id or None,
                            "badgeLabel": badge_label,
                            "clickCount": 0,
                            "hoverCount": 0,
                            "totalHoverTime": 0.0,
                            "maxHoverTime": None,
                            "minHoverTime": None,
                            "drawerOpenCount": 0,
                            "totalDrawerOpenTime": 0.0,
                            "maxDrawerOpenTime": None,
                            "minDrawerOpenTime": None,
                            "firstBadgeClickCount": 0,
                        }
                    row = rows[key]

                    # Update label if missing
                    if not row.get("badgeLabel") and badge_label:
                        row["badgeLabel"] = badge_label

                    # Sum counters (convert ms to seconds for totals)
                    row["clickCount"] += int(agg.get("clickCount", 0) or 0)
                    row["hoverCount"] += int(agg.get("totalHoverCount", 0) or 0)
                    row["totalHoverTime"] += _seconds(agg.get("totalHoverTimeMs", 0)) or 0.0
                    row["drawerOpenCount"] += int(agg.get("drawerOpenCount", 0) or 0)
                    row["totalDrawerOpenTime"] += _seconds(agg.get("totalDrawerOpenTimeMs", 0)) or 0.0

                    # Collect first click latency for per-trial first-click determination
                    fcl = agg.get("firstClickLatencyMs")
                    if fcl is not None:
                        try:
                            first_click_latency_by_badge[badge_id] = float(fcl)
                        except (TypeError, ValueError):
                            pass

            # Determine which badge was the FIRST clicked in this trial (minimum latency)
            if first_click_latency_by_badge:
                min_latency = min(first_click_latency_by_badge.values())
                # In rare ties, increment all with equal minimal latency
                for bid, lat in first_click_latency_by_badge.items():
                    if lat == min_latency:
                        key = (stimulus_id, bid)
                        if key not in rows:
                            rows[key] = {
                                "stimulusId": stimulus_id,
                                "badgeId": bid or None,
                                "badgeLabel": None,
                                "clickCount": 0,
                                "hoverCount": 0,
                                "totalHoverTime": 0.0,
                                "maxHoverTime": None,
                                "minHoverTime": None,
                                "drawerOpenCount": 0,
                                "totalDrawerOpenTime": 0.0,
                                "maxDrawerOpenTime": None,
                                "minDrawerOpenTime": None,
                                "firstBadgeClickCount": 0,
                            }
                        rows[key]["firstBadgeClickCount"] += 1

            # Use detailed interactions to compute min/max durations
            if isinstance(tracking, dict):
                for tr_id, tr in tracking.items():
                    if not isinstance(tr, dict):
                        continue
                    badge_id = str(tr.get("badgeId", tr_id)).strip()
                    key = (stimulus_id, badge_id)
                    if key not in rows:
                        # Create a minimal row if not present yet
                        rows[key] = {
                            "stimulusId": stimulus_id,
                            "badgeId": badge_id or None,
                            "badgeLabel": tr.get("badgeLabel") or None,
                            "clickCount": 0,
                            "hoverCount": 0,
                            "totalHoverTime": 0.0,
                            "maxHoverTime": None,
                            "minHoverTime": None,
                            "drawerOpenCount": 0,
                            "totalDrawerOpenTime": 0.0,
                            "maxDrawerOpenTime": None,
                            "minDrawerOpenTime": None,
                            "firstBadgeClickCount": 0,
                        }
                    row = rows[key]

                    interactions = tr.get("interactions", [])
                    if not isinstance(interactions, list):
                        continue

                    # Hover durations are recorded on hover_end events
                    for ev in interactions:
                        if not isinstance(ev, dict):
                            continue
                        itype = ev.get("interactionType")
                        dur_ms = ev.get("duration")
                        if itype == "hover_end":
                            sec = _seconds(dur_ms)
                            if sec is not None and sec > 0:
                                # max
                                if row["maxHoverTime"] is None or sec > row["maxHoverTime"]:
                                    row["maxHoverTime"] = sec
                                # min
                                if row["minHoverTime"] is None or sec < row["minHoverTime"]:
                                    row["minHoverTime"] = sec
                        elif itype == "drawer_close":
                            sec = _seconds(dur_ms)
                            if sec is not None and sec > 0:
                                if row["maxDrawerOpenTime"] is None or sec > row["maxDrawerOpenTime"]:
                                    row["maxDrawerOpenTime"] = sec
                                if row["minDrawerOpenTime"] is None or sec < row["minDrawerOpenTime"]:
                                    row["minDrawerOpenTime"] = sec

    # Prepare CSV columns as requested
    fieldnames = [
        "stimulusId",
        "badgeId",
        "badgeLabel",
        # Click/interaction counts at the beginning
        "clickCount",
        "firstBadgeClickCount",
        "hoverCount",
        "drawerOpenCount",
        # Timing-related columns at the end
        "totalHoverTime",
        "maxHoverTime",
        "minHoverTime",
        "totalDrawerOpenTime",
        "maxDrawerOpenTime",
        "minDrawerOpenTime",
    ]

    # Normalize empty rows: if a badge has zero across all numeric fields and no min/max, leave totals as 0.0? -> per request, empty when no data recorded
    def _row_has_activity(r: Dict[str, Any]) -> bool:
        return any([
            r.get("clickCount", 0) or 0,
            r.get("hoverCount", 0) or 0,
            (r.get("totalHoverTime", 0.0) or 0.0) > 0,
            (r.get("totalDrawerOpenTime", 0.0) or 0.0) > 0,
            r.get("firstBadgeClickCount", 0) or 0,
            r.get("maxHoverTime") is not None,
            r.get("maxDrawerOpenTime") is not None,
        ])

    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for _, row in sorted(rows.items()):
            # If truly no data recorded, output empty/nulls
            if not _row_has_activity(row):
                out = {
                    "stimulusId": row.get("stimulusId"),
                    "badgeId": row.get("badgeId"),
                    "badgeLabel": row.get("badgeLabel"),
                    "clickCount": None,
                    "hoverCount": None,
                    "totalHoverTime": None,
                    "maxHoverTime": None,
                    "minHoverTime": None,
                    "drawerOpenCount": None,
                    "totalDrawerOpenTime": None,
                    "maxDrawerOpenTime": None,
                    "minDrawerOpenTime": None,
                    "firstBadgeClickCount": None,
                }
            else:
                out = {k: row.get(k) for k in fieldnames}
                # Round seconds for readability
                for k in [
                    "totalHoverTime",
                    "maxHoverTime",
                    "minHoverTime",
                    "totalDrawerOpenTime",
                    "maxDrawerOpenTime",
                    "minDrawerOpenTime",
                ]:
                    if out.get(k) is not None:
                        out[k] = round(float(out[k]), 3)
            writer.writerow(out)

    return dst_path


def main() -> None:
    export_badge_stats()


if __name__ == "__main__":
    main()


from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from .io import DEFAULT_INPUT_PATH, load_completed_participants


_BADGE_STIMULUS_RE = re.compile(r"^(?P<base>.+)-badges$")


def _iter_participants(data: Iterable[Dict[str, Any]]):
	for record in data:
		yield record


def _seconds(ms: Any) -> float | None:
	if ms is None:
		return None
	try:
		val = float(ms)
	except (TypeError, ValueError):
		return None
	return val / 1000.0


def export_badge_stats(
	src: Path | str = DEFAULT_INPUT_PATH.parent / "db.json",
	dst: Path | str = DEFAULT_INPUT_PATH.parent / "stimulus_badge_metrics.csv",
) -> Path:
	import json

	src_path = Path(src)
	dst_path = Path(dst)

	data = load_completed_participants(src_path)

	# Aggregation keyed by (stimulusId, badgeId)
	rows: Dict[Tuple[str, str], Dict[str, Any]] = {}

	for rec in _iter_participants(data):
		answers: Dict[str, Any] = rec.get("answers", {})
		for _, trial in answers.items():
			if not isinstance(trial, dict):
				continue
			name = trial.get("componentName")
			if not isinstance(name, str):
				continue
			m = _BADGE_STIMULUS_RE.match(name)
			stimulus_id = m.group("base") if m else name

			ans = trial.get("answer", {}) if isinstance(trial.get("answer", {}), dict) else {}

			# Ensure all available badges have an entry (even without interactions)
			available = ans.get("availableBadges")
			if isinstance(available, list):
				for b in available:
					if not isinstance(b, dict):
						continue
					badge_id = str(b.get("id", "")).strip()
					badge_label = str(b.get("label", "")).strip()
					if not badge_id and not badge_label:
						continue
					key = (stimulus_id, badge_id or badge_label)
					if key not in rows:
						rows[key] = {
							"stimulusId": stimulus_id,
							"badgeId": badge_id or None,
							"badgeLabel": badge_label or None,
							# Counters (sums across participants)
							"clickCount": 0,
							"hoverCount": 0,
							"totalHoverTime": 0.0,  # seconds
							"maxHoverTime": None,   # seconds
							"minHoverTime": None,   # seconds
							"drawerOpenCount": 0,
							"totalDrawerOpenTime": 0.0,  # seconds
							"maxDrawerOpenTime": None,    # seconds
							"minDrawerOpenTime": None,    # seconds
							# First-click aggregation (count trials where this badge was first clicked)
							"firstBadgeClickCount": 0,
						}

			aggregates = ans.get("badgeAggregates", {})
			tracking = ans.get("badgeTrackingData", {}).get("badgeInteractions", {})
			coverage = ans.get("badgeCoverage", {}) if isinstance(ans.get("badgeCoverage", {}), dict) else {}

			first_click_latency_by_badge: Dict[str, float] = {}
			if isinstance(aggregates, dict):
				for agg_id, agg in aggregates.items():
					if not isinstance(agg, dict):
						continue
					badge_id = str(agg.get("badgeId", agg_id)).strip()
					badge_label = str(agg.get("badgeLabel", "")).strip() or None
					key = (stimulus_id, badge_id)
					if key not in rows:
						rows[key] = {
							"stimulusId": stimulus_id,
							"badgeId": badge_id or None,
							"badgeLabel": badge_label,
							"clickCount": 0,
							"hoverCount": 0,
							"totalHoverTime": 0.0,
							"maxHoverTime": None,
							"minHoverTime": None,
							"drawerOpenCount": 0,
							"totalDrawerOpenTime": 0.0,
							"maxDrawerOpenTime": None,
							"minDrawerOpenTime": None,
							"firstBadgeClickCount": 0,
						}
					row = rows[key]

					# Update label if missing
					if not row.get("badgeLabel") and badge_label:
						row["badgeLabel"] = badge_label

					# Sum counters (convert ms to seconds for totals)
					row["clickCount"] += int(agg.get("clickCount", 0) or 0)
					row["hoverCount"] += int(agg.get("totalHoverCount", 0) or 0)
					row["totalHoverTime"] += _seconds(agg.get("totalHoverTimeMs", 0)) or 0.0
					row["drawerOpenCount"] += int(agg.get("drawerOpenCount", 0) or 0)
					row["totalDrawerOpenTime"] += _seconds(agg.get("totalDrawerOpenTimeMs", 0)) or 0.0

					# Collect first click latency for per-trial first-click determination
					fcl = agg.get("firstClickLatencyMs")
					if fcl is not None:
						try:
							first_click_latency_by_badge[badge_id] = float(fcl)
						except (TypeError, ValueError):
							pass

			# Determine which badge was the FIRST clicked in this trial (minimum latency)
			if first_click_latency_by_badge:
				min_latency = min(first_click_latency_by_badge.values())
				# In rare ties, increment all with equal minimal latency
				for bid, lat in first_click_latency_by_badge.items():
					if lat == min_latency:
						key = (stimulus_id, bid)
						if key not in rows:
							rows[key] = {
								"stimulusId": stimulus_id,
								"badgeId": bid or None,
								"badgeLabel": None,
								"clickCount": 0,
								"hoverCount": 0,
								"totalHoverTime": 0.0,
								"maxHoverTime": None,
								"minHoverTime": None,
								"drawerOpenCount": 0,
								"totalDrawerOpenTime": 0.0,
								"maxDrawerOpenTime": None,
								"minDrawerOpenTime": None,
								"firstBadgeClickCount": 0,
							}
						rows[key]["firstBadgeClickCount"] += 1

			# Use detailed interactions to compute min/max durations
			if isinstance(tracking, dict):
				for tr_id, tr in tracking.items():
					if not isinstance(tr, dict):
						continue
					badge_id = str(tr.get("badgeId", tr_id)).strip()
					key = (stimulus_id, badge_id)
					if key not in rows:
						# Create a minimal row if not present yet
						rows[key] = {
							"stimulusId": stimulus_id,
							"badgeId": badge_id or None,
							"badgeLabel": tr.get("badgeLabel") or None,
							"clickCount": 0,
							"hoverCount": 0,
							"totalHoverTime": 0.0,
							"maxHoverTime": None,
							"minHoverTime": None,
							"drawerOpenCount": 0,
							"totalDrawerOpenTime": 0.0,
							"maxDrawerOpenTime": None,
							"minDrawerOpenTime": None,
							"firstBadgeClickCount": 0,
						}
					row = rows[key]

					interactions = tr.get("interactions", [])
					if not isinstance(interactions, list):
						continue

					# Hover durations are recorded on hover_end events
					for ev in interactions:
						if not isinstance(ev, dict):
							continue
						itype = ev.get("interactionType")
						dur_ms = ev.get("duration")
						if itype == "hover_end":
							sec = _seconds(dur_ms)
							if sec is not None and sec > 0:
								# max
								if row["maxHoverTime"] is None or sec > row["maxHoverTime"]:
									row["maxHoverTime"] = sec
								# min
								if row["minHoverTime"] is None or sec < row["minHoverTime"]:
									row["minHoverTime"] = sec
						elif itype == "drawer_close":
							sec = _seconds(dur_ms)
							if sec is not None and sec > 0:
								if row["maxDrawerOpenTime"] is None or sec > row["maxDrawerOpenTime"]:
									row["maxDrawerOpenTime"] = sec
								if row["minDrawerOpenTime"] is None or sec < row["minDrawerOpenTime"]:
									row["minDrawerOpenTime"] = sec

	# Prepare CSV columns as requested
	fieldnames = [
		"stimulusId",
		"badgeId",
		"badgeLabel",
		# Click/interaction counts at the beginning
		"clickCount",
		"firstBadgeClickCount",
		"hoverCount",
		"drawerOpenCount",
		# Timing-related columns at the end
		"totalHoverTime",
		"maxHoverTime",
		"minHoverTime",
		"totalDrawerOpenTime",
		"maxDrawerOpenTime",
		"minDrawerOpenTime",
	]

	# Normalize empty rows: if a badge has zero across all numeric fields and no min/max, leave totals as 0.0? -> per request, empty when no data recorded
	def _row_has_activity(r: Dict[str, Any]) -> bool:
		return any([
			r.get("clickCount", 0) or 0,
			r.get("hoverCount", 0) or 0,
			(r.get("totalHoverTime", 0.0) or 0.0) > 0,
			(r.get("totalDrawerOpenTime", 0.0) or 0.0) > 0,
			r.get("firstBadgeClickCount", 0) or 0,
			r.get("maxHoverTime") is not None,
			r.get("maxDrawerOpenTime") is not None,
		])

	with open(dst_path, "w", encoding="utf-8", newline="") as f:
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		for _, row in sorted(rows.items()):
			# If truly no data recorded, output empty/nulls
			if not _row_has_activity(row):
				out = {
					"stimulusId": row.get("stimulusId"),
					"badgeId": row.get("badgeId"),
					"badgeLabel": row.get("badgeLabel"),
					"clickCount": None,
					"hoverCount": None,
					"totalHoverTime": None,
					"maxHoverTime": None,
					"minHoverTime": None,
					"drawerOpenCount": None,
					"totalDrawerOpenTime": None,
					"maxDrawerOpenTime": None,
					"minDrawerOpenTime": None,
					"firstBadgeClickCount": None,
				}
			else:
				out = {k: row.get(k) for k in fieldnames}
				# Round seconds for readability
				for k in [
					"totalHoverTime",
					"maxHoverTime",
					"minHoverTime",
					"totalDrawerOpenTime",
					"maxDrawerOpenTime",
					"minDrawerOpenTime",
				]:
					if out.get(k) is not None:
						out[k] = round(float(out[k]), 3)
			writer.writerow(out)

	return dst_path


def main() -> None:
	export_badge_stats()


if __name__ == "__main__":
	main()



