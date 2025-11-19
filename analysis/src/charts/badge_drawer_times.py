from __future__ import annotations

from pathlib import Path
from typing import Optional

import altair as alt
import pandas as pd

from reporting.util import figure_path


def _stimulus_label(stimulus_id: str) -> str:
	label_map = {
		"global-warming-projection": "Global Warming Projection",
		"co2-emissions": "CO₂ Emissions",
	}
	return label_map.get(str(stimulus_id), str(stimulus_id))


def _badge_sort_order(labels: pd.Series) -> list[str]:
	unique = [str(v) for v in labels.dropna().unique()]
	special = [v for v in unique if str(v).strip().lower() == "contains prediction"]
	others = sorted(v for v in unique if v not in special)
	return others + special


def _with_display_labels(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	df["badgeLabelDisplay"] = df.apply(
		lambda r: (
			str(r["badgeLabel"]).strip()
			if pd.notna(r.get("badgeLabel")) and str(r["badgeLabel"]).strip()
			else str(r.get("badgeId", "")).strip()
		),
		axis=1,
	)
	df = df[df["badgeLabelDisplay"] != ""].copy()
	df["stimulus_label"] = df["stimulusId"].map(_stimulus_label)
	return df


def plot_badge_drawer_open_counts(badge_metrics: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	if badge_metrics is None or "stimulusId" not in badge_metrics.columns:
		return None
	df = badge_metrics.copy()
	if "drawerOpenCount" not in df.columns:
		return None
	# Treat missing as zeros
	df["drawerOpenCount"] = pd.to_numeric(df["drawerOpenCount"], errors="coerce").fillna(0)
	df = _with_display_labels(df)
	if df.empty:
		return None
	agg = (
		df.groupby(["stimulus_label", "badgeLabelDisplay"], as_index=False)["drawerOpenCount"]
		.sum()
	)
	if agg.empty:
		return None
	badge_order = _badge_sort_order(agg["badgeLabelDisplay"])
	chart = (
		alt.Chart(agg)
		.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
		.encode(
			x=alt.X("badgeLabelDisplay:N", sort=badge_order, axis=alt.Axis(title=None)),
			y=alt.Y("drawerOpenCount:Q", title="Drawer open count", scale=alt.Scale(domain=(0, 10))),
		).properties(width=100, height=100)
		.facet(column=alt.Column("stimulus_label:N", title=None))
		.resolve_scale(x="independent", y="shared")
		.configure_axis(labelFontSize=11, titleFontSize=12)
	)
	path = figure_path(out_dir, "f_badge_drawer_open_facets")
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)
	return path


def plot_badge_drawer_open_times(badge_metrics: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	if badge_metrics is None or "stimulusId" not in badge_metrics.columns:
		return None
	df = badge_metrics.copy()
	if "totalDrawerOpenTime" not in df.columns:
		return None
	# Treat missing as zeros
	df["totalDrawerOpenTime"] = pd.to_numeric(df["totalDrawerOpenTime"], errors="coerce").fillna(0)
	df = _with_display_labels(df)
	if df.empty:
		return None
	agg = (
		df.groupby(["stimulus_label", "badgeLabelDisplay"], as_index=False)["totalDrawerOpenTime"]
		.sum()
	)
	if agg.empty:
		return None
	badge_order = _badge_sort_order(agg["badgeLabelDisplay"])
	chart = (
		alt.Chart(agg)
		.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
		.encode(
			x=alt.X("badgeLabelDisplay:N", sort=badge_order, axis=alt.Axis(title=None)),
			y=alt.Y("totalDrawerOpenTime:Q", title="Total drawer open time (s)"),
		).properties(width=100, height=100)
		.facet(column=alt.Column("stimulus_label:N", title=None))
		.resolve_scale(x="independent", y="shared")
		.configure_axis(labelFontSize=11, titleFontSize=12)
	)
	path = figure_path(out_dir, "f_badge_drawer_time_facets")
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)
	return path


def plot_badge_drawer_duration_stats(badge_metrics: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	if badge_metrics is None or "stimulusId" not in badge_metrics.columns:
		return None
	df = badge_metrics.copy()
	for col in ["drawerOpenCount", "totalDrawerOpenTime"]:
		if col not in df.columns:
			return None
	# Treat missing as zeros to compute mean as 0 when no opens
	df["drawerOpenCount"] = pd.to_numeric(df["drawerOpenCount"], errors="coerce").fillna(0)
	df["totalDrawerOpenTime"] = pd.to_numeric(df["totalDrawerOpenTime"], errors="coerce").fillna(0)
	df = _with_display_labels(df)
	if df.empty:
		return None
	agg = (
		df.groupby(["stimulus_label", "badgeLabelDisplay"], as_index=False)[
			["drawerOpenCount", "totalDrawerOpenTime"]
		].sum()
	)
	if agg.empty:
		return None
	# Compute mean; avoid division by zero by using where + fillna(0)
	agg["meanDrawerOpenTime"] = (agg["totalDrawerOpenTime"] / agg["drawerOpenCount"].where(agg["drawerOpenCount"] != 0)).fillna(0)
	badge_order = _badge_sort_order(agg["badgeLabelDisplay"])
	chart = (
		alt.Chart(agg)
		.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
		.encode(
			x=alt.X("badgeLabelDisplay:N", sort=badge_order, axis=alt.Axis(title=None)),
			y=alt.Y("meanDrawerOpenTime:Q", title="Mean drawer open time (s)"),
		).properties(width=100, height=100)
		.facet(column=alt.Column("stimulus_label:N", title=None))
		.resolve_scale(x="independent", y="shared")
		.configure_axis(labelFontSize=11, titleFontSize=12)
	)
	path = figure_path(out_dir, "f_badge_drawer_duration_stats_facets")
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)
	return path


