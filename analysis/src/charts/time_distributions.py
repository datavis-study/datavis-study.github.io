import pathlib
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from reporting.util import figure_path, save_current_fig


def plot_time_distributions(time_df: pd.DataFrame, out_dir: pathlib.Path, component_cols: List[str]) -> List[pathlib.Path]:
	paths: List[pathlib.Path] = []
	if time_df is None or "group" not in time_df.columns:
		return paths
	for col in component_cols:
		if col not in time_df.columns:
			continue
		df = time_df.loc[time_df[col].notna() & (time_df[col] > 0)].copy()
		if df.empty:
			continue
		fig_name = f"time_{col.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')}"
		plt.figure(figsize=(6, 3.5))
		ax = sns.violinplot(data=df, x="group", y=col, inner=None, cut=0)
		sns.boxplot(data=df, x="group", y=col, showcaps=True, boxprops={"facecolor": "white", "alpha": 0.6}, showfliers=False, width=0.25)
		ax.set_title(f"Time spent: {col}")
		ax.set_xlabel("Group")
		ax.set_ylabel("Seconds (log scale)")
		ax.set_yscale("log")
		path = figure_path(out_dir, fig_name)
		save_current_fig(path)
		paths.append(path)
	return paths

from typing import List, Optional
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def _figure_path(out_dir: Path, name: str) -> Path:
	return out_dir / "figures" / f"{name}.png"


def _save_current_fig(path: Path, dpi: int = 160) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	plt.tight_layout()
	plt.savefig(path, dpi=dpi, bbox_inches="tight")
	plt.close()


def plot_time_distributions(time_df: pd.DataFrame, out_dir: Path, component_cols: List[str]) -> List[Path]:
	paths: List[Path] = []
	if time_df is None or "group" not in time_df.columns:
		return paths
	for col in component_cols:
		if col not in time_df.columns:
			continue
		df = time_df.loc[time_df[col].notna() & (time_df[col] > 0)].copy()
		if df.empty:
			continue
		fig_name = f"time_{col.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')}"
		plt.figure(figsize=(6, 3.5))
		ax = sns.violinplot(data=df, x="group", y=col, inner=None, cut=0)
		sns.boxplot(data=df, x="group", y=col, showcaps=True, boxprops={"facecolor": "white", "alpha": 0.6}, showfliers=False, width=0.25)
		ax.set_title(f"Time spent: {col}")
		ax.set_xlabel("Group")
		ax.set_ylabel("Seconds (log scale)")
		ax.set_yscale("log")
		path = _figure_path(out_dir, fig_name)
		_save_current_fig(path)
		paths.append(path)
	return paths


def plot_total_time_hist(time_df: pd.DataFrame, out_dir: Path, col: str = "total (s)") -> Optional[Path]:
	if time_df is None or "group" not in time_df.columns or col not in time_df.columns:
		return None
	df = time_df.loc[time_df[col].notna() & (time_df[col] > 0)].copy()
	if df.empty:
		return None
	upper = df[col].quantile(0.95)
	df = df.loc[df[col] <= upper].copy()
	plt.figure(figsize=(6, 3.5))
	ax = sns.histplot(data=df, x=col, hue="group", bins=20, element="step", stat="density", common_norm=False, alpha=0.5)
	sns.kdeplot(data=df, x=col, hue="group", common_norm=False, legend=False)
	ax.set_title("Total session time (trimmed at 95th percentile)")
	ax.set_xlabel("Seconds")
	ax.set_ylabel("Density")
	path = _figure_path(out_dir, "f_total_time_hist")
	_save_current_fig(path)
	return path



