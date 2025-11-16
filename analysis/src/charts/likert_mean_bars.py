from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _figure_path(out_dir: Path, name: str) -> Path:
	return out_dir / "figures" / f"{name}.png"


def plot_likert_mean_bars(likert: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	"""
	Simple grouped mean bar chart of Likert per dimension in a single figure.
	Vertical bars; two bars per dimension (Footnotes vs Badges). Only vertical grid lines. No legend.
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
	# Numeric scores
	df["score"] = pd.to_numeric(df["score"], errors="coerce").astype("Int64")
	df = df.dropna(subset=["score"])
	df["score"] = df["score"].astype(int)
	# Labels and ordering
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
	# Aggregates
	stats = (
		df.groupby(["group", "dimension_label"])["score"]
		.mean()
		.reset_index(name="mean_score")
	)
	groups = [g for g in ["Footnotes", "Badges"] if g in set(stats["group"].dropna().unique())]
	if not groups:
		return None
	colors = {"Footnotes": "#6C757D", "Badges": "#2A7DE1"}
	# Build single figure with grouped vertical bars
	width = 0.28
	x = np.arange(len(label_order))
	height = 3.6
	fig, ax = plt.subplots(figsize=(max(6.5, 0.9 * len(label_order) + 4.0), height))
	for i, grp in enumerate(groups):
		sub = stats[stats["group"] == grp].set_index("dimension_label").reindex(label_order)
		vals = sub["mean_score"].values
		offset = (i - (len(groups) - 1) / 2) * width
		ax.bar(x + offset, vals, width=width, color=colors.get(grp, "#2A7DE1"), edgecolor="white", linewidth=0.2, label=grp)
		# Value labels above bars
		for xi, v in zip(x + offset, vals):
			if pd.notna(v):
				ax.text(xi, v + 0.05, f"{v:.2f}", va="bottom", ha="center", fontsize=8)
	ax.set_ylabel("")
	ax.set_xlim(-0.5, len(label_order) - 0.5)
	ax.set_ylim(0.8, 5.2)
	ax.set_yticks([1, 2, 3, 4, 5])
	ax.set_xticks(x)
	ax.set_xticklabels(label_order, rotation=20, ha="right")
	# Only vertical grid lines
	ax.grid(True, axis="x", alpha=0.2)
	ax.grid(False, axis="y")
	# Legend on the right
	if len(groups) > 1:
		ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, title="")
		fig.subplots_adjust(right=0.82)
	plt.tight_layout()
	path = _figure_path(out_dir, "f_likert_mean_bars")
	plt.savefig(path, dpi=160, bbox_inches="tight")
	plt.close(fig)
	return path


