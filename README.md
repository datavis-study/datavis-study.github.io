
## Run (web)

```bash
yarn install
yarn serve
# http://localhost:8080
```

## Exports (analysis)

From `analysis/`:

```bash
# Run all exports and archive data
mtb-export-all

# Individual exports
mtb-export-participants      # participants.csv
mtb-export-time              # participant_time_per_component.csv
mtb-export-notes             # stimulus_notes.csv
mtb-export-likert            # questionnaire_likert_scores.csv
mtb-export-open              # questionnaire_open_responses.csv
mtb-export-badges            # stimulus_badge_metrics.csv
```

- Input JSON: `analysis/input/db.json`
- Output CSVs: `analysis/input/`
- Archives: `analysis/archive/study-data-YYYY-MM-DD_HH-MM-SS.zip`

## License

MIT
