
## Run (web)


 
```bash
yarn install
yarn serve
# http://localhost:8080
```

## Exports (analysis)

From `analysis/`:

```bash
cd analysis

# 1) Create & activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\\Scripts\\activate

# 2) Install the CLI in editable mode to get console scripts
python -m pip install -e .

# 3) Run all exports and archive data
mtb-export-all

# Individual exports
mtb-export-participants      # participants.csv
mtb-export-time              # participant_time_per_component.csv
mtb-export-notes             # stimulus_notes.csv
mtb-export-likert            # questionnaire_likert_scores.csv
mtb-export-open              # questionnaire_open_responses.csv
mtb-export-badges            # stimulus_badge_metrics.csv
```

- Input JSON: `analysis/data/db.json`
- Output CSVs: `analysis/data/`
- Archives: `analysis/archive/study-data-YYYY-MM-DD_HH-MM-SS.zip`

Run without installing (fallback):

```bash
# from repo root, run without installing console scripts
PYTHONPATH=analysis/src \
python -c "from mtb import main_run_all; main_run_all()"
```

## License

MIT
