from __future__ import annotations

from pathlib import Path
from typing import List, Optional

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


def plot_badge_click_counts(badge_metrics: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	if badge_metrics is None or "stimulusId" not in badge_metrics.columns:
		return None
	df = badge_metrics.copy()
	if "clickCount" not in df.columns:
		return None
	# Treat missing as zeros to allow empty/zero charts to render
	df["clickCount"] = pd.to_numeric(df["clickCount"], errors="coerce").fillna(0)
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
	df["stimulus_label"] = df["stimulusId"].map(_stimulus_label)
	agg = (
		df.groupby(["stimulus_label", "badgeLabelDisplay"], as_index=False)["clickCount"]
		.sum()
	)
	if agg.empty:
		return None
	badge_order = _badge_sort_order(agg["badgeLabelDisplay"])
	base = (
		alt.Chart(agg)
		.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
		.encode(
			x=alt.X("badgeLabelDisplay:N", sort=badge_order, axis=alt.Axis(title=None)),
			y=alt.Y("clickCount:Q", title="Click Count", scale=alt.Scale(domain=(0, 10))),
		).properties(width=100, height=100)
	)
	chart = (
		base.facet(column=alt.Column("stimulus_label:N", title=None))
		.resolve_scale(x="independent", y="shared")
		.configure_axis(labelFontSize=11, titleFontSize=12)
	)
	fig_name = "f_badge_click_facets"
	path = figure_path(out_dir, fig_name)
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)
	return path


