from __future__ import annotations

from pathlib import Path
from typing import Optional, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def _figure_path(out_dir: Path, name: str) -> Path:
	return out_dir / "figures" / f"{name}.png"


def plot_likert_diverging_bars(likert: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	"""
	Create diverging 100% stacked bars per dimension, faceted by group.
	Left side shows share of 1–2, right side shows share of 4–5, and 3 is centered (split half-left/half-right).
	"""
	if likert is None or "group" not in likert.columns:
		return None
	metrics: List[str] = [c for c in ["saliency", "clutter", "interpretability", "usefulness", "trust", "standardization"] if c in likert.columns]
	if not metrics:
		return None
	df = likert.melt(
		id_vars=[c for c in ["group", "participantId"] if c in likert.columns],
		value_vars=metrics,
		var_name="dimension",
		value_name="score",
	).dropna()
	if df.empty:
		return None
	# Ensure numeric
	df["score"] = pd.to_numeric(df["score"], errors="coerce").astype("Int64")
	df = df.dropna(subset=["score"])
	df["score"] = df["score"].astype(int)
	# Friendly group names
	title_map = {"footnote": "Footnotes", "badge": "Badges"}
	df["group"] = df["group"].map(lambda g: title_map.get(str(g).lower(), str(g).title()))
	# Order categories for consistent display
	dimension_order = metrics
	df["dimension"] = pd.Categorical(df["dimension"], categories=dimension_order, ordered=True)
	dimension_labels = {
		"saliency": "Saliency",
		"clutter": "Clutter",
		"interpretability": "Interpretability",
		"usefulness": "Usefulness",
		"trust": "Trust",
		"standardization": "Standardization",
	}
	df["dimension_label"] = df["dimension"].map(dimension_labels)
	label_order = [dimension_labels[m] for m in dimension_order if m in dimension_labels]
	df["dimension_label"] = pd.Categorical(df["dimension_label"], categories=label_order, ordered=True)
	# Compute percent distribution per group x dimension x score
	counts = (
		df.groupby(["group", "dimension_label", "score"], dropna=False)["participantId"]
		.count()
		.reset_index(name="n")
	)
	totals = counts.groupby(["group", "dimension_label"], as_index=False)["n"].sum().rename(columns={"n": "total"})
	counts = counts.merge(totals, on=["group", "dimension_label"], how="left")
	counts["pct"] = counts["n"] / counts["total"] * 100.0
	# Ensure missing scores have zero percent
	all_scores = pd.Index([1, 2, 3, 4, 5], name="score")
	counts = (
		counts.set_index(["group", "dimension_label", "score"])
		.reindex(pd.MultiIndex.from_product([counts["group"].unique(), counts["dimension_label"].cat.categories, all_scores]))
		.reset_index()
		.rename(columns={"level_0": "group", "level_1": "dimension_label", "level_2": "score"})
	)
	counts["pct"] = counts["pct"].fillna(0.0)
	# Colors by score
	score_colors = {
		1: "#d73027",  # strong negative
		2: "#fc8d59",
		3: "#bdbdbd",  # neutral
		4: "#91bfdb",
		5: "#4575b4",  # strong positive
	}
	# Build facets per group
	groups = list(counts["group"].dropna().unique())
	if not groups:
		return None
	ncols = len(groups)
	height = max(3.0, 0.45 * len(label_order) + 1.0)
	fig, axes = plt.subplots(nrows=1, ncols=ncols, figsize=(6.0 + 2.0 * (ncols - 1), height), sharex=True, sharey=True)
	if ncols == 1:
		axes = [axes]
	for ax, grp in zip(axes, groups):
		sub = counts[counts["group"] == grp].copy()
		# Pivot to arrays per score preserving label order
		pivot = sub.pivot_table(index="dimension_label", columns="score", values="pct", fill_value=0.0).reindex(label_order)
		p1 = pivot.get(1, pd.Series(0.0, index=label_order)).values
		p2 = pivot.get(2, pd.Series(0.0, index=label_order)).values
		p3 = pivot.get(3, pd.Series(0.0, index=label_order)).values
		p4 = pivot.get(4, pd.Series(0.0, index=label_order)).values
		p5 = pivot.get(5, pd.Series(0.0, index=label_order)).values
		y = np.arange(len(label_order))
		# Negative stack (left): 1 and 2 plus half of 3
		left_neg = np.zeros_like(y, dtype=float)
		ax.barh(y, -p1, left=left_neg, color=score_colors[1], edgecolor="white", linewidth=0.2)
		left_neg = left_neg - p1
		ax.barh(y, -p2, left=left_neg, color=score_colors[2], edgecolor="white", linewidth=0.2)
		left_neg = left_neg - p2
		ax.barh(y, -(p3 / 2.0), left=left_neg, color=score_colors[3], edgecolor="white", linewidth=0.2)
		# Positive stack (right): half of 3 plus 4 and 5
		left_pos = np.zeros_like(y, dtype=float)
		ax.barh(y, (p3 / 2.0), left=left_pos, color=score_colors[3], edgecolor="white", linewidth=0.2)
		left_pos = left_pos + (p3 / 2.0)
		ax.barh(y, p4, left=left_pos, color=score_colors[4], edgecolor="white", linewidth=0.2)
		left_pos = left_pos + p4
		ax.barh(y, p5, left=left_pos, color=score_colors[5], edgecolor="white", linewidth=0.2)
		# Aesthetics
		ax.axvline(0, color="#999999", linewidth=0.6, alpha=0.6)
		ax.set_title(f"Group: {grp}")
		ax.set_yticks(y)
		ax.set_yticklabels(label_order)
		ax.set_xlabel("")
		ax.grid(True, axis="x", alpha=0.2)
		ax.grid(False, axis="y")
		ax.set_xlim(-100, 100)
		# Put first dimension at the top
		ax.invert_yaxis()
	plt.tight_layout()
	path = _figure_path(out_dir, "f_likert_diverging")
	plt.savefig(path, dpi=160, bbox_inches="tight")
	plt.close(fig)
	return path


