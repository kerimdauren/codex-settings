#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${1:-}" == "--background" ]]; then
    nohup "$0" --once >/dev/null 2>&1 &
    exit 0
fi

if [[ "${1:-}" != "" && "${1:-}" != "--once" ]]; then
    echo "usage: $0 [--once|--background]" >&2
    exit 2
fi

export GIT_TERMINAL_PROMPT=0
codex_home="${CODEX_HOME:-$HOME/.codex}"
ai_checkout="${CODEX_AI_ROOT:-$HOME/ai}"
settings_checkout="${CODEX_SETTINGS_CHECKOUT:-$HOME/.local/share/codex-settings}"
runtime_dir="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
lock_dir="$runtime_dir/codex-github-sync.lock.d"

if ! mkdir "$lock_dir" 2>/dev/null; then
    echo "sync already running; skipping"
    exit 0
fi
trap 'rmdir "$lock_dir" 2>/dev/null || true' EXIT

sync_ai() {
    if [[ ! -d "$ai_checkout/.git" ]]; then
        echo "ai checkout missing; cloning"
        git clone git@github.com:kerimdauren/ai.git "$ai_checkout"
        return
    fi

    if [[ -n "$(git -C "$ai_checkout" status --porcelain)" ]]; then
        echo "ai has local changes; skipping update"
        return
    fi

    echo "updating ai"
    git -C "$ai_checkout" pull --ff-only
}

apply_codex_settings() {
    mkdir -p "$codex_home/rules" "$codex_home/scripts" "$codex_home/skills"
    cp "$settings_checkout/AGENTS.md" \
       "$settings_checkout/SETUP.md" \
       "$settings_checkout/hooks.json" \
       "$settings_checkout/shared.config.toml" \
       "$codex_home/"
    cp -a "$settings_checkout/rules/." "$codex_home/rules/"
    cp -a "$settings_checkout/skills/." "$codex_home/skills/"
    find "$settings_checkout/scripts" -maxdepth 1 -type f \
        ! -name 'sync-github-settings.sh' -exec cp {} "$codex_home/scripts/" \;
    CODEX_SKIP_AUTOSYNC_INSTALL=1 "$settings_checkout/scripts/bootstrap-unix.sh"
    python3 "$settings_checkout/scripts/doctor.py" --mark-complete
    cp "$settings_checkout/scripts/sync-github-settings.sh" "$codex_home/scripts/"
    chmod 755 "$codex_home/scripts/sync-github-settings.sh"
}

sync_codex_settings() {
    local before="" after marker
    marker="$codex_home/.settings-sync-complete"

    if [[ ! -d "$settings_checkout/.git" ]]; then
        echo "codex-settings checkout missing; cloning"
        mkdir -p "$(dirname "$settings_checkout")"
        git clone git@github.com:kerimdauren/codex-settings.git "$settings_checkout"
    else
        before="$(git -C "$settings_checkout" rev-parse HEAD)"
        if [[ -n "$(git -C "$settings_checkout" status --porcelain)" ]]; then
            echo "codex-settings has local changes; skipping update"
            return
        fi
        echo "updating codex-settings"
        git -C "$settings_checkout" pull --ff-only
    fi

    after="$(git -C "$settings_checkout" rev-parse HEAD)"
    if [[ "$before" == "$after" && -f "$marker" ]] && \
       [[ "$(sed -n '1p' "$marker")" == "$after" ]]; then
        echo "codex-settings unchanged"
        return
    fi

    echo "applying codex-settings at $after"
    apply_codex_settings
    printf '%s\n' "$after" >"$marker"
}

sync_ai
sync_codex_settings
