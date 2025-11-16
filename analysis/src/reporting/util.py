import os
import pathlib
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class LoadedData:
	participants: Optional[pd.DataFrame]
	time_per_component: Optional[pd.DataFrame]
	likert_scores: Optional[pd.DataFrame]
	open_responses: Optional[pd.DataFrame]
	badge_metrics: Optional[pd.DataFrame]
	notes: Optional[pd.DataFrame]


def _read_csv_safe(path: str | os.PathLike, dtype: Optional[Dict[str, str]] = None) -> Optional[pd.DataFrame]:
	try:
		return pd.read_csv(path, dtype=dtype)
	except FileNotFoundError:
		return None


def _normalize_group_label(label: str) -> str:
	if pd.isna(label):
		return label
	lbl = str(label).strip().lower()
	if lbl.endswith("-group"):
		lbl = lbl.replace("-group", "")
	return lbl


def normalize_groups(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
	df = df.copy()
	df[group_col] = df[group_col].map(_normalize_group_label)
	return df


def load_all_data(data_dir: str | os.PathLike) -> LoadedData:
	data_dir = pathlib.Path(data_dir)
	participants = _read_csv_safe(data_dir / "participants.csv")
	if participants is not None and "participantGroup" in participants.columns:
		participants = participants.rename(columns={"participantGroup": "group"})
		participants = normalize_groups(participants, "group")

	time_df = _read_csv_safe(data_dir / "participant_time_per_component.csv")
	if time_df is not None and "group" in time_df.columns:
		time_df = normalize_groups(time_df, "group")

	likert = _read_csv_safe(data_dir / "questionnaire_likert_scores.csv")
	if likert is not None and "group" in likert.columns:
		likert = normalize_groups(likert, "group")

	open_resp = _read_csv_safe(data_dir / "questionnaire_open_responses.csv")
	if open_resp is not None and "group" in open_resp.columns:
		open_resp = normalize_groups(open_resp, "group")

	badge = _read_csv_safe(data_dir / "stimulus_badge_metrics.csv")

	notes = _read_csv_safe(data_dir / "stimulus_notes.csv")
	if notes is not None and "group" in notes.columns:
		notes = normalize_groups(notes, "group")

	return LoadedData(
		participants=participants,
		time_per_component=time_df,
		likert_scores=likert,
		open_responses=open_resp,
		badge_metrics=badge,
		notes=notes,
	)


def safe_make_dir(path: str | os.PathLike) -> None:
	pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def compute_word_counts(notes_df: pd.DataFrame) -> Optional[pd.DataFrame]:
	if notes_df is None:
		return None
	df = notes_df.copy()
	df["word_count"] = df["speech"].fillna("").astype(str).str.split().map(len)
	return df


def summarize_counts_by_group(participants_df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
	if participants_df is None or "group" not in participants_df.columns:
		return None
	return (
		participants_df.groupby("group", dropna=False)["participantId"]
		.nunique()
		.reset_index(name="n_participants")
	)


def get_time_columns(df: pd.DataFrame) -> Tuple[list[str], list[str]]:
	if df is None:
		return [], []
	all_cols = list(df.columns)
	sec_cols = [c for c in all_cols if c.endswith("(s)")]
	non_sec_cols = [c for c in all_cols if c not in sec_cols]
	return sec_cols, non_sec_cols


# Figure utilities used by charts modules
def figure_path(out_dir: pathlib.Path, name: str) -> pathlib.Path:
	return out_dir / "figures" / f"{name}.png"


def save_current_fig(path: pathlib.Path, dpi: int = 160) -> None:
	import matplotlib.pyplot as plt

	path.parent.mkdir(parents=True, exist_ok=True)
	plt.tight_layout()
	plt.savefig(path, dpi=dpi, bbox_inches="tight")
	plt.close()

import os
import pathlib
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class LoadedData:
	participants: Optional[pd.DataFrame]
	time_per_component: Optional[pd.DataFrame]
	likert_scores: Optional[pd.DataFrame]
	open_responses: Optional[pd.DataFrame]
	badge_metrics: Optional[pd.DataFrame]
	notes: Optional[pd.DataFrame]


def _read_csv_safe(path: str | os.PathLike, dtype: Optional[Dict[str, str]] = None) -> Optional[pd.DataFrame]:
	try:
		return pd.read_csv(path, dtype=dtype)
	except FileNotFoundError:
		return None


def _normalize_group_label(label: str) -> str:
	if pd.isna(label):
		return label
	lbl = str(label).strip().lower()
	if lbl.endswith("-group"):
		lbl = lbl.replace("-group", "")
	return lbl


def normalize_groups(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
	df = df.copy()
	df[group_col] = df[group_col].map(_normalize_group_label)
	return df


def load_all_data(data_dir: str | os.PathLike) -> LoadedData:
	data_dir = pathlib.Path(data_dir)
	participants = _read_csv_safe(data_dir / "participants.csv")
	if participants is not None and "participantGroup" in participants.columns:
		participants = participants.rename(columns={"participantGroup": "group"})
		participants = normalize_groups(participants, "group")

	time_df = _read_csv_safe(data_dir / "participant_time_per_component.csv")
	if time_df is not None and "group" in time_df.columns:
		time_df = normalize_groups(time_df, "group")

	likert = _read_csv_safe(data_dir / "questionnaire_likert_scores.csv")
	if likert is not None and "group" in likert.columns:
		likert = normalize_groups(likert, "group")

	open_resp = _read_csv_safe(data_dir / "questionnaire_open_responses.csv")
	if open_resp is not None and "group" in open_resp.columns:
		open_resp = normalize_groups(open_resp, "group")

	badge = _read_csv_safe(data_dir / "stimulus_badge_metrics.csv")

	notes = _read_csv_safe(data_dir / "stimulus_notes.csv")
	if notes is not None and "group" in notes.columns:
		notes = normalize_groups(notes, "group")

	return LoadedData(
		participants=participants,
		time_per_component=time_df,
		likert_scores=likert,
		open_responses=open_resp,
		badge_metrics=badge,
		notes=notes,
	)


def safe_make_dir(path: str | os.PathLike) -> None:
	pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def compute_word_counts(notes_df: pd.DataFrame) -> Optional[pd.DataFrame]:
	if notes_df is None:
		return None
	df = notes_df.copy()
	df["word_count"] = df["speech"].fillna("").astype(str).str.split().map(len)
	return df


def summarize_counts_by_group(participants_df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
	if participants_df is None or "group" not in participants_df.columns:
		return None
	return (
		participants_df.groupby("group", dropna=False)["participantId"]
		.nunique()
		.reset_index(name="n_participants")
	)


def get_time_columns(df: pd.DataFrame) -> Tuple[list[str], list[str]]:
	if df is None:
		return [], []
	all_cols = list(df.columns)
	sec_cols = [c for c in all_cols if c.endswith("(s)")]
	non_sec_cols = [c for c in all_cols if c not in sec_cols]
	return sec_cols, non_sec_cols



