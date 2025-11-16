import pathlib
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from reporting.util import figure_path, save_current_fig


def plot_group_counts(participants: pd.DataFrame, out_dir: pathlib.Path) -> Optional[pathlib.Path]:
	if participants is None or "group" not in participants.columns:
		return None
	fig_name = "f1_group_counts"
	plt.figure(figsize=(5, 3))
	ax = sns.countplot(data=participants, x="group", order=sorted(participants["group"].dropna().unique()))
	ax.set_title("Participants by group")
	ax.set_xlabel("Group")
	ax.set_ylabel("Count")
	path = figure_path(out_dir, fig_name)
	save_current_fig(path)
	return path

from typing import Optional
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


def plot_group_counts(participants: pd.DataFrame, out_dir: Path) -> Optional[Path]:
	if participants is None or "group" not in participants.columns:
		return None
	fig_name = "f1_group_counts"
	plt.figure(figsize=(5, 3))
	ax = sns.countplot(data=participants, x="group", order=sorted(participants["group"].dropna().unique()))
	ax.set_title("Participants by group")
	ax.set_xlabel("Group")
	ax.set_ylabel("Count")
	path = _figure_path(out_dir, fig_name)
	_save_current_fig(path)
	return path



