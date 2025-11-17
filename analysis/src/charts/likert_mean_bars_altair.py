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
	Altair implementation of the grouped Likert mean bar chart.

	Two vertical bars per dimension (Footnotes vs Badges), shared y-scale [1, 5],
	value labels above bars, and only vertical grid lines (on the score axis).
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

	# Grouped bars: color/offset by group
	color_scale = alt.Scale(
		domain=["Footnotes", "Badges"],
		range=["#6C757D", "#2A7DE1"],
	)

	base = alt.Chart(stats)

	bars = (
		base.mark_bar()
		.encode(
			x=alt.X(
				"dimension_label:N",
				sort=label_order,
				axis=alt.Axis(title=None, labelAngle=20),
			),
			xOffset="group:N",
			y=alt.Y(
				"mean_score:Q",
				title="",
				scale=alt.Scale(domain=(0.8, 5.2)),
				axis=alt.Axis(
					values=[1, 2, 3, 4, 5],
					grid=False,
				),
			),
			color=alt.Color(
				"group:N",
				title=None,
				scale=color_scale,
				legend=alt.Legend(orient="right"),
			),
		)
	)

	# Value labels above bars
	labels = (
		base.mark_text(dy=-4, size=9)
		.encode(
			x=alt.X(
				"dimension_label:N",
				sort=label_order,
			),
			xOffset="group:N",
			y="mean_score:Q",
			text=alt.Text("mean_score:Q", format=".2f"),
			color=alt.value("black"),
		)
	)

	chart = (
		(bars + labels)
		.properties(
			width=max(320, 60 * len(label_order)),
			height=260,
		)
		.configure_axisX(grid=True)  # only vertical grid lines
		.configure_axisY(grid=False)
	)

	path = figure_path(out_dir, "f_likert_mean_bars_altair")
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)

	return path



