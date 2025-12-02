#!/usr/bin/env bash

set -euo pipefail

# Root of the project (this script is assumed to live in the project root)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-stimuli"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[stimuli] Using project root: ${ROOT_DIR}"
echo "[stimuli] Using virtualenv:   ${VENV_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "[stimuli] Creating virtual environment..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "[stimuli] Activating virtual environment..."
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "[stimuli] Upgrading pip..."
pip install --upgrade pip >/dev/null

echo "[stimuli] Installing required Python packages (matplotlib, seaborn)..."
pip install matplotlib seaborn >/dev/null

echo "[stimuli] Generating Experiment 2 stimuli..."
python3 "${ROOT_DIR}/public/mind-the-badge-experiment-2/generate_stimuli.py"

echo "[stimuli] Done."


