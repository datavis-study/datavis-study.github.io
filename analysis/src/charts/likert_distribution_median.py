from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, List

import altair as alt
import pandas as pd

from reporting.util import figure_path


def plot_likert_distribution_median(
	likert: pd.DataFrame,
	out_dir: Path,
) -> Optional[Path]:
	"""
	Likert distributions with median ticks, inspired by the Vega-Lite example:
	https://vega.github.io/vega-lite/examples/layer_likert.html

	We create separate facets per group (Footnotes vs Badges), mirroring the
	beehive plot: one chart per group, shared x-scale [1, 5].
	"""
	if likert is None:
		return None

	# Dimensions we know about
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

	# Long form: one row per (participant, dimension) rating
	id_vars = [c for c in ["participantId", "group"] if c in likert.columns]
	df = likert.melt(
		id_vars=id_vars,
		value_vars=metrics,
		var_name="dimension",
		value_name="score",
	).dropna(subset=["score"])
	if df.empty:
		return None

	# Numeric Likert scores, clipped to 1–5
	df["score"] = pd.to_numeric(df["score"], errors="coerce").clip(lower=1, upper=5)
	df = df.dropna(subset=["score"])
	if df.empty:
		return None

	# Human-friendly dimension labels and ordering (match other Likert charts)
	dimension_labels: Dict[str, str] = {
		"saliency": "Saliency",
		"clutter": "Clutter",
		"interpretability": "Interpretability",
		"usefulness": "Usefulness",
		"trust": "Trust",
		"standardization": "Standardization",
	}
	df["dimension_label"] = df["dimension"].map(dimension_labels)
	label_order: List[str] = [dimension_labels[m] for m in metrics if m in dimension_labels]
	df = df[df["dimension_label"].notna()].copy()
	if df.empty:
		return None
	df["dimension_label"] = pd.Categorical(df["dimension_label"], categories=label_order, ordered=True)

	# Group labels: mirror beehive plot (Footnotes vs Badges)
	if "group" in df.columns:
		title_map = {"footnote": "Footnotes", "badge": "Badges"}
		df["group_label"] = df["group"].map(lambda g: title_map.get(str(g).lower(), str(g).title()))
	else:
		df["group_label"] = "All"

	# Dataset "values": individual ratings
	values = df.rename(columns={"dimension_label": "name", "score": "value"})[
		["group_label", "name", "value"]
	].copy()

	# Base encodings for x/y
	x_enc = alt.X(
		"value:Q",
		scale=alt.Scale(domain=(1, 5)),
		axis=alt.Axis(
			grid=False,
			values=[1, 2, 3, 4, 5],
			format="d",  # show 1,2,3,4,5 (no decimals)
			title=None,
			offset=10,
			labelPadding=8,
			labelFontSize=12,
			tickSize=4,
		),
	)
	y_enc = alt.Y(
		"name:N",
		sort=label_order,
		axis=alt.Axis(
			domain=False,
			offset=20,  # reduce gap between labels and chart
			labelFontWeight="bold",
			ticks=False,
			grid=True,
			title=None,
		),
	)

	# Slightly increase cell size to create more horizontal spacing between x ticks
	base = alt.Chart(values).properties(width=360, height=220)

	# Circle layer: distributions, size by count
	circles = (
		base.mark_circle(color="#6EB4FD")
		.encode(
			x=x_enc,
			y=y_enc,
			size=alt.Size(
				"count():Q",
				title="Number of ratings",
				legend=alt.Legend(orient="right"),
			),
		)
	)

	# Subtle median tick layer (median of value per (group_label, name))
	median_tick = (
		base.mark_tick(color="#444444", size=6, thickness=1)
		.encode(
			x=alt.X(
				"median(value):Q",
				scale=alt.Scale(domain=(1, 5)),
			),
			y=alt.Y("name:N", sort=label_order),
		)
	)

	chart = (
		alt.layer(circles, median_tick)
		.facet(
			column=alt.Column(
				"group_label:N",
				header=alt.Header(title=None, labelExpr="'Group: ' + datum.label"),
			)
		)
		.resolve_scale(x="shared", y="shared")
		.configure_view(stroke=None)
	)

	path = figure_path(out_dir, "f_likert_distribution_median")
	path.parent.mkdir(parents=True, exist_ok=True)
	chart.save(str(path), engine="vl-convert", format="png", scale_factor=3)

	return path



