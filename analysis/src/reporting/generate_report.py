import argparse
import datetime as dt
import pathlib
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from jinja2 import Template

from . import util
from . import text_clean
from charts.group_counts import plot_group_counts
from charts.time_distributions import plot_time_distributions
from charts.total_time_hist import plot_total_time_hist
from charts.likert_diverging_bars import plot_likert_diverging_bars
from charts.likert_dot_ci import plot_likert_dot_ci
from charts.likert_mean_bars import plot_likert_mean_bars
from charts.likert_mean_bars_altair import plot_likert_mean_bars_altair
from charts.likert_distribution_median import plot_likert_distribution_median
from charts.badge_hover_counts import (
	plot_badge_hover_counts,
	plot_badge_hover_times,
	plot_badge_hover_duration_stats,
)
from charts.badge_click_counts import plot_badge_click_counts
from charts.badge_drawer_times import (
	plot_badge_drawer_open_times,
	plot_badge_drawer_duration_stats,
)

import json


def _timestamp() -> str:
	return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _human_timestamp() -> str:
	return dt.datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M %Z")

def _run_label() -> str:
	# Human-friendly, filesystem-safe label for the report directory
	# Lowercase, underscores instead of spaces. Example: "sun_16_nov_2025_13-22"
	raw = dt.datetime.now().astimezone().strftime("%a %d %b %Y %H-%M")
	return raw.lower().replace(" ", "_")

def _sanitize_path_component(name: str) -> str:
	# Prevent path separator issues while keeping it readable
	return "".join(("-" if ch in {"/", "\\"} else ch) for ch in name).strip()


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


def _render_full_template(md_text: str, context: dict) -> str:
	if not md_text:
		return ""
	return Template(md_text).render(**context)


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

	run_id = run_id or _run_label()
	root_out = pathlib.Path(out_dir) / _sanitize_path_component(run_id)
	fig_out = root_out / "figures"
	util.safe_make_dir(fig_out)

	figure_paths: List[pathlib.Path] = []

	# Copy static stimulus assets (actual study stimuli) into the figures folder
	# so they can be referenced from the Markdown template via "figures/...".
	try:
		import shutil

		assets_dir = pathlib.Path(__file__).with_name("assets")
		stimulus_assets = [
			"stimuli_co2_emissions_badges.jpg",
			"stimuli_co2_emissions_footnotes.jpg",
			"stimuli_global_warming_badges.jpg",
			"stimuli_global_warming_footnotes.jpg",
		]
		for fname in stimulus_assets:
			src = assets_dir / fname
			if not src.exists():
				continue
			dst = fig_out / fname
			if not dst.exists():
				shutil.copy(src, dst)
	except Exception:
		# If anything goes wrong here, we still want the rest of the report to render.
		pass

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
		# Likert diverging bars (100% stacked)
		# p_likert_div = plot_likert_diverging_bars(data.likert_scores, root_out)
		# if p_likert_div is not None:
		# 	figure_paths.append(p_likert_div)
		# (removed) Likert mean scores chart
		# Likert mean bars
		p_likert_bar = plot_likert_mean_bars(data.likert_scores, root_out)
		if p_likert_bar is not None:
			figure_paths.append(p_likert_bar)
		# Altair version of Likert mean bars
		p_likert_bar_alt = plot_likert_mean_bars_altair(data.likert_scores, root_out)
		if p_likert_bar_alt is not None:
			figure_paths.append(p_likert_bar_alt)
		# Likert distributions + medians (Altair)
		p_likert_dist = plot_likert_distribution_median(data.likert_scores, root_out)
		if p_likert_dist is not None:
			figure_paths.append(p_likert_dist)

	# Badge hover-count & hover-time charts (Altair)
	badge_hover_chart: Optional[dict] = None
	badge_hover_time_chart: Optional[dict] = None
	badge_hover_duration_chart: Optional[dict] = None
	badge_click_chart: Optional[dict] = None
	badge_drawer_time_chart: Optional[dict] = None
	badge_drawer_duration_chart: Optional[dict] = None
	if data.badge_metrics is not None:
		badge_counts_fig = plot_badge_hover_counts(data.badge_metrics, root_out)
		if badge_counts_fig is not None:
			figure_paths.append(badge_counts_fig)
			badge_hover_chart = {
				"name": badge_counts_fig.stem,
				"path": f"figures/{badge_counts_fig.name}",
			}
		badge_time_fig = plot_badge_hover_times(data.badge_metrics, root_out)
		if badge_time_fig is not None:
			figure_paths.append(badge_time_fig)
			badge_hover_time_chart = {
				"name": badge_time_fig.stem,
				"path": f"figures/{badge_time_fig.name}",
			}
		badge_dur_fig = plot_badge_hover_duration_stats(data.badge_metrics, root_out)
		if badge_dur_fig is not None:
			figure_paths.append(badge_dur_fig)
			badge_hover_duration_chart = {
				"name": badge_dur_fig.stem,
				"path": f"figures/{badge_dur_fig.name}",
			}
		# Click counts (per badge, per stimulus)
		click_fig = plot_badge_click_counts(data.badge_metrics, root_out)
		if click_fig is not None:
			figure_paths.append(click_fig)
			badge_click_chart = {"name": click_fig.stem, "path": f"figures/{click_fig.name}"}
		# Drawer open metrics (time + mean duration)
		drawer_time_fig = plot_badge_drawer_open_times(data.badge_metrics, root_out)
		if drawer_time_fig is not None:
			figure_paths.append(drawer_time_fig)
			badge_drawer_time_chart = {"name": drawer_time_fig.stem, "path": f"figures/{drawer_time_fig.name}"}
		drawer_dur_fig = plot_badge_drawer_duration_stats(data.badge_metrics, root_out)
		if drawer_dur_fig is not None:
			figure_paths.append(drawer_dur_fig)
			badge_drawer_duration_chart = {"name": drawer_dur_fig.stem, "path": f"figures/{drawer_dur_fig.name}"}

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
		"demographics": False,
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

	context = {
		"report_title": "Mind the Badge – Automated Report",
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
		"badge_hover_chart": badge_hover_chart,
		"badge_hover_time_chart": badge_hover_time_chart,
		"badge_hover_duration_chart": badge_hover_duration_chart,
		"badge_click_chart": badge_click_chart,
		"badge_drawer_time_chart": badge_drawer_time_chart,
		"badge_drawer_duration_chart": badge_drawer_duration_chart,
		"demographics_rows": [],
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
		"group_line": group_line,
	}

	# Participant readable ID mapping
	participant_id_map: dict[str, str] = {}
	participant_map_records: list[dict] = []
	if data.participants is not None:
		dfp = data.participants
		if "participantId" in dfp.columns and "readableId" in dfp.columns:
			for _, row in dfp.iterrows():
				pid = str(row["participantId"])
				rid = None if pd.isna(row["readableId"]) else str(row["readableId"])
				if pid and rid:
					participant_id_map[pid] = rid
					participant_map_records.append({
						"participantId": pid,
						"readableId": rid,
						"group": str(row.get("group", "")) if "group" in dfp.columns else "",
					})

	# Attach per-component timing to the participant mapping records (converted to minutes)
	time_columns_map: list[dict] = []
	if data.time_per_component is not None and "participantId" in data.time_per_component.columns:
		time_df = data.time_per_component
		# Use all component columns (seconds) except identifiers; this includes questionnaires, intros, etc.
		time_components_for_map = [c for c in time_df.columns if c not in {"participantId", "group"}]
		time_lookup: dict[str, pd.Series] = {
			str(row["participantId"]): row for _, row in time_df.iterrows()
			if not pd.isna(row.get("participantId"))
		}

		for rec in participant_map_records:
			row = time_lookup.get(rec["participantId"])
			if row is None:
				# Still include keys so the template can render empty cells safely
				for col in time_components_for_map:
					rec[col] = ""
				continue
			for col in time_components_for_map:
				val = row.get(col)
				if pd.isna(val):
					rec[col] = ""
				else:
					# Convert seconds → minutes and round to 1 decimal place for display
					try:
						minutes = float(val) / 60.0
						rec[col] = round(minutes, 1)
					except Exception:
						rec[col] = val

		def _pretty_time_label(col: str) -> str:
			# Strip raw "(s)" suffix if present and annotate as minutes for clarity
			if col.endswith(" (s)"):
				base = col[:-4]
			else:
				base = col
			return f"{base} (min)"

		time_columns_map = [{"key": col, "label": _pretty_time_label(col)} for col in time_components_for_map]

	# Build open-ended responses summary for collapsible display
	def _build_open_questions_context() -> list[dict]:
		if data.open_responses is None or data.open_responses.empty:
			return []
		df = data.open_responses.copy()
		# Friendly group names
		title_map = {"footnote": "Footnotes", "badge": "Badges"}
		if "group" in df.columns:
			df["group_friendly"] = df["group"].map(lambda g: title_map.get(str(g).lower(), str(g).title()))
		else:
			df["group_friendly"] = "Unknown"
		# Known question columns – neutral, comparable dimension labels
		label_map = {
			# Noticing / attention
			"notice-comments": "Noticing and interactivity",
			"noticed-in-task": "Noticing and interactivity",
			# How annotations influenced reading
			"experience-with-badges": "How annotations influenced reading",
			# Shared dimensions (same ids in both groups)
			"ease-of-understanding": "Ease of understanding annotations",
			"considered-in-notes": "Use of annotations in the main task",
			"most-least-useful": "Most and least useful annotations",
			"overall-help": "Overall helpfulness of annotations",
			# Catch‑all comments
			"final-comments": "Additional comments",
		}

		# Load the exact question prompts from the study config so we can
		# reuse the real wording in the report (rather than short labels).
		badge_prompts: dict[str, str] = {}
		foot_prompts: dict[str, str] = {}
		try:
			this_file = pathlib.Path(__file__).resolve()
			project_root = this_file.parents[2].parent  # .../study
			cfg_path = project_root / "public" / "mind-the-badge" / "config.json"
			if cfg_path.exists():
				with cfg_path.open("r", encoding="utf-8") as f:
					cfg = json.load(f)
				components = cfg.get("components", {})
				for comp_id, target_dict in [
					("badge-questionaire-1", badge_prompts),
					("footnote-questionaire-1", foot_prompts),
				]:
					comp = components.get(comp_id)
					if not isinstance(comp, dict):
						continue
					for item in comp.get("response", []):
						if not isinstance(item, dict):
							continue
						if item.get("type") != "longText":
							continue
						qid = str(item.get("id", "")).strip()
						prompt = str(item.get("prompt", "")).strip()
						if qid and prompt:
							target_dict[qid] = prompt
		except Exception:
			pass

		questions: list[dict] = []
		for col, label in label_map.items():
			if col not in df.columns:
				continue
			sub = df[[c for c in ["participantId", "group_friendly", col] if c in df.columns]].copy()
			sub[col] = sub[col].apply(text_clean.clean_text)
			sub = sub[sub[col] != ""]
			if sub.empty:
				continue
			responses: list[dict] = []
			for _, row in sub.iterrows():
				pid = str(row.get("participantId", ""))
				rid = participant_id_map.get(pid)
				disp_id = rid or (pid[:8] if pid else "")
				text = str(row[col])
				# Simple word count for display (aligned with stimulus notes)
				words = len(text.split()) if text else 0
				responses.append(
					{
						"participant": disp_id,
						"group": row.get("group_friendly", "Unknown"),
						"text": text,
						"words": int(words),
					}
				)
			# Split responses by group for separate Footnotes/Badges drawers
			foot_responses = [r for r in responses if r.get("group") == "Footnotes"]
			badge_responses = [r for r in responses if r.get("group") == "Badges"]
			other_responses = [r for r in responses if r.get("group") not in {"Footnotes", "Badges"}]

			noticed_summary: list[dict] | None = None
			if col == "noticed-in-task":
				# Compact per-group summary table for the noticing question.
				# Fixed option order so that missing categories still appear with (0).
				option_order = [
					"Yes",
					"No",
					"Sometimes (I did not consistently check)",
					"Not sure",
				]
				groups_order = ["Footnotes", "Badges"]
				noticed_summary = []
				for g in groups_order:
					row_vals: list[dict] = []
					for opt in option_order:
						cnt = sum(1 for r in responses if r.get("group") == g and str(r.get("text", "")).strip() == opt)
						row_vals.append({"label": opt, "count": cnt})
					# Use key "options" instead of "values" to avoid clashing with dict.values()
					noticed_summary.append({"group": g, "options": row_vals})

			questions.append(
				{
					"key": col,
					"label": label,
					"count": len(responses),
					"responses": responses,
					"responses_footnotes": foot_responses,
					"responses_badges": badge_responses,
					"responses_other": other_responses,
					"prompt_footnotes": foot_prompts.get(col),
					"prompt_badges": badge_prompts.get(col),
					"noticed_summary": noticed_summary,
				}
			)
		return questions

	context["open_questions"] = _build_open_questions_context()

	# Build stimulus notes context and simple stats
	def _build_notes_context() -> tuple[list[dict], dict]:
		if data.notes is None or data.notes.empty:
			return [], {}
		dfn = data.notes.copy()
		dfn["speech"] = dfn["speech"].apply(text_clean.clean_text)
		dfn = dfn[dfn["speech"].str.strip() != ""]
		if dfn.empty:
			return [], {}
		# Friendly group names
		title_map = {"footnote": "Footnotes", "badge": "Badges"}
		if "group" in dfn.columns:
			dfn["group_friendly"] = dfn["group"].map(lambda g: title_map.get(str(g).lower(), str(g).title()))
		else:
			dfn["group_friendly"] = "Unknown"
		# Word counts
		dfn["word_count"] = dfn["speech"].str.split().map(len)
		# Pretty stimulus labels
		stim_label = {
			"global-warming-projection": "Global Warming Projection",
			"co2-emissions": "CO₂ Emissions",
		}
		dfn["stimulus_label"] = dfn["stimulusId"].map(lambda s: stim_label.get(str(s), str(s)))
		# Summary stats
		total = int(dfn.shape[0])
		median_wc = int(dfn["word_count"].median()) if not dfn["word_count"].empty else 0
		mean_wc = float(dfn["word_count"].mean()) if not dfn["word_count"].empty else 0.0
		counts_by_group = dfn.groupby("group_friendly")["speech"].count().to_dict()
		summary = {
			"total": total,
			"median_words": median_wc,
			"mean_words": round(mean_wc, 1),
			"counts_by_group": counts_by_group,
		}
		# Group responses by stimulus label
		items: list[dict] = []
		for stim, sub in dfn.groupby("stimulus_label", dropna=False):
			responses = []
			for _, row in sub.iterrows():
				pid = str(row.get("participantId", ""))
				rid = participant_id_map.get(pid)
				disp_id = rid or (pid[:8] if pid else "")
				responses.append(
					{
						"participant": disp_id,
						"group": row.get("group_friendly", "Unknown"),
						"words": int(row.get("word_count", 0)),
						"text": row.get("speech", ""),
					}
				)
			items.append({"stimulus": stim, "count": len(responses), "responses": responses})
		# Sort stimuli by name for stability
		items.sort(key=lambda d: d["stimulus"])
		return items, summary

	notes_items, notes_summary = _build_notes_context()
	context["notes_items"] = notes_items
	context["notes_summary"] = notes_summary
	context["participant_id_map"] = participant_map_records
	context["time_columns_map"] = time_columns_map

	# Build the template text: use provided --md paths as the full template,
	# otherwise fall back to the default packaged template.
	# Demographics table rows (read directly from CSV to avoid coupling)
	try:
		demo_path = pathlib.Path(data_dir) / "demographics.csv"
		if demo_path.exists():
			dfd = pd.read_csv(demo_path)
			# Build compact summary (top values per category)
			label_map_demo = {
				"gender": "Gender",
				"age": "Age",
				"education": "Education",
				"field-of-study": "Field",
				"chart-reading-frequency": "Reads charts",
				"chart-creation-frequency": "Creates charts",
				"color-vision": "Color vision",
			}
			summary_items: list[dict] = []
			for col, label in label_map_demo.items():
				if col not in dfd.columns:
					continue
				series = dfd[col].dropna().astype(str).str.strip()
				if series.empty:
					continue
				vc = series.value_counts()
				top = vc.head(3).items()
				values = [{"value": k, "count": int(v)} for k, v in top]
				total = int(series.shape[0])
				summary_items.append({"label": label, "top_values": values, "total": total})
			if summary_items:
				context["demographics_summary"] = summary_items
			preferred = [
				"readableId",
				"gender",
				"age",
				"education",
				"field-of-study",
				"chart-reading-frequency",
				"chart-creation-frequency",
				"color-vision",
			]
			cols = [c for c in preferred if c in dfd.columns]
			if cols:
				dfd = dfd[cols]
			if "readableId" in dfd.columns:
				dfd = dfd.sort_values("readableId")
			context["demographics_rows"] = dfd.to_dict(orient="records")
			files_present["demographics"] = True
	except Exception:
		pass

	# Build the template text: use provided --md paths as the full template,
	# otherwise fall back to the default packaged template.
	md_template_text = ""
	if md_paths:
		md_template_text = _read_markdown_files(md_paths)
	if not md_template_text:
		default_template = pathlib.Path(__file__).with_name("templates") / "report.md"
		if default_template.exists():
			md_template_text = default_template.read_text(encoding="utf-8")

	# Auto-load study Likert question texts if not provided
	def _auto_load_likert_md() -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
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
					def _extract_items(key: str) -> tuple[list[tuple[str, str]], Optional[str], Optional[str]]:
						comp = components.get(key)
						if not isinstance(comp, dict):
							return [], None, None
						items = comp.get("response", [])
						likerts = [it for it in items if isinstance(it, dict) and it.get("type") == "likert"]
						if not likerts:
							return [], None, None
						left = likerts[0].get("leftLabel")
						right = likerts[0].get("rightLabel")
						items_out: list[tuple[str, str]] = []
						for it in likerts:
							item_id = str(it.get("id", "")).strip()
							prompt = str(it.get("prompt", "")).strip()
							if item_id or prompt:
								items_out.append((item_id, prompt))
						return items_out, left, right
					def _build_md_from_items(items: list[tuple[str, str]], left: Optional[str], right: Optional[str]) -> Optional[str]:
						if not items:
							return None
						ls = [f"_Scale: 1 = {left or 'Strongly Disagree'}, 5 = {right or 'Strongly Agree'}_", ""]
						for item_id, prompt in items:
							label = f"**{item_id}**: " if item_id else ""
							ls.append(f"- {label}{prompt}")
						return "\n".join(ls)
					badge_items, b_left, b_right = _extract_items("badge-questionaire-2")
					foot_items, f_left, f_right = _extract_items("footnote-questionaire-2")
					badge_md = _build_md_from_items(badge_items, b_left, b_right)
					foot_md = _build_md_from_items(foot_items, f_left, f_right)
					# Scale labels (prefer badge, then footnote)
					scale_left = b_left or f_left
					scale_right = b_right or f_right
					# Build merged items, deduplicating identical prompts per id
					merged_lines: list[str] = []
					compact_lines: list[str] = []
					if badge_items or foot_items:
						merged_lines.append(f"_Scale: 1 = {scale_left or 'Strongly Disagree'}, 5 = {scale_right or 'Strongly Agree'}_")
						merged_lines.append("")
						# Build stable keys (prefer id; fallback to prompt)
						def _key_for(item_id: str, prompt: str) -> str:
							return item_id if item_id else f"__prompt__:{prompt}"
						foot_keys = [_key_for(i, p) for i, p in foot_items]
						badge_keys = [_key_for(i, p) for i, p in badge_items]
						# Preserve order: start with footnotes, then append any missing from badges
						order = foot_keys + [k for k in badge_keys if k not in set(foot_keys)]
						# Build maps from key to prompt text
						foot_map = {_key_for(i, p): p for i, p in foot_items}
						badge_map = {_key_for(i, p): p for i, p in badge_items}
						seen = set()
						for key in order:
							if key in seen:
								continue
							seen.add(key)
							fp = foot_map.get(key)
							bp = badge_map.get(key)
							item_label = key if not str(key).startswith("__prompt__:") else ""
							if fp and bp and fp.strip().lower() == bp.strip().lower():
								prefix = f"**{item_label}**: " if item_label else ""
								merged_lines.append(f"- {prefix}{fp}")
								# Compact: just the prompt
								compact_lines.append(f"- {fp}")
							else:
								# Show differences per group
								title = f"**{item_label}**" if item_label else None
								if title:
									merged_lines.append(f"- {title}")
								if fp:
									merged_lines.append(f"  - Footnotes: {fp}")
								if bp:
									merged_lines.append(f"  - Badges: {bp}")
								# Compact: show a single line and mark as differing
								choice = fp or bp or ""
								if choice:
									compact_lines.append(f"- {choice} _(differs by group)_")
					merged_md = "\n".join(merged_lines) if merged_lines else None
					compact_md = "\n".join(compact_lines) if compact_lines else None
					return badge_md, foot_md, scale_left, scale_right, merged_md, compact_md
				except Exception:
					continue
		return None, None, None, None, None, None

	if (not likert_questions_badge_md) or (not likert_questions_footnote_md):
		auto_badge_md, auto_foot_md, scale_left, scale_right, merged_md, compact_md = _auto_load_likert_md()
		if not likert_questions_badge_md and auto_badge_md:
			context["likert_questions_badge_md"] = auto_badge_md
		if not likert_questions_footnote_md and auto_foot_md:
			context["likert_questions_footnote_md"] = auto_foot_md
		if scale_left:
			context["likert_scale_left"] = scale_left
		if scale_right:
			context["likert_scale_right"] = scale_right
		if merged_md:
			context["likert_questions_merged_md"] = merged_md
		if compact_md:
			context["likert_questions_compact_md"] = compact_md

	# Render the full template with the context
	md_out = _render_full_template(md_template_text, context)
	md_path = root_out / "report.md"
	with open(md_path, "w", encoding="utf-8") as f:
		f.write(md_out)
	return md_path


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generate a Markdown report from the study CSVs.")
	parser.add_argument("--data-dir", type=str, default="data", help="Directory containing CSV files.")
	parser.add_argument("--out-dir", type=str, default="reports", help="Directory to write the generated report into.")
	parser.add_argument("--run-id", type=str, default=None, help="Optional custom run id to use in the output path.")
	parser.add_argument("--md", action="append", default=[], help="Path(s) to Markdown template file(s) to render (Jinja2). If multiple are provided, they will be concatenated in order before rendering.")
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


