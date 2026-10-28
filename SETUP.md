# Codex Initial Platform Setup

## Portable workspace: Git + Google Drive + Bitwarden Free

Global settings stay in `codex-settings`. Project instructions, context, rules,
memories, documents, and project skills stay in a private Google Drive folder.
Code stays in its original Git repositories. Env values stay in Bitwarden
Password Manager secure notes; file attachments and Premium are not required.
Existing global customizations are kept when the shared file has not changed.
Changes on both sides are merged against the prior installed version; conflicts
stop setup without overwriting the local file.

The real `workspace.toml` catalog belongs in the private Drive folder, **not in
this public Git repository**. It contains repository URLs, relative paths, and
Bitwarden note names or IDs, but no secret values. `workspace.example.toml` is
an example only. Default workspace: `~/ai`; override with `CODEX_AI_ROOT`.

### New computer: one command

macOS or Debian/Ubuntu, in an interactive Bash or Zsh terminal:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/kerimdauren/codex-settings/main/scripts/bootstrap-unix.sh) --workspace
```

Windows, in PowerShell:

```powershell
& ([scriptblock]::Create((Invoke-RestMethod https://raw.githubusercontent.com/kerimdauren/codex-settings/main/scripts/bootstrap-windows.ps1))) -Workspace
```

These entry points install missing prerequisites through Homebrew, apt/npm,
winget, and the official uv/rclone installers. Linux keeps a current Node runtime
for Bitwarden under `~/.codex/tools`. Other Linux distributions need Git, uv,
rclone, and Bitwarden CLI (`bw`) installed first. macOS Homebrew and system
package installation can ask for your OS password. Codex is assumed installed;
authenticate Codex on each computer separately when needed.

The default Drive location is `codex-projects:Codex Projects`. Set
`CODEX_DRIVE_REMOTE` before setup if your folder differs. The script opens the
Google authorization page when the rclone remote does not exist. This creates
a machine-local rclone login, independent of the Drive plugin in Codex.

The command downloads and validates the private catalog, applies global
settings, clones/updates its code repositories, synchronizes material, and
restores the selected env files after Bitwarden login/unlock. Git credentials,
SSH keys, VPN access, and Bitwarden 2FA may require your participation. Enter
credentials only in the terminal or provider login UI, never in chat.

After success, material, global settings, and clean Git checkouts synchronize
every five minutes (LaunchAgent, systemd user timer, or Windows scheduled task).
Codex session startup also requests a background sync. The old `ai` Git sync
is bypassed in workspace mode, so it does not compete with Drive for context.
Uncommitted code is kept locally and is not transferred to another computer.
If the workspace root itself is a code repository, list it with `path = "."`
before nested repositories. A new clone uses sparse checkout to leave material
paths to Drive. Root Git status checks exclude those material paths; Git still
refuses a pull that would overwrite changed tracked files.

### First migration on the source computer

1. Review a private copy of `workspace.example.toml`, listing only the material
   paths, code repositories, and env files you want to transfer. Paths are
   relative to `CODEX_AI_ROOT`; repository URLs must not contain credentials.
2. Create your Bitwarden Free account. Select the correct server in the catalog:
   `https://vault.bitwarden.com` or `https://vault.bitwarden.eu`.
3. Preview without contacting Git, Drive, or Bitwarden:

   ```bash
   uv run --script scripts/workspace.py setup --manifest /path/to/private/workspace.toml --dry-run
   ```

4. Run the initial migration from this settings checkout:

   ```bash
   uv run --script scripts/workspace.py setup --manifest /path/to/private/workspace.toml --import-envs
   ```

The first run uploads the private catalog only if the cloud copy does not
already differ. It creates missing Bitwarden secure notes from **only** the
listed local env files. Existing notes are kept. Without `--import-envs`, notes
must already exist. Choose a unique exact note name or, preferably, its item ID.

The private Drive catalog is the source of truth after migration. Download a
copy before editing it and upload the reviewed update to that same location.
Local settings/configuration/state files are not added to the public repo.

### Sync and env refresh

```bash
uv run --script ~/.codex/scripts/workspace.py sync
uv run --script ~/.codex/scripts/workspace.py env
```

Background sync never logs into or unlocks Bitwarden. It never rewrites envs.
The explicit `env` command fetches the selected notes. If a local env differs,
it is kept; pass `--refresh-envs` to explicitly replace it. Generated envs are
excluded through Git's local `info/exclude` and restricted to owner access on
Unix. Windows uses the account's existing filesystem ACLs. Tracked env targets
are rejected, even with `--refresh-envs`; resolve their Git tracking first.

Drive sync uses an allowlist and excludes env files, common credential/key
files, code working trees outside that allowlist, Git metadata, caches, and
temporary secret-write directories. Review project prose before the initial
upload: filename filters cannot detect credentials pasted into a Markdown file.
Use ordinary uploaded files for portable material; native Google Docs are
skipped to avoid converting editable source files during synchronization.

Initial sync checks common files and stops if their contents differ. Later
conflicts retain both versions with `.conflict` names and report incomplete
sync. Replaced/deleted material is backed up locally under
`~/.codex/workspace-state/drive-backups` and in a sibling Drive folder ending
in `.backups`. Backups are not automatically pruned. Do not edit the same file
on two devices during a sync: the devices have separate local locks, not a
distributed transaction. Wait for sync before switching devices.

If rclone requires a new baseline after an interrupted run, reconcile the
local and Drive copies and keep backups first. Then move the affected
`~/.codex/workspace-state/drive/<identity>` directory aside and rerun `setup`.
The initial content check still applies; background sync never forces a resync.

Existing repository instructions are preserved. Repositories without their
own `AGENTS.md` receive a Git-ignored pointer to the shared project instructions.
Shared rules and skills resolve from the project folder. This restores files
and guidance; it does not copy app SQLite state, sidebar layout, sessions,
device credentials, or plugin runtimes. Open the restored folders as projects
in Codex and authorize plugins separately where needed.

Validation:

```bash
uv run --with tomlkit python -m unittest discover -s scripts -p 'test_*.py'
```

The rclone tests use two temporary local folders, including conflicts and secret
exclusions. They do not establish acceptance against a real Drive account,
Bitwarden vault, or a fresh Windows/Linux computer.

## Existing platform-only setup

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

Keep project-specific skills in the project `.agents/skills/`, outside the shared
`skills/` synchronization source. Keep only user-managed skills in that source;
Codex manages `skills/.system/`, which must not be tracked or synchronized.
Biometry skills are maintained only under
`beeline/biometry-3.0/.agents/skills/` in the `ai` checkout. Synchronization copies
files but does not delete old installed copies; when migrating an existing
machine, remove only the reviewed obsolete global copies after verifying the
project versions are available.

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
- hooks and `rules/default.rules` are valid;
- `rm` is forbidden;
- no paths from another operating system remain active.

When all required checks pass, create the local completion marker:

```bash
uv run --script ~/.codex/scripts/doctor.py --mark-complete
```

The marker is machine-local and must not be committed.
