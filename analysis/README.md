## Automated reporting (Markdown) for Mind the Badge

This project includes a simple, reproducible way to generate a timestamped Markdown report from the exported CSVs.

### Install

- Ensure Python 3.10+ is available.
- From the repo root:

```bash
pip install -e .
```

This installs the `mtb-generate-report` CLI and required Python packages.

### Generate a report

From the repo root:

```bash
python -m tools.reporting.generate_report --data-dir data --out-dir reports --md report.md
```

Outputs to a new folder like `reports/report_YYYYMMDD-HHMMSS/` with:
- `report.md`: the report (Markdown)
- `figures/`: generated figures (PNG)

Options:
- `--data-dir`: directory containing the CSVs (default: `data`)
- `--out-dir`: directory to write the report (default: `reports`)
- `--run-id`: optional custom id for the output folder
- `--md`: path to a Markdown file to include as narrative (can be passed multiple times)

### What’s included in the report

- Participant counts by group (if `participants.csv` present)
- Time-on-task distributions for `global-warming-projection (s)`, `co2-emissions (s)`, `total (s)` (if `participant_time_per_component.csv` present)
- Badge attention ranking by total hover time (if `stimulus_badge_metrics.csv` present)
- Likert mean scores by dimension and group (if `questionnaire_likert_scores.csv` present)
- Notes word counts by group × stimulus (if `stimulus_notes.csv` present)

Missing inputs are handled gracefully; corresponding figures are skipped.

### Add Markdown narrative (editable text)

You can write the report text in Markdown and include it into the HTML output. A sample file is provided at `report.md`.

Generate a report with Markdown:

```bash
mtb-generate-report --data-dir data --out-dir reports --md report.md
```

You can pass multiple `--md` files; they will be concatenated in order.

The Markdown supports simple templating (Jinja2) with these context variables:
- `participants_count`: integer
- `group_counts`: list of objects with `group`, `n_participants`
- `data_dir`, `out_dir`, `run_id`, `generated_at`
- `figures`: list of objects with `name`, `filename`, `path`
Example inside `report.md`:

```markdown
We analyzed {{ participants_count }} participants.
{% for gc in group_counts %}- {{ gc.group }}: {{ gc.n_participants }}{% endfor %}
```

### PDF reports (optional)

This setup generates a Markdown report. For PDF, use your editor/Markdown viewer’s “Export to PDF”, or we can add Quarto/Pandoc export in a follow-up.

### Updating with new data
Drop new CSVs into `data/` (same filenames), then rerun the CLI. A fresh timestamped report will be created without touching previous runs.

### Minimal R-based charts (experimental)

If you prefer to experiment with R for chart creation while keeping the existing Python pipeline intact, there is a small R pipeline composed of:
- A **single main wrapper** at `analysis/r_charts.R`.
- One **per-chart script** at `analysis/r_scripts/likert_mean_chart.R` (for now).

- **Dependencies**: R with `readr`, `dplyr`, `tidyr`, and `ggplot2` installed.
- **Default behavior**: Reads CSVs from `analysis/data` and writes PNG charts to `analysis/r_output/`.

From the repo root:

```bash
Rscript analysis/r_charts.R
```

You can also override the input data directory and output directory:

```bash
Rscript analysis/r_charts.R path/to/data path/to/output
```

Currently, the main wrapper internally calls the Likert script to generate:
- A **Likert mean scores by group and dimension** chart from `questionnaire_likert_scores.csv` (if present).

This does not modify the Python report generation or file layout; it only reads the existing CSVs and writes additional figures.


