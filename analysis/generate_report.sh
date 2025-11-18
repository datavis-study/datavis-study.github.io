#!/usr/bin/env bash
set -euo pipefail

# Simple helper to generate the study report.
# Defaults:
#   --data-dir:       ./data
#   --out-dir:        ./reports
#   --skip-dataprep:  skip running the data export pipeline before report generation
#
# Usage examples:
#   ./generate_report.sh
#   ./generate_report.sh --data-dir path/to/data --out-dir path/to/reports --md notes.md
#   ./generate_report.sh --skip-dataprep  # reuse already-exported CSVs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# Pick a Python
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
	PYTHON_BIN=python
fi

# Ensure local src/ is on the module path
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH:-}"

DATA_DIR_DEFAULT="${SCRIPT_DIR}/data"
OUT_DIR_DEFAULT="${SCRIPT_DIR}/reports"

# Ensure ARGS is always defined (safe with set -u)
declare -a ARGS=()
if [ "$#" -gt 0 ]; then
	ARGS=("$@")
fi

# Optional local virtualenv bootstrap if dependencies are missing
VENV_DIR="${SCRIPT_DIR}/.venv"
VENV_PY="${VENV_DIR}/bin/python"

ensure_venv() {
	if [ ! -x "$VENV_PY" ]; then
		echo "Creating virtual environment at ${VENV_DIR}..."
		"$PYTHON_BIN" -m venv "$VENV_DIR"
		"$VENV_PY" -m pip install --upgrade pip setuptools wheel
	fi
	# (Re)install this package in editable mode to pick up any new dependencies
	"$VENV_PY" -m pip install -e "${SCRIPT_DIR}"
}

has_arg() {
	local term="$1"
	shift || true
	for a in "$@"; do
		if [[ "$a" == "$term" ]]; then
			return 0
		fi
	done
	return 1
}

# If required analysis deps (Altair) aren't available, fall back to the managed venv
if ! "$PYTHON_BIN" -c 'import altair' >/dev/null 2>&1; then
	ensure_venv
	PYTHON_BIN="$VENV_PY"
fi

# Handle optional --skip-dataprep flag (shell-only; not forwarded to Python)
RUN_DATAPREP=1
if has_arg "--skip-dataprep" "${ARGS[@]-}"; then
	RUN_DATAPREP=0
	# Remove the flag from ARGS so it isn't passed to the Python CLI
	declare -a tmp_args=()
	for a in "${ARGS[@]}"; do
		if [[ "$a" == "--skip-dataprep" ]]; then
			continue
		fi
		tmp_args+=("$a")
	done
	if ((${#tmp_args[@]} > 0)); then
		ARGS=("${tmp_args[@]}")
	else
		ARGS=()
	fi
fi

if ! has_arg "--data-dir" "${ARGS[@]-}"; then
	ARGS+=("--data-dir" "$DATA_DIR_DEFAULT")
fi
if ! has_arg "--out-dir" "${ARGS[@]-}"; then
	ARGS+=("--out-dir" "$OUT_DIR_DEFAULT")
fi
# If no --md was passed, include the default template when present
if ! has_arg "--md" "${ARGS[@]-}"; then
	NEW_MD="${SCRIPT_DIR}/src/reporting/templates/report.md"
	LEGACY_MD="${SCRIPT_DIR}/report.md"
	if [ -f "$NEW_MD" ]; then
		ARGS+=("--md" "$NEW_MD")
	elif [ -f "$LEGACY_MD" ]; then
		ARGS+=("--md" "$LEGACY_MD")
	fi
fi

# Run full data preparation pipeline before report generation (unless skipped)
if [ "$RUN_DATAPREP" -eq 1 ]; then
	echo "Exporting study data (participants, time, questionnaires, notes, badges)..."
	"$PYTHON_BIN" -m data_prep.export_participant_meta >/dev/null
	"$PYTHON_BIN" -m data_prep.export_time_spent >/dev/null
	"$PYTHON_BIN" -m data_prep.export_questionnaire_likert >/dev/null
	"$PYTHON_BIN" -m data_prep.export_questionnaire_open >/dev/null
	"$PYTHON_BIN" -m data_prep.export_speech >/dev/null
	"$PYTHON_BIN" -m data_prep.export_badge_stats >/dev/null
	"$PYTHON_BIN" -m data_prep.export_demographics >/dev/null
else
	echo "Skipping data preparation (per --skip-dataprep); using existing CSV exports."
fi

mkdir -p "$OUT_DIR_DEFAULT"

exec "$PYTHON_BIN" -m reporting.generate_report "${ARGS[@]}"


