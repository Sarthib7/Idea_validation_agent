#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv313/bin/python"
RUN_HOME="$SCRIPT_DIR/.run-home"
LOCAL_MASUMI="$SCRIPT_DIR/../../pip-masumi"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Missing .venv313/bin/python. Create the Python 3.13 virtualenv first." >&2
  exit 1
fi

mkdir -p "$RUN_HOME"
export HOME="$RUN_HOME"

if [ -f "$LOCAL_MASUMI/masumi/__init__.py" ]; then
  export PYTHONPATH="$LOCAL_MASUMI${PYTHONPATH:+:$PYTHONPATH}"
fi

exec "$VENV_PYTHON" -m masumi run "$@"
