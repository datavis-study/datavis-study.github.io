from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict

import altair as alt
import pandas as pd

from reporting.util import figure_path


def plot_likert_mean_bars_altair(
	likert: pd.DataFrame,
	out_dir: Path,
) -> Optional[Path]:
	"""
	Altair implementation of the Likert mean bar chart.

	Refactored to small multiples in a single row:
	one facet per dimension with two bars (Footnotes vs Badges),
	shared y-scale [1, 5], and value labels above bars.
	"""
	if likert is None or "group" not in likert.columns:
		return None

	metrics: List[str] = [
		c
		for c in [
			"saliency",
			"clutter",
			"interpretability",
			"usefulness",
			"trust",
			"standardization",
		]
		if c in likert.columns
	]
	if not metrics:
		return None

	# Long form
	df = likert.melt(
		id_vars=[c for c in ["group", "participantId"] if c in likert.columns],
		value_vars=metrics,
		var_name="dimension",
		value_name="score",
	).dropna(subset=["score"])
	if df.empty:
		return None

	# Numeric scores 1–5
	df["score"] = (
		pd.to_numeric(df["score"], errors="coerce")
		.clip(lower=1, upper=5)
	)
	df = df.dropna(subset=["score"])
	if df.empty:
		return None

	# Labels and ordering (match existing matplotlib chart)
	title_map = {"footnote": "Footnotes", "badge": "Badges"}
	df["group"] = df["group"].map(
		lambda g: title_map.get(str(g).lower(), str(g).title())
	)

	dimension_order: List[str] = metrics
	dimension_labels: Dict[str, str] = {
		"saliency": "Saliency",
		"clutter": "Clutter",
		"interpretability": "Interpretability",
		"usefulness": "Usefulness",
		"trust": "Trust",
		"standardization": "Standardization",
	}
	df["dimension_label"] = df["dimension"].map(dimension_labels)
	label_order: List[str] = [
		dimension_labels[m] for m in dimension_order if m in dimension_labels
	]
	df = df[df["dimension_label"].notna()].copy()
	if df.empty:
		return None
	df["dimension_label"] = pd.Categorical(
		df["dimension_label"],
		categories=label_order,
		ordered=True,
	)

	# Aggregate means
	stats = (
		df.groupby(["group", "dimension_label"], observed=True)["score"]
		.mean()
		.reset_index(name="mean_score")
	)
	if stats.empty:
		return None

	groups = [
		g for g in ["Footnotes", "Badges"]
		if g in set(stats["group"].dropna().unique())
	]
	if not groups:
		return None

	# Small-multiple bars per dimension: color by group
	color_scale = alt.Scale(
		domain=["Footnotes", "Badges"],
		range=["#6C757D", "#2A7DE1"],
	)

	# Keep width 100; set height to 100
	base = alt.Chart(stats).properties(width=100, height=100)

	# Horizontal bars; thicker with subtle rounding; numeric axis on x (0–5)
	bars = base.mark_bar(size=14, cornerRadiusTopRight=1, cornerRadiusBottomRight=1).encode(
		x=alt.X(
			"mean_score:Q",
			title="",
			scale=alt.Scale(domain=(0, 5)),
			axis=alt.Axis(values=[0, 1, 2, 3, 4, 5], grid=True, gridColor="#DDDDDD"),
		),
		y=alt.Y(
			"group:N",
			sort=["Footnotes", "Badges"],
			axis=alt.Axis(title=None),
			scale=alt.Scale(paddingInner=0.0, paddingOuter=0.0),
		),
		color=alt.Color(
			"group:N",
			title=None,
			scale=color_scale,
			legend=alt.Legend(orient="right"),
		),
	)

	# Value labels at the end of each bar
	labels = base.mark_text(dx=4, size=7, align="left", baseline="middle").encode(
		x="mean_score:Q",
		y=alt.Y("group:N", sort=["Footnotes", "Badges"]),
		text=alt.Text("mean_score:Q", format=".2f"),
		color=alt.value("black"),
	)

	# Facet into a single row: one facet per dimension
	chart = (bars + labels).facet(
		column=alt.Column("dimension_label:N", sort=label_order, header=alt.Header(title=None))
	).resolve_scale(x="shared", y="shared").configure_axisX(grid=True).configure_axisY(grid=False)

	path = figure_path(out_dir, "f_likert_mean_bars_altair")
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)

	return path



