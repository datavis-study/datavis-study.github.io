import argparse
import datetime as dt
import pathlib
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from jinja2 import Template

from . import util


def _timestamp() -> str:
	return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _human_timestamp() -> str:
	return dt.datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M %Z")


def _figure_path(out_dir: pathlib.Path, name: str) -> pathlib.Path:
	return out_dir / "figures" / f"{name}.png"


def _save_current_fig(path: pathlib.Path, dpi: int = 160) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	plt.tight_layout()
	plt.savefig(path, dpi=dpi, bbox_inches="tight")
	plt.close()


def _plot_group_counts(participants: pd.DataFrame, out_dir: pathlib.Path) -> Optional[pathlib.Path]:
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


def _plot_time_distributions(time_df: pd.DataFrame, out_dir: pathlib.Path, component_cols: List[str]) -> List[pathlib.Path]:
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
		path = _figure_path(out_dir, fig_name)
		_save_current_fig(path)
		paths.append(path)
	return paths


def _plot_total_time_hist(time_df: pd.DataFrame, out_dir: pathlib.Path, col: str = "total (s)") -> Optional[pathlib.Path]:
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


def _read_markdown_files(md_paths: List[str]) -> str:
	texts: List[str] = []
	for p in md_paths:
		try:
			with open(p, "r", encoding="utf-8") as f:
				texts.append(f.read())
		except FileNotFoundError:
			continue
	return "\n\n".join(texts).strip()


def _render_md_template(md_text: str, context: dict) -> str:
	if not md_text:
		return ""
	return Template(md_text).render(**context)


def _build_markdown(report_title: str, timestamp: str, intro_lines: List[str], narrative_md: str | None = None) -> str:
	lines: List[str] = []
	lines.append(f"# {report_title}")
	lines.append("")
	lines.append(f"_Generated: {timestamp}_")
	lines.append("")
	if intro_lines:
		lines.append("## Overview")
		lines.extend([f"- {line}" for line in intro_lines])
		lines.append("")
	if narrative_md:
		lines.append("## Narrative")
		lines.append(narrative_md.strip())
		lines.append("")
	return "\n".join(lines).rstrip() + "\n"


def generate_report(data_dir: str, out_dir: str, run_id: Optional[str] = None, md_paths: Optional[List[str]] = None) -> pathlib.Path:
	sns.set_theme(style="whitegrid")
	plt.rcParams["font.family"] = "DejaVu Sans"
	data = util.load_all_data(data_dir)

	run_id = run_id or _timestamp()
	root_out = pathlib.Path(out_dir) / f"report_{run_id}"
	fig_out = root_out / "figures"
	util.safe_make_dir(fig_out)

	figure_paths: List[pathlib.Path] = []

	p1 = _plot_group_counts(data.participants, root_out)
	if p1 is not None:
		figure_paths.append(p1)

	if data.time_per_component is not None:
		component_cols = []
		for col in ["global-warming-projection (s)", "co2-emissions (s)", "total (s)"]:
			if col in data.time_per_component.columns:
				component_cols.append(col)
		figure_paths.extend(_plot_time_distributions(data.time_per_component, root_out, component_cols))
		p_total_hist = _plot_total_time_hist(data.time_per_component, root_out, col="total (s)")
		if p_total_hist is not None:
			figure_paths.append(p_total_hist)

	n_participants = (
		int(data.participants["participantId"].nunique())
		if data.participants is not None and "participantId" in data.participants.columns
		else 0
	)
	group_counts = util.summarize_counts_by_group(data.participants)
	if group_counts is not None and not group_counts.empty:
		group_line = "; ".join(f"{row['group']}: {int(row['n_participants'])}" for _, row in group_counts.iterrows())
	else:
		group_line = "No participant metadata available"

	def _top_counts(series: Optional[pd.Series], top_n: int = 3) -> list[tuple[str, int]]:
		if series is None:
			return []
		vc = series.dropna().astype(str).str.strip()
		if vc.empty:
			return []
		cnt = vc.value_counts().head(top_n)
		return [(idx, int(val)) for idx, val in cnt.items()]

	languages_top: list[tuple[str, int]] = []
	if data.participants is not None and "language" in data.participants.columns:
		lang_primary = data.participants["language"].dropna().astype(str).str.split("-").str[0]
		languages_top = _top_counts(lang_primary, top_n=3)

	countries_top: list[tuple[str, int]] = []
	if data.participants is not None and "country" in data.participants.columns:
		countries_top = _top_counts(data.participants["country"], top_n=3)

	resolutions_top: list[tuple[str, int]] = []
	if data.participants is not None and {"resolutionWidth", "resolutionHeight"}.issubset(data.participants.columns):
		res_str = (data.participants["resolutionWidth"].astype("Int64").astype(str) + "x" + data.participants["resolutionHeight"].astype("Int64").astype(str))
		resolutions_top = _top_counts(res_str, top_n=3)

	files_present = {
		"participants": data.participants is not None,
		"time_per_component": data.time_per_component is not None,
		"likert_scores": data.likert_scores is not None,
		"open_responses": data.open_responses is not None,
		"badge_metrics": data.badge_metrics is not None,
		"notes": data.notes is not None,
	}

	time_components: list[str] = []
	time_outliers: dict[str, int] = {}
	if data.time_per_component is not None:
		sec_cols, _ = util.get_time_columns(data.time_per_component)
		time_components = [c for c in sec_cols if c in data.time_per_component.columns]
		for c in time_components:
			series = data.time_per_component[c]
			time_outliers[c] = int(series[series > 1800].count())

	n_likert = int(data.likert_scores["participantId"].nunique()) if data.likert_scores is not None and "participantId" in data.likert_scores.columns else 0
	n_open = int(data.open_responses["participantId"].nunique()) if data.open_responses is not None and "participantId" in data.open_responses.columns else 0

	n_notes = 0
	median_note_words = None
	if data.notes is not None and "speech" in data.notes.columns:
		n_notes = int(data.notes.shape[0])
		words = data.notes["speech"].fillna("").astype(str).str.split().map(len)
		median_note_words = int(words.median()) if not words.empty else None

	n_badge_rows = int(data.badge_metrics.shape[0]) if data.badge_metrics is not None else 0
	n_badge_labels = int(data.badge_metrics["badgeLabel"].nunique()) if data.badge_metrics is not None and "badgeLabel" in data.badge_metrics.columns else 0
	n_stimuli_with_badges = int(data.badge_metrics["stimulusId"].nunique()) if data.badge_metrics is not None and "stimulusId" in data.badge_metrics.columns else 0

	intro_lines = [
		f"Participants: {n_participants}",
		f"Group split: {group_line}",
		f"Data directory: {pathlib.Path(data_dir).resolve()}",
	]

	context = {
		"participants_count": n_participants,
		"group_counts": (group_counts.to_dict(orient="records") if group_counts is not None else []),
		"data_dir": str(pathlib.Path(data_dir).resolve()),
		"out_dir": str(root_out.resolve()),
		"run_id": run_id,
		"generated_at": _human_timestamp(),
		"figures": [{"name": p.stem, "filename": p.name, "path": f"figures/{p.name}"} for p in figure_paths],
		"languages_top": languages_top,
		"countries_top": countries_top,
		"resolutions_top": resolutions_top,
		"files_present": files_present,
		"time_components": time_components,
		"time_outliers": time_outliers,
		"n_likert": n_likert,
		"n_open": n_open,
		"n_notes": n_notes,
		"median_note_words": median_note_words,
		"n_badge_rows": n_badge_rows,
		"n_badge_labels": n_badge_labels,
		"n_stimuli_with_badges": n_stimuli_with_badges,
	}

	narrative_md = None
	if md_paths:
		md_text = _read_markdown_files(md_paths)
		narrative_md = _render_md_template(md_text, context) if md_text else None

	md_out = _build_markdown(
		report_title="Mind the Badge – Automated Report",
		timestamp=_human_timestamp(),
		intro_lines=intro_lines,
		narrative_md=narrative_md,
	)
	md_path = root_out / "report.md"
	with open(md_path, "w", encoding="utf-8") as f:
		f.write(md_out)
	return md_path


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generate a Markdown report from the study CSVs.")
	parser.add_argument("--data-dir", type=str, default="data", help="Directory containing CSV files.")
	parser.add_argument("--out-dir", type=str, default="reports", help="Directory to write the generated report into.")
	parser.add_argument("--run-id", type=str, default=None, help="Optional custom run id to use in the output path.")
	parser.add_argument("--md", action="append", default=[], help="Path(s) to Markdown file(s) to include as narrative (supports Jinja2 templating). Can be passed multiple times.")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	out_path = generate_report(data_dir=args.data_dir, out_dir=args.out_dir, run_id=args.run_id, md_paths=args.md)
	print(f"Report written to: {out_path}")


if __name__ == "__main__":
	main()


