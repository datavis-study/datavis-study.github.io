from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _figure_path(out_dir: Path, name: str) -> Path:
	return out_dir / "figures" / f"{name}.png"


def plot_likert_dot_ci(likert: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	"""
	Compact Likert summary: mean per dimension (no CI), split by group.
	X-axis: score (1–5). Y: dimensions (top-to-bottom).
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
	df["score"] = pd.to_numeric(df["score"], errors="coerce").astype("Int64")
	df = df.dropna(subset=["score"])
	df["score"] = df["score"].astype(int)
	title_map = {"footnote": "Footnotes", "badge": "Badges"}
	df["group"] = df["group"].map(lambda g: title_map.get(str(g).lower(), str(g).title()))
	dimension_order = metrics
	dimension_labels: Dict[str, str] = {
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
	# Compute mean per group x dimension
	stats = (
		df.groupby(["group", "dimension_label"])["score"]
		.agg(["mean"])
		.reset_index()
		.rename(columns={"mean": "mean_score"})
	)
	# Plot
	groups = list(stats["group"].dropna().unique())
	if not groups:
		return None
	palette = {"Footnotes": "#6C757D", "Badges": "#2A7DE1"}
	offset_map = {groups[0]: -0.15, groups[-1]: 0.15} if len(groups) > 1 else {groups[0]: 0.0}
	height = max(3.0, 0.45 * len(label_order) + 1.0)
	fig, ax = plt.subplots(figsize=(6.5, height))
	ypos = np.arange(len(label_order))
	for grp in groups:
		sub = stats[stats["group"] == grp].set_index("dimension_label").reindex(label_order)
		x = sub["mean_score"].values
		y = ypos + offset_map.get(grp, 0.0)
		ax.plot(x, y, "o", color=palette.get(grp, "#2A7DE1"), markersize=5.0, alpha=0.95, zorder=3, label=grp)
	# Axes styling
	ax.set_yticks(ypos)
	ax.set_yticklabels(label_order)
	ax.invert_yaxis()  # first dimension at top
	ax.set_xlim(0.8, 5.2)
	ax.set_xticks([1, 2, 3, 4, 5])
	ax.set_xlabel("")  # keep minimal
	ax.grid(True, axis="x", alpha=0.2)
	ax.grid(False, axis="y")
	# Place legend on right
	if len(groups) > 1:
		ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
		fig = ax.get_figure()
		fig.subplots_adjust(right=0.82)
	plt.tight_layout()
	path = _figure_path(out_dir, "f_likert_dot_ci")
	plt.savefig(path, dpi=160, bbox_inches="tight")
	plt.close(fig)
	return path


