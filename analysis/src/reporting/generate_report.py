import argparse
import datetime as dt
import pathlib
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from jinja2 import Template

from . import util
from charts.group_counts import plot_group_counts
from charts.time_distributions import plot_time_distributions
from charts.total_time_hist import plot_total_time_hist
from charts.likert_beehive import plot_likert_beehive

import json


def _timestamp() -> str:
	return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _human_timestamp() -> str:
	return dt.datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M %Z")


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


def generate_report(
	data_dir: str,
	out_dir: str,
	run_id: Optional[str] = None,
	md_paths: Optional[List[str]] = None,
	likert_questions_badge_md: Optional[str] = None,
	likert_questions_footnote_md: Optional[str] = None,
) -> pathlib.Path:
	sns.set_theme(style="whitegrid")
	plt.rcParams["font.family"] = "DejaVu Sans"
	data = util.load_all_data(data_dir)

	run_id = run_id or _timestamp()
	root_out = pathlib.Path(out_dir) / f"report_{run_id}"
	fig_out = root_out / "figures"
	util.safe_make_dir(fig_out)

	figure_paths: List[pathlib.Path] = []

	p1 = plot_group_counts(data.participants, root_out)
	if p1 is not None:
		figure_paths.append(p1)

	if data.time_per_component is not None:
		component_cols = []
		for col in ["global-warming-projection (s)", "co2-emissions (s)", "total (s)"]:
			if col in data.time_per_component.columns:
				component_cols.append(col)
		figure_paths.extend(plot_time_distributions(data.time_per_component, root_out, component_cols))
		p_total_hist = plot_total_time_hist(data.time_per_component, root_out, col="total (s)")
		if p_total_hist is not None:
			figure_paths.append(p_total_hist)
	# Likert beehive plot
	if data.likert_scores is not None:
		p_likert_bee = plot_likert_beehive(data.likert_scores, root_out)
		if p_likert_bee is not None:
			figure_paths.append(p_likert_bee)

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
		"dimension_labels": {
			"saliency": "Saliency",
			"clutter": "Clutter",
			"interpretability": "Interpretability",
			"usefulness": "Usefulness",
			"trust": "Trust",
			"standardization": "Standardization",
		},
		"dimension_questions": [
			{"key": "saliency", "label": "Saliency", "question": "How noticeable were the visual cues/elements?"},
			{"key": "clutter", "label": "Clutter", "question": "How cluttered or visually busy did it feel?"},
			{"key": "interpretability", "label": "Interpretability", "question": "How easy was it to interpret and understand the visualization?"},
			{"key": "usefulness", "label": "Usefulness", "question": "How useful was the added information for your task?"},
			{"key": "trust", "label": "Trust", "question": "How much did you trust the presented information?"},
			{"key": "standardization", "label": "Standardization", "question": "How consistent/standardized did the presentation feel?"},
		],
		"likert_questions_badge_md": likert_questions_badge_md,
		"likert_questions_footnote_md": likert_questions_footnote_md,
	}

	narrative_md = None
	if md_paths:
		md_text = _read_markdown_files(md_paths)
		narrative_md = _render_md_template(md_text, context) if md_text else None

	# Auto-load study Likert question texts if not provided
	def _auto_load_likert_md() -> tuple[Optional[str], Optional[str]]:
		try_paths = []
		# Attempt to locate project root (study/) from this file path
		this_file = pathlib.Path(__file__).resolve()
		# analysis/src/reporting/generate_report.py → project root is parent of "analysis"
		candidate_root = this_file.parents[2].parent  # .../study
		try_paths.append(candidate_root / "public" / "mind-the-badge" / "config.json")
		for p in try_paths:
			if p.exists():
				try:
					cfg = json.loads(p.read_text(encoding="utf-8"))
					components = cfg.get("components", {})
					def _build_md(key: str, label_prefix: str) -> Optional[str]:
						comp = components.get(key)
						if not isinstance(comp, dict):
							return None
						items = comp.get("response", [])
						likerts = [it for it in items if isinstance(it, dict) and it.get("type") == "likert"]
						if not likerts:
							return None
						left = likerts[0].get("leftLabel", "Strongly Disagree")
						right = likerts[0].get("rightLabel", "Strongly Agree")
						lines = [f"_Scale: 1 = {left}, 5 = {right}_", ""]
						for it in likerts:
							item_id = it.get("id", "")
							prompt = it.get("prompt", "")
							lines.append(f"- **{item_id}**: {prompt}")
						return "\n".join(lines)
					badge_md = _build_md("badge-questionaire-2", "Badges")
					foot_md = _build_md("footnote-questionaire-2", "Footnotes")
					return badge_md, foot_md
				except Exception:
					continue
		return None, None

	if not likert_questions_badge_md or not likert_questions_footnote_md:
		auto_badge_md, auto_foot_md = _auto_load_likert_md()
		if not likert_questions_badge_md and auto_badge_md:
			context["likert_questions_badge_md"] = auto_badge_md
		if not likert_questions_footnote_md and auto_foot_md:
			context["likert_questions_footnote_md"] = auto_foot_md

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
	parser.add_argument("--likert-questions-badge", type=str, default=None, help="Optional Markdown file with exact badge-group Likert question texts.")
	parser.add_argument("--likert-questions-footnote", type=str, default=None, help="Optional Markdown file with exact footnote-group Likert question texts.")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	# Read optional question files
	likert_q_badge = None
	likert_q_footnote = None
	if args.likert_questions_badge and pathlib.Path(args.likert_questions_badge).exists():
		likert_q_badge = pathlib.Path(args.likert_questions_badge).read_text(encoding="utf-8")
	if args.likert_questions_footnote and pathlib.Path(args.likert_questions_footnote).exists():
		likert_q_footnote = pathlib.Path(args.likert_questions_footnote).read_text(encoding="utf-8")
	# Generate report
	out_path = generate_report(
		data_dir=args.data_dir,
		out_dir=args.out_dir,
		run_id=args.run_id,
		md_paths=args.md,
		likert_questions_badge_md=likert_q_badge,
		likert_questions_footnote_md=likert_q_footnote,
	)
	# Append info about where to place question files if missing (context is used during rendering already if supplied)
	print(f"Report written to: {out_path}")


if __name__ == "__main__":
	main()


