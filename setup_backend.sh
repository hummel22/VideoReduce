#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
FRONTEND_BUILD_DIR="${PROJECT_ROOT}/backend/app/static/frontend"

if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
pip install -r "${PROJECT_ROOT}/backend/requirements.txt"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

if command -v npm >/dev/null 2>&1 && [ -f "${FRONTEND_DIR}/package.json" ]; then
  pushd "${FRONTEND_DIR}" >/dev/null
  npm install
  npm run build
  popd >/dev/null
  rm -rf "${FRONTEND_BUILD_DIR}"
  mkdir -p "${FRONTEND_BUILD_DIR}"
  cp -a "${FRONTEND_DIR}/dist/." "${FRONTEND_BUILD_DIR}/"
else
  echo "Skipping frontend build. npm is not available in PATH." >&2
fi

${PYTHON_BIN} -m backend.app.manage migrate

${PYTHON_BIN} -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8005 
echo "API server started on port 8000"

