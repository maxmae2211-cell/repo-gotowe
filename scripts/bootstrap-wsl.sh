#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_VENV_DIR="${HOME}/.venv-wsl-k6"
VENV_DIR="${VENV_DIR:-${DEFAULT_VENV_DIR}}"
BZT_ARTIFACTS_DIR="${BZT_ARTIFACTS_DIR:-${HOME}/bzt-artifacts}"
BZT_RC_FILE="${HOME}/.bzt-rc"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() {
  echo "[bootstrap-wsl] $*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

configure_bzt_artifacts_dir() {
  local rc_file="$1"
  local artifacts_dir="$2"
  local tmp_file

  mkdir -p "${artifacts_dir}"

  if [ ! -f "${rc_file}" ]; then
    cat > "${rc_file}" <<EOF
settings:
  artifacts-dir: ${artifacts_dir}
EOF
    log "Configured Taurus artifacts dir in ${rc_file}: ${artifacts_dir}"
    return
  fi

  if grep -Eq '^[[:space:]]*artifacts-dir:' "${rc_file}"; then
    log "Taurus artifacts dir already configured in ${rc_file}"
    return
  fi

  if grep -Eq '^settings:[[:space:]]*$' "${rc_file}"; then
    tmp_file="$(mktemp)"
    awk -v dir="${artifacts_dir}" '
      { print }
      /^settings:[[:space:]]*$/ && !inserted {
        print "  artifacts-dir: " dir
        inserted=1
      }
    ' "${rc_file}" > "${tmp_file}"
    mv "${tmp_file}" "${rc_file}"
  else
    {
      echo
      echo "settings:"
      echo "  artifacts-dir: ${artifacts_dir}"
    } >> "${rc_file}"
  fi

  log "Configured Taurus artifacts dir in ${rc_file}: ${artifacts_dir}"
}

log "Project directory: ${PROJECT_DIR}"

if ! command -v apt-get >/dev/null 2>&1; then
  log "This script currently supports Debian/Ubuntu (apt-get)."
  log "Install equivalents manually and rerun."
  exit 1
fi

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
fi

log "Installing system dependencies (python headers + build tools)..."
${SUDO} apt-get update
${SUDO} apt-get install -y \
  build-essential \
  gcc \
  g++ \
  make \
  libev-dev \
  libffi-dev \
  python3 \
  python3-venv \
  python3-dev

cd "${PROJECT_DIR}"

require_cmd "${PYTHON_BIN}"

configure_bzt_artifacts_dir "${BZT_RC_FILE}" "${BZT_ARTIFACTS_DIR}"

if [[ "${VENV_DIR}" != /* ]]; then
  VENV_DIR="${PROJECT_DIR}/${VENV_DIR}"
fi

if [ -d "${VENV_DIR}" ] && [ ! -f "${VENV_DIR}/bin/activate" ]; then
  log "Detected incomplete virtual environment, recreating: ${VENV_DIR}"
  rm -rf "${VENV_DIR}"
fi

if [ ! -d "${VENV_DIR}" ]; then
  log "Creating virtual environment: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  log "Virtual environment already exists: ${VENV_DIR}"
fi

if [ ! -f "${VENV_DIR}/bin/activate" ]; then
  log "Virtual environment is invalid: missing ${VENV_DIR}/bin/activate"
  log "Try rerunning with: VENV_DIR=/home/${USER}/.venv-wsl-k6 ./scripts/bootstrap-wsl.sh"
  exit 1
fi

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

log "Upgrading pip tooling..."
python -m pip install --upgrade pip setuptools wheel

log "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

log "Verifying Taurus installation..."
if command -v bzt >/dev/null 2>&1; then
  if bzt -h >/dev/null 2>&1; then
    python -c "import bzt; print('Taurus version:', getattr(bzt, 'VERSION', 'unknown'))"
  else
    log "bzt is installed but help command failed"
    exit 1
  fi
else
  log "bzt command not found after installation."
  log "Try: python -m pip install bzt"
  exit 1
fi

log "Bootstrap complete."
log "Activate env with: source ${VENV_DIR}/bin/activate"
log "Run tests with: bzt taurus-k6.yml"
