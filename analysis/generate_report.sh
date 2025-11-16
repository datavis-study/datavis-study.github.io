#!/usr/bin/env bash
set -euo pipefail

# Simple helper to generate the study report.
# Defaults:
#   --data-dir:   ./data
#   --out-dir:    ./reports
#
# Usage examples:
#   ./generate_report.sh
#   ./generate_report.sh --data-dir path/to/data --out-dir path/to/reports --md notes.md

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
		# Install this package in editable mode to get CLI deps
		"$VENV_PY" -m pip install -e "${SCRIPT_DIR}"
	fi
}

# If matplotlib isn't available in the current Python, fall back to the venv
if ! "$PYTHON_BIN" -c 'import matplotlib' >/dev/null 2>&1; then
	ensure_venv
	PYTHON_BIN="$VENV_PY"
fi
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

mkdir -p "$OUT_DIR_DEFAULT"

exec "$PYTHON_BIN" -m reporting.generate_report "${ARGS[@]-}"


