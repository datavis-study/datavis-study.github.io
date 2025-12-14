import argparse
import datetime as dt
import pathlib
from typing import List, Optional

import pandas as pd
from jinja2 import Template
import json
import shutil

from . import util
from . import text_clean


def _timestamp() -> str:
	return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _human_timestamp() -> str:
	return dt.datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M %Z")


def _run_label() -> str:
	"""
	Human-friendly, filesystem-safe label for the report directory.

	We prefix with an ISO-style date and time so that lexicographic sorting
	matches chronological order, ensuring the newest report directory appears
	at the bottom when sorted by name in ascending order.

	Example: "2025-12-05_18-19_fri"
	"""
	now = dt.datetime.now().astimezone()
	date_part = now.strftime("%Y-%m-%d")
	time_part = now.strftime("%H-%M")
	weekday_part = now.strftime("%a").lower()
	return f"{date_part}_{time_part}_{weekday_part}"

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
	data = util.load_all_data(data_dir)

	run_id = run_id or _run_label()
	root_out = pathlib.Path(out_dir) / _sanitize_path_component(run_id)
	# Ensure the report output directory (and figures/data subfolders) exist
	util.safe_make_dir(root_out)
	fig_out = root_out / "figures"
	util.safe_make_dir(fig_out)
	data_out = root_out / "data"
	util.safe_make_dir(data_out)

	# Archive all CSV data files used for this report into the run directory
	try:
		data_dir_path = pathlib.Path(data_dir)
		if data_dir_path.exists():
			for csv_path in data_dir_path.glob("*.csv"):
				dst = data_out / csv_path.name
				shutil.copy2(csv_path, dst)
	except Exception:
		# Data archiving should not break report generation
		pass

	# Copy R-generated charts (and any other PNGs) into the local figures folder
	try:
		this_file = pathlib.Path(__file__).resolve()
		analysis_dir = this_file.parents[2]  # .../analysis
		# Copy both "global" R outputs and s1b-specific charts
		r_output_dirs = [
			analysis_dir / "r_output",
			analysis_dir / "s1b" / "r_output",
		]
		for r_output_dir in r_output_dirs:
			if not r_output_dir.exists():
				continue
			for png in r_output_dir.glob("*.png"):
				dst = fig_out / png.name
				if not dst.exists():
					shutil.copy2(png, dst)
		# Also copy static stimulus assets if present
		assets_dir = this_file.with_name("assets")
		if assets_dir.exists():
			for asset in assets_dir.iterdir():
				if asset.suffix.lower() in {".png", ".jpg", ".jpeg"}:
					dst = fig_out / asset.name
					if not dst.exists():
						shutil.copy2(asset, dst)
	except Exception:
		# Figure copying is best-effort; do not fail the whole report
		pass
	# Ensure the report output directory exists before writing report.md
	util.safe_make_dir(root_out)
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

	# Prettified group counts for the report header (Badges / Footnotes)
	group_label_map = {
		"badge": "Badges",
		"badges": "Badges",
		"footnote": "Footnotes",
		"footnotes": "Footnotes",
	}
	group_counts_pretty: list[dict] = []
	if group_counts is not None and not group_counts.empty:
		for _, row in group_counts.iterrows():
			raw = str(row.get("group", "")).strip()
			label = group_label_map.get(raw.lower(), raw.title() if raw else "Unknown")
			group_counts_pretty.append({"group": label, "n": int(row.get("n_participants", 0))})

	# s1b "quick reminder" (do they remember the study / the stimuli?)
	quick_reminder: dict | None = None
	try:
		qr_path = pathlib.Path(data_dir) / "s1b" / "quick_reminder.csv"
		if qr_path.exists():
			qr = pd.read_csv(qr_path)
			# Normalize group labels
			if "group" in qr.columns:
				qr["group"] = qr["group"].astype(str).str.strip().str.lower()
			total = int(qr.shape[0])
			remember_study_yes = int((qr.get("rememberStudy", "").astype(str).str.strip().str.lower() == "yes").sum()) if "rememberStudy" in qr.columns else 0
			remember_stimuli_yes = int((qr.get("rememberStimuli", "").astype(str).str.strip().str.lower() == "yes").sum()) if "rememberStimuli" in qr.columns else 0
			by_group: list[dict] = []
			if "group" in qr.columns and total > 0:
				for g, sub in qr.groupby("group", dropna=False):
					g_label = group_label_map.get(str(g).lower(), str(g).title())
					g_total = int(sub.shape[0])
					g_stim_yes = int((sub.get("rememberStimuli", "").astype(str).str.strip().str.lower() == "yes").sum()) if "rememberStimuli" in sub.columns else 0
					by_group.append({"group": g_label, "total": g_total, "remember_stimuli_yes": g_stim_yes})
				by_group.sort(key=lambda d: d["group"])
			quick_reminder = {
				"total": total,
				"remember_study_yes": remember_study_yes,
				"remember_stimuli_yes": remember_stimuli_yes,
				"remember_stimuli_all": (total > 0 and remember_stimuli_yes == total),
				"by_group": by_group,
			}
	except Exception:
		quick_reminder = None

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

	# Per-stimulus participant counts (hover / click) for badge interactions
	badge_participant_stats: list[dict] = []
	if (
		data.badge_metrics is not None
		and {"stimulusId", "hoverParticipantCount", "clickParticipantCount"}.issubset(data.badge_metrics.columns)
	):
		dfb = data.badge_metrics.copy()
		stim_label_map = {
			"co2-emissions": "CO₂ Emissions",
			"global-warming-projection": "Global Warming Projection",
		}
		for stim, sub in dfb.groupby("stimulusId", dropna=False):
			if pd.isna(stim):
				continue
			label = stim_label_map.get(str(stim), str(stim))
			hover_vals = sub["hoverParticipantCount"]
			click_vals = sub["clickParticipantCount"]
			hover_n = int(hover_vals.max()) if not hover_vals.isna().all() else 0
			click_n = int(click_vals.max()) if not click_vals.isna().all() else 0
			badge_participant_stats.append(
				{
					"stimulusId": str(stim),
					"label": label,
					"hover_participants": hover_n,
					"click_participants": click_n,
				}
			)
		badge_participant_stats.sort(key=lambda d: d["label"])

	context = {
		"report_title": "Mind the Badge – Automated Report",
		"participants_count": n_participants,
		"group_counts": (group_counts.to_dict(orient="records") if group_counts is not None else []),
		"group_counts_pretty": group_counts_pretty,
		"quick_reminder": quick_reminder,
		"data_dir": str(pathlib.Path(data_dir).resolve()),
		"out_dir": str(root_out.resolve()),
		"run_id": run_id,
		"generated_at": _human_timestamp(),
		# No Python-generated figures; R scripts handle chart creation outside this pipeline.
		"figures": [],
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
		"badge_participant_stats": badge_participant_stats,
		# Chart metadata is omitted; the report no longer embeds charts.
		"badge_hover_chart": None,
		"badge_hover_time_chart": None,
		"badge_hover_duration_chart": None,
		"badge_click_chart": None,
		"badge_drawer_time_chart": None,
		"badge_drawer_duration_chart": None,
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

	# Participant readable ID mapping (+ Prolific flag)
	participant_id_map: dict[str, str] = {}
	participant_is_prolific: dict[str, bool] = {}
	participant_first_stimulus: dict[str, str] = {}
	participant_map_records: list[dict] = []
	if data.participants is not None:
		dfp = data.participants
		has_prolific = "isProlific" in dfp.columns
		has_first_stim = "firstStimulus" in dfp.columns
		if "participantId" in dfp.columns and "readableId" in dfp.columns:
			for _, row in dfp.iterrows():
				pid = str(row["participantId"])
				rid = None if pd.isna(row["readableId"]) else str(row["readableId"])
				if pid and rid:
					participant_id_map[pid] = rid
					if has_prolific:
						participant_is_prolific[pid] = bool(row.get("isProlific"))
					if has_first_stim:
						fs = row.get("firstStimulus")
						if isinstance(fs, str) and fs:
							participant_first_stimulus[pid] = fs
					participant_map_records.append({
						"participantId": pid,
						"readableId": rid,
						"group": str(row.get("group", "")) if "group" in dfp.columns else "",
						"isProlific": bool(row.get("isProlific")) if has_prolific else False,
					})

	# ---------------------------------------------------------------------
	# s1b follow-up: participant counts + free-text preference reasons
	# ---------------------------------------------------------------------
	s1b_followup: dict | None = None
	s1b_preference_reasons: list[dict] = []
	s1b_preference_summary: list[dict] = []
	try:
		s1b_pref_path = pathlib.Path(data_dir) / "s1b" / "preferences.csv"
		if s1b_pref_path.exists():
			df_s1b_pref = pd.read_csv(s1b_pref_path)
			if {"group", "participantId"}.issubset(df_s1b_pref.columns):
				# Normalize groups
				df_s1b_pref["group"] = df_s1b_pref["group"].astype(str).str.strip().str.lower()
				df_s1b_pref["participantId"] = df_s1b_pref["participantId"].astype(str).str.strip()

				# Participant counts (who actually filled out the s1b preferences)
				counts = (
					df_s1b_pref.groupby("group", dropna=False)["participantId"]
					.nunique()
					.reset_index(name="n")
				)
				counts_pretty: list[dict] = []
				total_n = int(df_s1b_pref["participantId"].nunique())
				for _, row in counts.iterrows():
					raw = str(row.get("group", "")).strip().lower()
					# Use the study identifiers for clarity in the report
					if raw == "badges":
						label = "s1b-badges"
					elif raw == "footnotes":
						label = "s1b-footnotes"
					else:
						label = raw if raw else "Unknown"
					counts_pretty.append({"group": label, "n": int(row.get("n", 0))})
				# Stable order
				order = {"s1b-badges": 0, "s1b-footnotes": 1}
				counts_pretty.sort(key=lambda d: order.get(d["group"], 99))
				s1b_followup = {"total": total_n, "by_group": counts_pretty}

				# Free-text reasons (the *_why columns)
				task_map = [
					("global_understanding", "Stimuli 1 - Understanding"),
					("co2_understanding", "Stimuli 2 - Understanding"),
					("global_presenting", "Stimuli 1 - Presenting"),
					("co2_presenting", "Stimuli 2 - Presenting"),
				]

				def _pref_label(x: str) -> str:
					v = str(x or "").strip().lower()
					if v == "badges":
						return "Prefer Badges"
					if v == "footnotes":
						return "Prefer Footnotes"
					return "No preference"

				for key, label in task_map:
					choice_col = f"{key}_choice"
					why_col = f"{key}_why"
					if choice_col not in df_s1b_pref.columns or why_col not in df_s1b_pref.columns:
						continue

					res_badges: list[dict] = []
					res_foot: list[dict] = []

					for _, row in df_s1b_pref.iterrows():
						pid = str(row.get("participantId", "")).strip()
						if not pid:
							continue
						group_raw = str(row.get("group", "")).strip().lower()
						why = text_clean.clean_text(row.get(why_col))
						if not why:
							continue
						choice = _pref_label(row.get(choice_col))
						rid = participant_id_map.get(pid) or (pid[:8] if pid else "")
						is_prolific = participant_is_prolific.get(pid, False)
						rec = {
							"participant": rid,
							"isProlific": bool(is_prolific),
							"choice": choice,
							"text": why,
						}
						if group_raw == "badges":
							res_badges.append(rec)
						elif group_raw == "footnotes":
							res_foot.append(rec)

					s1b_preference_reasons.append(
						{
							"key": key,
							"label": label,
							"responses_badges": res_badges,
							"responses_footnotes": res_foot,
						}
					)

				# Preference counts (for compact reporting in the main report)
				def _count_choice(col: str) -> dict[str, int]:
					ser = df_s1b_pref[col].dropna().astype(str).str.strip().str.lower()
					return {
						"badges": int((ser == "badges").sum()),
						"footnotes": int((ser == "footnotes").sum()),
						"no_preference": int((~ser.isin(["badges", "footnotes"]) | (ser == "no_preference")).sum()),
						"n": int(ser.shape[0]),
					}

				# Extract the *exact* question wording from the s1b study config (best-effort).
				prompts: dict[str, dict] = {}
				try:
					this_file = pathlib.Path(__file__).resolve()
					project_root = this_file.parents[2].parent  # .../study
					cfg_candidates = [
						project_root / "public" / "s1b-footnotes" / "config.json",
						project_root / "public" / "s1b-badges" / "config.json",
					]
					cfg_path = next((p for p in cfg_candidates if p.exists()), None)
					if cfg_path:
						cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
						comps = cfg.get("components", {}) if isinstance(cfg, dict) else {}

						def _get_prompt(comp_id: str, resp_id: str) -> tuple[str | None, list[str] | None]:
							comp = comps.get(comp_id) if isinstance(comps, dict) else None
							if not isinstance(comp, dict):
								return None, None
							for it in comp.get("response", []) or []:
								if not isinstance(it, dict):
									continue
								if str(it.get("id", "")).strip() == resp_id:
									return it.get("prompt"), it.get("options")
							return None, None

						for key, comp_id, resp_id in [
							("global_understanding", "badge-global-comparison", "preferred-condition-global-understanding"),
							("global_presenting", "badge-global-comparison", "preferred-condition-global-presenting"),
							("co2_understanding", "badge-co2-comparison", "preferred-condition-co2-understanding"),
							("co2_presenting", "badge-co2-comparison", "preferred-condition-co2-presenting"),
						]:
							prompt, options = _get_prompt(comp_id, resp_id)
							if prompt:
								prompts[key] = {"prompt": str(prompt), "options": options}
				except Exception:
					prompts = {}

				# Use meaningful labels (not "Stimuli 1/2") for the summary table.
				summary_map = [
					("global_understanding", "Global warming projection — Understanding"),
					("global_presenting", "Global warming projection — Presenting"),
					("co2_understanding", "CO₂ emissions — Understanding"),
					("co2_presenting", "CO₂ emissions — Presenting"),
				]
				for key, label in summary_map:
					choice_col = f"{key}_choice"
					if choice_col not in df_s1b_pref.columns:
						continue
					cnt = _count_choice(choice_col)
					p = prompts.get(key) or {}
					s1b_preference_summary.append(
						{
							"key": key,
							"label": label,
							"prefer_badges": cnt["badges"],
							"no_preference": cnt["no_preference"],
							"prefer_footnotes": cnt["footnotes"],
							"n": cnt["n"],
							"prompt": p.get("prompt"),
							"options": p.get("options"),
						}
					)
	except Exception:
		s1b_followup = None
		s1b_preference_reasons = []
		s1b_preference_summary = []

	context["s1b_followup"] = s1b_followup
	context["s1b_preference_reasons"] = s1b_preference_reasons
	context["s1b_preference_summary"] = s1b_preference_summary

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

	# Participant‑level badge interaction flags (any stimulus)
	participant_hovered_any_badge: dict[str, bool] = {}
	participant_clicked_any_badge: dict[str, bool] = {}
	flags_df_all = getattr(data, "badge_participant_flags", None)
	if flags_df_all is not None and not flags_df_all.empty:
		for _, row_f in flags_df_all.iterrows():
			pid_f = str(row_f.get("participantId", "")).strip()
			if not pid_f:
				continue
			if bool(row_f.get("hoveredAnyBadge")):
				participant_hovered_any_badge[pid_f] = True
			if bool(row_f.get("clickedAnyBadge")):
				participant_clicked_any_badge[pid_f] = True

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
			# Badge‑group only follow‑ups – keep near the top for coherence
			"experience-with-badges": "How badges influenced reading",
			"most-least-useful": "Most and least useful badge",
			# Shared dimensions (same ids in both groups)
			"ease-of-understanding": "Ease of understanding",
			"considered-in-notes": "Use of badges/footnotes during the main task",
			"overall-help": "Overall helpfulness",
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
				is_prolific = participant_is_prolific.get(pid, False)
				disp_id = rid or (pid[:8] if pid else "")
				text = str(row[col])
				# Simple word count for display (aligned with stimulus notes)
				words = len(text.split()) if text else 0
				hovered_any = participant_hovered_any_badge.get(pid, False)
				clicked_any = participant_clicked_any_badge.get(pid, False)
				responses.append(
					{
						"participant": disp_id,
						"isProlific": is_prolific,
						"group": row.get("group_friendly", "Unknown"),
						"text": text,
						"words": int(words),
						"hoveredAnyBadge": hovered_any,
						"clickedAnyBadge": clicked_any,
					}
				)
			# Split responses by group for separate Footnotes/Badges drawers
			foot_responses = [r for r in responses if r.get("group") == "Footnotes"]
			badge_responses = [r for r in responses if r.get("group") == "Badges"]
			other_responses = [r for r in responses if r.get("group") not in {"Footnotes", "Badges"}]

			# If a question was effectively only answered by a single group, make that explicit
			# in the label so the report reflects the study design (e.g., Badges-only follow‑ups).
			groups_with_responses = {r.get("group") for r in responses if r.get("group")}
			if len(groups_with_responses) == 1:
				only_group = next(iter(groups_with_responses))
				label = f"{label} ({only_group} group only)"

			noticed_summary: list[dict] | None = None
			if col == "noticed-in-task":
				# Compact per-group summary table for the noticing question.
				# Fixed option order so that missing categories still appear with (0),
				# but skip groups that were never actually asked this question.
				option_order = [
					"Yes",
					"No",
					"Sometimes (I did not consistently check)",
					"Not sure",
				]
				groups_present = {r.get("group") for r in responses}
				default_order = ["Footnotes", "Badges"]
				groups_order = [g for g in default_order if g in groups_present]
				if not groups_order:
					# Fallback: use whatever groups we saw, or the defaults if empty.
					groups_order = sorted(groups_present) if groups_present else default_order

				noticed_summary = []
				for g in groups_order:
					row_vals: list[dict] = []
					for opt in option_order:
						cnt = sum(
							1
							for r in responses
							if r.get("group") == g and str(r.get("text", "")).strip() == opt
						)
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

		# Optional badge interaction flags per (stimulusId, participantId)
		hover_keys: set[tuple[str, str]] = set()
		click_keys: set[tuple[str, str]] = set()
		flags_df = getattr(data, "badge_participant_flags", None)
		if flags_df is not None and not flags_df.empty:
			for _, row_f in flags_df.iterrows():
				sid = str(row_f.get("stimulusId", "")).strip()
				pid_f = str(row_f.get("participantId", "")).strip()
				if not sid or not pid_f:
					continue
				key = (sid, pid_f)
				if bool(row_f.get("hoveredAnyBadge")):
					hover_keys.add(key)
				if bool(row_f.get("clickedAnyBadge")):
					click_keys.add(key)
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
				is_prolific = participant_is_prolific.get(pid, False)
				disp_id = rid or (pid[:8] if pid else "")
				sid_raw = str(row.get("stimulusId", "")).strip()
				key = (sid_raw, pid) if sid_raw and pid else None
				hovered_any = bool(key and key in hover_keys)
				clicked_any = bool(key and key in click_keys)
				first_stim_raw = participant_first_stimulus.get(pid)
				if first_stim_raw and sid_raw:
					if first_stim_raw == sid_raw:
						stim_order_label = "First"
					else:
						stim_order_label = "Second"
				else:
					stim_order_label = None
				responses.append(
					{
						"participant": disp_id,
						"isProlific": is_prolific,
						"group": row.get("group_friendly", "Unknown"),
						"words": int(row.get("word_count", 0)),
						"text": row.get("speech", ""),
						"hoveredAnyBadge": hovered_any,
						"clickedAnyBadge": clicked_any,
						"stimOrderLabel": stim_order_label,
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


