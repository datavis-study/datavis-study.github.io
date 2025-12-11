#!/usr/bin/env bash

set -euo pipefail

# Simple helper to export both s1b pilot JSON files to CSV.
# Usage (from repo root or from the analysis directory):
#   ./analysis/export_s1b_pilots.sh
#
# It will create:
#   analysis/data/s1b/s1b-badges_all.csv
#   analysis/data/s1b/s1b-footnotes_all.csv

# Resolve script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}/analysis"

echo "Exporting s1b-badges pilot to CSV..."
python3 -m src.data_prep.export_s1b_pilots "data/s1b/s1b-badges_all.json"

echo "Exporting s1b-footnotes pilot to CSV..."
python3 -m src.data_prep.export_s1b_pilots "data/s1b/s1b-footnotes_all.json"

echo "Exporting quick_reminder CSV (both groups combined)..."
python3 -m src.data_prep.export_s1b_quick_reminder

echo "Exporting preferences CSV (both groups combined)..."
python3 -m src.data_prep.export_s1b_preferences

echo "Exporting Likert CSV (both groups combined)..."
python3 -m src.data_prep.export_s1b_likert

echo "Done. CSV files are in analysis/data/s1b/."

