# Codex Initial Platform Setup

Use this workflow when `.setup-complete` is absent or when the user requests a platform setup audit.

## Safety

- Run diagnostics before changing the machine.
- Present the proposed work and obtain user approval before installing software, authenticating, or changing configuration.
- Never copy `auth.json`, sessions, logs, SQLite files, caches, plugin runtimes, or another machine's local `config.toml`.
- Keep the trusted workspace limited to the platform-specific absolute path for the user's `ai` directory.

## 1. Detect

Determine:

- operating system and architecture;
- home directory, `CODEX_HOME`, and `CODEX_AI_ROOT`;
- available shell and package manager;
- presence of Codex, Git, `uv`, `uvx`, Python, and Node.js;
- Codex login state;
- local and shared configuration state;
- MCP availability, hooks, command rules, and trusted projects;
- paths or integrations copied from an incompatible operating system.

Run the diagnostic tool when Python 3.11+ is available:

```bash
python3 ~/.codex/scripts/doctor.py --json
```

With `uv`:

```bash
uv run --script ~/.codex/scripts/doctor.py --json
```

On Windows PowerShell:

```powershell
py -3.11 $HOME\.codex\scripts\doctor.py --json
```

If Python is unavailable, inspect the same items with platform-native commands and include Python or `uv` installation in the proposed plan.

## 2. Plan

Present a checklist grouped as:

- detected and ready;
- required and missing;
- optional and missing;
- incompatible with the current platform;
- actions requiring user approval.

Do not continue until the user approves the plan.

## 3. Configure

After approval, install missing prerequisites and apply the shared configuration.

macOS or Linux:

```bash
~/.codex/scripts/bootstrap-unix.sh
```

On Linux this also installs a user systemd timer. On macOS it installs a
LaunchAgent. Both check the `ai` and `codex-settings` repositories every five
minutes. The session-start hook also starts a non-blocking check whenever Codex
starts. Repositories with local changes are never reset or overwritten.

Windows PowerShell:

```powershell
& $HOME\.codex\scripts\bootstrap-windows.ps1
```

Authenticate independently on each machine when required:

```bash
codex login
```

## 4. Verify

Run diagnostics again. Verify that:

- the shared settings are present in the local `config.toml`;
- exactly one trusted project exists and points to the local `ai` directory;
- `code-review-graph` is listed by `codex mcp list`;
- hooks and `rules/default.rules` are valid;
- `rm` is forbidden;
- no paths from another operating system remain active.

When all required checks pass, create the local completion marker:

```bash
uv run --script ~/.codex/scripts/doctor.py --mark-complete
```

The marker is machine-local and must not be committed.
