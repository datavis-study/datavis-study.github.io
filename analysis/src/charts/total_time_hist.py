import pathlib
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from reporting.util import figure_path, save_current_fig


def plot_total_time_hist(time_df: pd.DataFrame, out_dir: pathlib.Path, col: str = "total (s)") -> Optional[pathlib.Path]:
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
	path = figure_path(out_dir, "f_total_time_hist")
	save_current_fig(path)
	return path


