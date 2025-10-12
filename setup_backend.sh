#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"

if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
pip install -r "${PROJECT_ROOT}/backend/requirements.txt"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

${PYTHON_BIN} -m backend.app.manage migrate

  ${PYTHON_BIN} -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 
  echo "API server started on port 8000"

