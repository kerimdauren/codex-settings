#!/usr/bin/env bash
set -Eeuo pipefail

codex_home="${CODEX_HOME:-$HOME/.codex}"
source_script="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/sync-github-settings.sh"
target_script="$codex_home/scripts/sync-github-settings.sh"
mkdir -p "$codex_home/scripts"
cp "$source_script" "$target_script"
chmod 755 "$target_script"

case "$(uname -s)" in
    Linux)
        unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
        mkdir -p "$unit_dir"
        cat >"$unit_dir/codex-github-sync.service" <<EOF
[Unit]
Description=Synchronize AI and Codex settings from GitHub
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$target_script --once
EOF
        cat >"$unit_dir/codex-github-sync.timer" <<'EOF'
[Unit]
Description=Check GitHub repositories for Codex updates

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
RandomizedDelaySec=30s
Persistent=true
Unit=codex-github-sync.service

[Install]
WantedBy=timers.target
EOF
        systemctl --user daemon-reload
        systemctl --user enable --now codex-github-sync.timer
        ;;
    Darwin)
        agent_dir="$HOME/Library/LaunchAgents"
        agent="$agent_dir/com.kerimdauren.codex-github-sync.plist"
        mkdir -p "$agent_dir"
        cat >"$agent" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.kerimdauren.codex-github-sync</string>
  <key>ProgramArguments</key>
  <array><string>$target_script</string><string>--once</string></array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>300</integer>
  <key>ProcessType</key><string>Background</string>
</dict>
</plist>
EOF
        launchctl bootout "gui/$(id -u)" "$agent" 2>/dev/null || true
        launchctl bootstrap "gui/$(id -u)" "$agent"
        ;;
    *)
        echo "unsupported platform: $(uname -s)" >&2
        exit 1
        ;;
esac

echo "Installed automatic GitHub synchronization"
