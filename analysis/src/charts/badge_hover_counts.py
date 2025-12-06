from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import altair as alt
import pandas as pd

from reporting.util import figure_path


def _stimulus_order(labels: pd.Series) -> List[str]:
	"""Stable ordering for stimuli: prefer known IDs, then alphabetical."""
	known = [
		"global-warming-projection",
		"co2-emissions",
	]
	seen = [s for s in known if s in set(labels.dropna().astype(str).unique())]
	other = sorted(
		{s for s in labels.dropna().astype(str).unique() if s not in set(seen)},
	)
	return seen + other


def _stimulus_label(stimulus_id: str) -> str:
	label_map = {
		"global-warming-projection": "Global Warming Projection",
		"co2-emissions": "CO2 Emissions",
	}
	return label_map.get(str(stimulus_id), str(stimulus_id))


def _badge_sort_order(labels: pd.Series) -> list[str]:
	"""
	Stable badge ordering for x-axis:
	- Alphabetical by label
	- But any badge labelled exactly 'Contains Prediction' (case-insensitive)
	  is always placed at the right-most side for easier comparison.
	"""
	# Normalise any CO₂-like text to plain ASCII "CO2" so it renders everywhere
	unique = [str(v).replace("₂", "2") for v in labels.dropna().unique()]
	special = [v for v in unique if str(v).strip().lower() == "contains prediction"]
	others = sorted(v for v in unique if v not in special)
	return others + special


def plot_badge_hover_counts(
	badge_metrics: pd.DataFrame,
	out_dir: Path,
) -> Optional[Path]:
	"""
	Plot total hover counts per badge, facetted by stimulus, using Altair.

	Returns the figure path, or None if no data.
	"""
	if badge_metrics is None or "stimulusId" not in badge_metrics.columns:
		return []

	df = badge_metrics.copy()
	if "hoverCount" not in df.columns:
		return []

	# Keep only rows with non-null hover counts
	df = df[df["hoverCount"].notna()].copy()
	if df.empty:
		return []

	# Ensure numeric hover counts
	df["hoverCount"] = pd.to_numeric(df["hoverCount"], errors="coerce")
	df = df[df["hoverCount"].notna()].copy()
	if df.empty:
		return None

	# Display label per badge: prefer badgeLabel, fall back to badgeId
	df["badgeLabelDisplay"] = df.apply(
		lambda r: (
			str(r["badgeLabel"]).strip()
			if pd.notna(r.get("badgeLabel")) and str(r["badgeLabel"]).strip()
			else str(r.get("badgeId", "")).strip()
		),
		axis=1,
	)
	df = df[df["badgeLabelDisplay"] != ""].copy()
	if df.empty:
		return None

	# Pretty stimulus labels for facets
	df["stimulus_label"] = df["stimulusId"].map(_stimulus_label)

	# Aggregate in case of multiple rows per (stimulus, badge)
	agg = (
		df.groupby(["stimulus_label", "badgeLabelDisplay"], as_index=False)["hoverCount"]
		.sum()
	)
	if agg.empty:
		return None

	badge_order = _badge_sort_order(agg["badgeLabelDisplay"])

	# One PNG with two small-multiple charts (facets) sharing the same y-scale.
	base = (
		alt.Chart(agg)
		.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
		.encode(
			x=alt.X(
				"badgeLabelDisplay:N",
				sort=badge_order,
				axis=alt.Axis(title=None),
			),
			y=alt.Y("hoverCount:Q", title="Hover Count", scale=alt.Scale(domain=(0, 10))),
		).properties(width=100, height=100)
	)
	chart = (
		base.facet(column=alt.Column("stimulus_label:N", title=None))
		.resolve_scale(x="independent", y="shared")
		.configure_axis(labelFontSize=11, titleFontSize=12)
	)

	fig_name = "f_badge_hover_facets"
	path = figure_path(out_dir, fig_name)
	path.parent.mkdir(parents=True, exist_ok=True)
	# Use a higher scale factor so text renders crisply in the PNG
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)

	return path


def plot_badge_hover_times(
	badge_metrics: pd.DataFrame,
	out_dir: Path,
) -> Optional[Path]:
	"""
	Plot hover time per badge, facetted by stimulus, using Altair.

	Each facet shows one bar per badge for total hover time, with a vertical rule
	indicating min/max hover duration for that badge.
	"""
	if badge_metrics is None or "stimulusId" not in badge_metrics.columns:
		return None

	df = badge_metrics.copy()
	for col in ["totalHoverTime", "minHoverTime", "maxHoverTime"]:
		if col not in df.columns:
			return None

	# Keep only rows with at least some timing information
	df = df[
		df["totalHoverTime"].notna()
		| df["minHoverTime"].notna()
		| df["maxHoverTime"].notna()
	].copy()
	if df.empty:
		return None

	# Numeric conversion
	for col in ["totalHoverTime", "minHoverTime", "maxHoverTime"]:
		df[col] = pd.to_numeric(df[col], errors="coerce")
	df = df.dropna(subset=["totalHoverTime", "minHoverTime", "maxHoverTime"], how="all")
	if df.empty:
		return None

	# Display label per badge: prefer badgeLabel, fall back to badgeId
	df["badgeLabelDisplay"] = df.apply(
		lambda r: (
			str(r["badgeLabel"]).strip()
			if pd.notna(r.get("badgeLabel")) and str(r["badgeLabel"]).strip()
			else str(r.get("badgeId", "")).strip()
		),
		axis=1,
	)
	df = df[df["badgeLabelDisplay"] != ""].copy()
	if df.empty:
		return None

	# Pretty stimulus labels for facets
	df["stimulus_label"] = df["stimulusId"].map(_stimulus_label)

	# Aggregate in case of multiple rows per (stimulus, badge)
	agg = (
		df.groupby(["stimulus_label", "badgeLabelDisplay"], as_index=False)[
			["totalHoverTime", "minHoverTime", "maxHoverTime"]
		]
		.agg(
			{
				"totalHoverTime": "sum",
				"minHoverTime": "min",
				"maxHoverTime": "max",
			}
		)
	)
	if agg.empty:
		return None

	badge_order = _badge_sort_order(agg["badgeLabelDisplay"])

	# Base chart per badge: total hover time only
	base = alt.Chart(agg)

	bars = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
		x=alt.X(
			"badgeLabelDisplay:N",
			sort=badge_order,
			axis=alt.Axis(title=None),
		),
		y=alt.Y(
			"totalHoverTime:Q",
			title="Total hover time (s)",
		),
	).properties(width=100, height=100)

	chart = (
		bars.facet(column=alt.Column("stimulus_label:N", title=None))
		.resolve_scale(x="independent", y="shared")
		.configure_axis(labelFontSize=11, titleFontSize=12)
	)

	fig_name = "f_badge_hover_time_facets"
	path = figure_path(out_dir, fig_name)
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)

	return path


def plot_badge_hover_duration_stats(
	badge_metrics: pd.DataFrame,
	out_dir: Path,
) -> Optional[Path]:
	"""
	Plot mean hover duration per badge, facetted by stimulus.
	"""
	if badge_metrics is None or "stimulusId" not in badge_metrics.columns:
		return None

	df = badge_metrics.copy()
	for col in ["hoverCount", "totalHoverTime", "minHoverTime", "maxHoverTime"]:
		if col not in df.columns:
			return None

	# Keep rows with at least some timing and count information
	df = df[
		(df["hoverCount"].notna() & (df["hoverCount"] > 0))
		| df["totalHoverTime"].notna()
		| df["minHoverTime"].notna()
		| df["maxHoverTime"].notna()
	].copy()
	if df.empty:
		return None

	# Numeric conversion
	for col in ["hoverCount", "totalHoverTime", "minHoverTime", "maxHoverTime"]:
		df[col] = pd.to_numeric(df[col], errors="coerce")
	df = df.dropna(subset=["hoverCount", "totalHoverTime"], how="any")
	if df.empty:
		return None

	# Badge labels
	df["badgeLabelDisplay"] = df.apply(
		lambda r: (
			str(r["badgeLabel"]).strip()
			if pd.notna(r.get("badgeLabel")) and str(r["badgeLabel"]).strip()
			else str(r.get("badgeId", "")).strip()
		),
		axis=1,
	)
	df = df[df["badgeLabelDisplay"] != ""].copy()
	if df.empty:
		return None

	# Stimulus labels
	df["stimulus_label"] = df["stimulusId"].map(_stimulus_label)

	# Aggregate per (stimulus, badge)
	agg = (
		df.groupby(["stimulus_label", "badgeLabelDisplay"], as_index=False)[
			["hoverCount", "totalHoverTime", "minHoverTime", "maxHoverTime"]
		]
		.agg(
			{
				"hoverCount": "sum",
				"totalHoverTime": "sum",
				"minHoverTime": "min",
				"maxHoverTime": "max",
			}
		)
	)
	if agg.empty:
		return None

	# Mean hover time per badge (seconds)
	agg = agg[agg["hoverCount"] > 0].copy()
	if agg.empty:
		return None
	agg["meanHoverTime"] = agg["totalHoverTime"] / agg["hoverCount"]

	badge_order = _badge_sort_order(agg["badgeLabelDisplay"])

	base = alt.Chart(agg)

	bars = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
		x=alt.X(
			"badgeLabelDisplay:N",
			sort=badge_order,
			axis=alt.Axis(title=None),
		),
		y=alt.Y("meanHoverTime:Q", title="Mean hover time (s)"),
	).properties(width=100, height=100)

	chart = bars.facet(column=alt.Column("stimulus_label:N", title=None)).resolve_scale(
		x="independent", y="shared"
	).configure_axis(labelFontSize=11, titleFontSize=12)

	fig_name = "f_badge_hover_duration_stats_facets"
	path = figure_path(out_dir, fig_name)
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)

	return path



