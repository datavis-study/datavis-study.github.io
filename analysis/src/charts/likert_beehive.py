import pathlib
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from reporting.util import figure_path


def plot_likert_beehive(likert: pd.DataFrame, out_dir: pathlib.Path) -> Optional[pathlib.Path]:
	if likert is None or "group" not in likert.columns:
		return None
	metrics = [c for c in ["saliency", "clutter", "interpretability", "usefulness", "trust", "standardization"] if c in likert.columns]
	if not metrics:
		return None
	df = likert.melt(id_vars=[c for c in ["group", "participantId"] if c in likert.columns], value_vars=metrics, var_name="dimension", value_name="score").dropna()
	if df.empty:
		return None
	# Ensure score is numeric and bounded
	df["score"] = pd.to_numeric(df["score"], errors="coerce").clip(lower=1, upper=5)
	df = df.dropna(subset=["score"])
	# One plot per group; each plot contains all dimensions on x-axis and scores on y-axis
	dimension_order = metrics
	df["dimension"] = pd.Categorical(df["dimension"], categories=dimension_order, ordered=True)
	score_order = ["1", "2", "3", "4", "5"]
	df["score_cat"] = pd.Categorical(df["score"].astype(int).astype(str), categories=score_order, ordered=True)
	# Friendlier group titles
	title_map = {"footnote": "Footnotes", "badge": "Badges"}
	if "group" in df.columns:
		df["group"] = df["group"].map(lambda g: title_map.get(str(g).lower(), str(g).title()))
	g = sns.FacetGrid(df, col="group", height=3.2, sharey=True, sharex=True, margin_titles=True, col_order=[title_map.get("footnote", "Footnotes"), title_map.get("badge", "Badges")])
	palette = {"Footnotes": "#6C757D", "Badges": "#2A7DE1"}
	def _swarm_with_group_color(data: pd.DataFrame, **kwargs):
		col = palette.get(str(data["group"].iloc[0]), "#2A7DE1")
		return sns.swarmplot(
			data=data,
			x="score_cat",
			y="dimension",
			order=score_order,
			size=4.2,
			color=col,
			alpha=0.85,
			edgecolor="white",
			linewidth=0.3,
		)
	g.map_dataframe(_swarm_with_group_color)
	for ax in g.axes.flatten():
		ax.set_xlabel("Likert score")
		ax.set_ylabel("Dimension")
		ax.set_xticks(range(5))
		ax.set_xticklabels(["1", "2", "3", "4", "5"])
		ax.grid(True, axis="x", alpha=0.2)
	g.set_titles(col_template="{col_name}")
	g.figure.suptitle("Likert responses by group and dimension (1 = low, 5 = high)", y=1.02, fontsize=12)
	path = figure_path(out_dir, "f_likert_beehive")
	g.figure.tight_layout()
	g.figure.savefig(path, dpi=160, bbox_inches="tight")
	plt.close(g.figure)
	return path

from typing import Optional
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def _figure_path(out_dir: Path, name: str) -> Path:
	return out_dir / "figures" / f"{name}.png"


def plot_likert_beehive(likert: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	if likert is None or "group" not in likert.columns:
		return None
	metrics = [c for c in ["saliency", "clutter", "interpretability", "usefulness", "trust", "standardization"] if c in likert.columns]
	if not metrics:
		return None
	df = likert.melt(id_vars=[c for c in ["group", "participantId"] if c in likert.columns], value_vars=metrics, var_name="dimension", value_name="score").dropna()
	if df.empty:
		return None
	# Ensure score is numeric and bounded
	df["score"] = pd.to_numeric(df["score"], errors="coerce").clip(lower=1, upper=5)
	df = df.dropna(subset=["score"])
	# One plot per group; each plot contains all dimensions on x-axis and scores on y-axis
	dimension_order = metrics
	df["dimension"] = pd.Categorical(df["dimension"], categories=dimension_order, ordered=True)
	score_order = ["1", "2", "3", "4", "5"]
	df["score_cat"] = pd.Categorical(df["score"].astype(int).astype(str), categories=score_order, ordered=True)
	# Friendlier group titles
	title_map = {"footnote": "Footnotes", "badge": "Badges"}
	if "group" in df.columns:
		df["group"] = df["group"].map(lambda g: title_map.get(str(g).lower(), str(g).title()))
	g = sns.FacetGrid(df, col="group", height=3.2, sharey=True, sharex=True, margin_titles=True, col_order=[title_map.get("footnote", "Footnotes"), title_map.get("badge", "Badges")])
	palette = {"Footnotes": "#6C757D", "Badges": "#2A7DE1"}
	def _swarm_with_group_color(data: pd.DataFrame, **kwargs):
		col = palette.get(str(data["group"].iloc[0]), "#2A7DE1")
		return sns.swarmplot(
			data=data,
			x="score_cat",
			y="dimension",
			order=score_order,
			size=4.2,
			color=col,
			alpha=0.85,
			edgecolor="white",
			linewidth=0.3,
		)
	g.map_dataframe(_swarm_with_group_color)
	for ax in g.axes.flatten():
		ax.set_xlabel("Likert score")
		ax.set_ylabel("Dimension")
		ax.set_xticks(range(5))
		ax.set_xticklabels(["1", "2", "3", "4", "5"])
		ax.grid(True, axis="x", alpha=0.2)
	g.set_titles(col_template="{col_name}")
	g.figure.suptitle("Likert responses by group and dimension (1 = low, 5 = high)", y=1.02, fontsize=12)
	path = _figure_path(out_dir, "f_likert_beehive")
	g.figure.tight_layout()
	g.figure.savefig(path, dpi=160, bbox_inches="tight")
	plt.close(g.figure)
	return path



