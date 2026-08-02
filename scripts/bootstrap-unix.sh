#!/usr/bin/env sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
uv run --script "$SCRIPT_DIR/bootstrap.py"

if [ "${CODEX_SKIP_AUTOSYNC_INSTALL:-0}" != "1" ]; then
    exec "$SCRIPT_DIR/install-autosync.sh"
fi
