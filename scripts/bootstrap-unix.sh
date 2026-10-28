#!/usr/bin/env sh
set -eu

if [ "${1:-}" = "--workspace" ]; then
    shift
    export PATH="$HOME/.local/bin:$PATH"
    if [ "$(uname -s)" = "Darwin" ] && ! command -v brew >/dev/null 2>&1; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ -x /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
    if ! command -v uv >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    if ! command -v git >/dev/null 2>&1; then
        if command -v brew >/dev/null 2>&1; then
            brew install git
        elif command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update
            sudo apt-get install -y git
        else
            echo "Install Git, then rerun this command." >&2
            exit 1
        fi
    fi
    exec uv run --script https://raw.githubusercontent.com/kerimdauren/codex-settings/main/scripts/workspace.py setup "$@"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
uv run --script "$SCRIPT_DIR/bootstrap.py"

if [ "${CODEX_SKIP_AUTOSYNC_INSTALL:-0}" != "1" ]; then
    exec "$SCRIPT_DIR/install-autosync.sh"
fi
