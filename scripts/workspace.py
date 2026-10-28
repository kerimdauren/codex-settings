# /// script
# requires-python = ">=3.11"
# ///
"""Restore portable Codex settings, project material, Git checkouts, and env files."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

SETTINGS_URL = "https://github.com/kerimdauren/codex-settings.git"
EXCLUDED_DIRS = {
    ".git", ".worktrees", "worktrees", "node_modules", ".venv", "venv",
    "__pycache__", ".cache", "temp", "tmp", ".archify",
}
ENV_NAMES = {".env", ".env.local", ".env.dev", ".env.development", ".env.test",
             ".env.prod", ".env.production", ".env.staging"}


def run(command, *, allowed=(0,), env=None, input=None):
    result = subprocess.run(command, capture_output=True, text=True, env=env, input=input)
    if result.returncode not in allowed:
        # Provider output can contain tokens, vault items, or credential-bearing URLs.
        raise RuntimeError(f"{Path(command[0]).name} {command[1]} failed (exit {result.returncode}); output withheld")
    return result


def location(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if (not relative or parts.is_absolute() or ".." in parts.parts
            or re.search(r"[\\\n\r:*?\[\]{}]", relative)):
        raise ValueError("Workspace paths must be relative, without traversal or glob characters")
    target = root / relative
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Workspace path escapes its root")
    return target


def read_manifest(path: Path, root: Path):
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    if config.get("version") != 1:
        raise ValueError("Unsupported workspace manifest version")
    for item in config.get("materials", []):
        target = location(root, item)
        if target.name not in {"AGENTS.md", "AGENTS.override.md", "context", "docs", "rules", "memories"} and not item.endswith("/.agents/skills"):
            raise ValueError("Only project instructions, context, docs, rules, memories, and .agents/skills belong in Drive")
    for repo in config.get("repositories", []):
        location(root, repo["path"])
        validate_git_url(repo["url"])
        if repo.get("project"):
            project = location(root, repo["project"])
            if not location(root, repo["path"]).is_relative_to(project):
                raise ValueError("Repository must be inside its project")
    for item in config.get("envs", []):
        target = location(root, item["path"])
        if target.name not in ENV_NAMES:
            raise ValueError("Env targets must use a supported .env filename")
        if not item.get("item") or "\n" in item["item"]:
            raise ValueError("Every env needs a Bitwarden item ID or exact name")
    server = config["bitwarden"]["server"]
    if server not in {"https://vault.bitwarden.com", "https://vault.bitwarden.eu"}:
        raise ValueError("Choose the Bitwarden US or EU server")
    if not re.fullmatch(r"[A-Za-z0-9_-]+:.+", config["drive"]["remote"]):
        raise ValueError("Drive remote must use remote-name:folder format")
    return config


def validate_git_url(url: str):
    if url.startswith(("https://", "ssh://")):
        parsed = urlsplit(url)
        if parsed.password or (parsed.scheme == "https" and parsed.username):
            raise ValueError("Git URLs must not contain credentials")
        if not parsed.hostname or parsed.query or parsed.fragment:
            raise ValueError("Invalid Git remote URL")
    elif not re.fullmatch(r"[\w.-]+@[\w.-]+:[\w./-]+", url):
        raise ValueError("Use an HTTPS or SSH Git URL without credentials")


def repo_identity(url: str) -> str:
    if "://" in url:
        parsed = urlsplit(url)
        return f"{parsed.hostname}:{parsed.path.lstrip('/').removesuffix('.git')}"
    return url.split("@", 1)[-1].removesuffix(".git")


def sync_repo(path: Path, url: str, *, materials=()):
    validate_git_url(url)
    git_env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    if not path.exists() or not any(path.iterdir()):
        path.parent.mkdir(parents=True, exist_ok=True)
        command = ["git", "clone"]
        if materials:
            command.append("--no-checkout")
        run([*command, "--", url, str(path)], env=git_env)
        if materials:
            patterns = "/*\n" + "".join(f"!/{item}\n" for item in materials)
            run(["git", "-C", str(path), "sparse-checkout", "set", "--no-cone", "--stdin"], input=patterns)
            run(["git", "-C", str(path), "checkout"])
        return
    if not (path / ".git").exists():
        raise RuntimeError(f"Refusing to clone into an existing non-repository: {path}")
    origin = run(["git", "-C", str(path), "config", "--get", "remote.origin.url"]).stdout.strip()
    if repo_identity(origin) != repo_identity(url):
        raise RuntimeError(f"Repository origin differs from manifest: {path}")
    status_command = ["git", "-C", str(path), "status", "--porcelain"]
    if materials:
        status_command += ["--", ".", *[f":(exclude){item}" for item in materials]]
    if run(status_command).stdout:
        print(f"Kept local Git changes: {path}")
        return
    branch = run(["git", "-C", str(path), "symbolic-ref", "--quiet", "HEAD"], allowed=(0, 1))
    if branch.returncode:
        print(f"Kept detached checkout: {path}")
        return
    run(["git", "-C", str(path), "pull", "--ff-only"], env=git_env)


def copy_asset(source: Path, relative: Path, codex_home: Path):
    incoming = source / relative
    target = codex_home / relative
    if incoming.resolve() == target.resolve():
        return
    data = incoming.read_bytes()
    baseline = codex_home / "workspace-state/settings-baseline" / relative
    if target.exists() and target.read_bytes() != data:
        if baseline.exists():
            old = baseline.read_bytes()
        else:
            marker = codex_home / ".settings-sync-complete"
            revision = marker.read_text().strip() if marker.exists() else "HEAD"
            old_file = subprocess.run(["git", "-C", str(source), "show", f"{revision}:{relative.as_posix()}"], capture_output=True)
            if old_file.returncode:
                raise RuntimeError(f"Kept existing global file with no known baseline: {relative}")
            old = old_file.stdout
        if data == old:
            print(f"Kept local global customization: {relative}")
        elif target.read_bytes() == old:
            shutil.copy2(incoming, target)
        else:
            with tempfile.TemporaryDirectory() as directory:
                base = Path(directory) / "base"
                base.write_bytes(old)
                merged = run(["git", "merge-file", "-p", str(target), str(base), str(incoming)], allowed=(0, 1))
                if merged.returncode:
                    raise RuntimeError(f"Kept conflicting global customization: {relative}; reconcile before setup")
                target.write_text(merged.stdout, encoding="utf-8")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(incoming, target)
    baseline.parent.mkdir(parents=True, exist_ok=True)
    if not baseline.exists() or baseline.read_bytes() != data:
        baseline.write_bytes(data)


def apply_settings(source: Path, codex_home: Path):
    codex_home.mkdir(parents=True, exist_ok=True)
    for name in ("AGENTS.md", "SETUP.md", "hooks.json", "shared.config.toml"):
        copy_asset(source, Path(name), codex_home)
    for name in ("rules", "scripts", "skills"):
        for asset in sorted((source / name).rglob("*")):
            relative = asset.relative_to(source)
            if asset.is_file() and not any(part in {".system", "__pycache__"} for part in relative.parts) and asset.suffix != ".pyc":
                copy_asset(source, relative, codex_home)
    run(["uv", "run", "--script", str(source / "scripts/bootstrap.py")])
    revision = run(["git", "-C", str(source), "rev-parse", "HEAD"]).stdout
    (codex_home / ".settings-sync-complete").write_text(revision, encoding="utf-8")
    if os.name == "nt":
        hooks_path = codex_home / "hooks.json"
        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
        command = subprocess.list2cmdline([str(Path(shutil.which("uv"))), "run", "--script",
                                           str(codex_home / "scripts/workspace.py"), "sync", "--background"])
        hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"] = command
        hooks_path.write_text(json.dumps(hooks, indent=2) + "\n", encoding="utf-8")


def ensure_tools(codex_home: Path):
    missing = [name for name in ("rclone", "bw") if not shutil.which(name)]
    if not missing:
        return
    if shutil.which("brew"):
        packages = ["bitwarden-cli" if name == "bw" else name for name in missing]
        subprocess.run(["brew", "install", *packages], check=True)
    elif platform.system() == "Windows" and shutil.which("winget"):
        for name in missing:
            package = "Bitwarden.CLI" if name == "bw" else "Rclone.Rclone"
            subprocess.run(["winget", "install", "--exact", "--id", package,
                            "--accept-package-agreements", "--accept-source-agreements"], check=True)
        # Winget shims are available without restarting this Python process.
        links = Path(os.environ["LOCALAPPDATA"]) / "Microsoft/WinGet/Links"
        os.environ["PATH"] += os.pathsep + str(links)
    elif platform.system() == "Linux" and shutil.which("apt-get"):
        packages = ["unzip"] if "rclone" in missing and not shutil.which("unzip") else []
        if "bw" in missing and not shutil.which("npm"):
            packages.append("npm")
        if packages:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", *packages], check=True)
        if "rclone" in missing:
            with tempfile.TemporaryDirectory() as directory:
                installer = str(Path(directory) / "install-rclone.sh")
                subprocess.run(["curl", "-fsSL", "https://rclone.org/install.sh", "--output", installer], check=True)
                subprocess.run(["sudo", "bash", installer], check=True)
        if "bw" in missing:
            tools = codex_home / "tools"
            # Distro npm/Node can be too old for bw; keep its runtime local to Codex.
            subprocess.run(["npm", "install", "--engine-strict=false", "--prefix", str(tools), "node@24", "npm@11"], check=True)
            subprocess.run([str(tools / "bin/node"), str(tools / "lib/node_modules/npm/bin/npm-cli.js"),
                            "install", "--prefix", str(tools), "@bitwarden/cli"], check=True)
    else:
        raise RuntimeError("Install rclone and Bitwarden CLI (bw), then rerun setup; see SETUP.md")
    if any(not shutil.which(name) for name in missing):
        raise RuntimeError("Tools installed; reopen the terminal to refresh PATH and rerun setup")


def filters_for(materials: list[str]) -> str:
    # Exclusions precede the allowlist, including secrets inside context/ and skills/.
    lines = [f"- **/{name}/**" for name in sorted(EXCLUDED_DIRS)]
    lines += ["- **/.env", "- **/.env.*", "- **/*.pem", "- **/*.key", "- **/*.p12",
              "- **/*.pfx", "- **/credentials.json", "- **/token.json", "- **/auth.json",
              "- **/.codex-env-*/**"]
    for item in materials:
        lines += [f"+ /{item}", f"+ /{item}/**", f"+ /{item}.conflict*"]
    return "\n".join([*lines, "- **", ""])


def sync_materials(root: Path, config, state: Path, *, initial=False):
    remote = config["drive"]["remote"]
    content = filters_for(config["materials"])
    identity = hashlib.sha256((str(root.resolve()) + remote + content).encode()).hexdigest()[:20]
    work = state / "drive" / identity
    work.mkdir(parents=True, exist_ok=True)
    filter_path = work / "filters.txt"
    filter_path.write_text(content, encoding="utf-8")
    marker = work / "initialized"
    root.mkdir(parents=True, exist_ok=True)
    common = ["--filter-from", str(filter_path), "--drive-skip-gdocs"]
    if not marker.exists():
        if not initial:
            raise RuntimeError("Drive sync needs initial setup; rerun workspace.py setup")
        run(["rclone", "mkdir", remote])
        check = run(["rclone", "check", str(root), remote, "--download", "--combined", "-", *common], allowed=(0, 1))
        if any(line.startswith(("* ", "! ")) for line in check.stdout.splitlines()):
            raise RuntimeError("Initial Drive sync has differing files; kept both sides unchanged. Reconcile them before setup")
    command = ["rclone", "bisync", str(root), remote, "--workdir", str(work),
               "--conflict-resolve", "none", "--conflict-loser", "num",
               "--compare", "size,checksum", "--max-delete", "10",
               "--filters-file", str(filter_path), "--drive-skip-gdocs"]
    backup_run = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    command += ["--backup-dir1", str(state / "drive-backups" / identity / backup_run),
                "--backup-dir2", remote.rstrip("/") + ".backups/" + identity + "/" + backup_run]
    if not marker.exists():
        command.append("--resync")
    run(command)
    marker.touch()
    conflicts = run(["rclone", "lsf", str(root), "--recursive", "--files-only", *common]).stdout.splitlines()
    if any(re.search(r"\.conflict\d+", name) for name in conflicts):
        raise RuntimeError("Drive conflicts preserved as .conflict files; review both versions before continuing")
    print("Drive material sync completed")


def authorize_drive(config):
    remote_name = config["drive"]["remote"].split(":", 1)[0]
    remotes = run(["rclone", "listremotes"]).stdout.splitlines()
    if remote_name + ":" not in remotes:
        print("Authorize Google Drive in the browser that opens.", flush=True)
        run(["rclone", "config", "create", remote_name, "drive", "scope", "drive",
             "config_is_local", "true", "--no-output"])


def attach_project(root: Path, repo):
    if not repo.get("project"):
        return
    checkout = location(root, repo["path"])
    project = location(root, repo["project"])
    instructions = checkout / "AGENTS.md"
    if not instructions.exists() and (project / "AGENTS.md").is_file():
        relative = Path(os.path.relpath(project, checkout)).as_posix()
        instructions.write_text(
            f"# Shared project guidance\n\nRead and follow `{relative}/AGENTS.md` before work. "
            f"Resolve its context, rules, and skill paths from `{relative}/`.\n",
            encoding="utf-8",
        )
        exclude = run(["git", "-C", str(checkout), "rev-parse", "--path-format=absolute", "--git-path", "info/exclude"]).stdout.strip()
        with Path(exclude).open("a", encoding="utf-8") as output:
            output.write("\n/AGENTS.md\n")


def install_autosync(checkout: Path, codex_home: Path, root: Path):
    if os.name != "nt":
        subprocess.run(["bash", str(checkout / "scripts/install-autosync.sh")], check=True)
        return
    uv = str(Path(shutil.which("uv")))
    def quote(text):
        return "'" + text.replace("'", "''") + "'"
    payload = (
        f"$env:CODEX_HOME={quote(str(codex_home))}; $env:CODEX_AI_ROOT={quote(str(root))}; "
        f"$env:CODEX_SETTINGS_CHECKOUT={quote(str(checkout))}; "
        f"& {quote(uv)} run --script {quote(str(codex_home / 'scripts/workspace.py'))} sync"
    )
    arguments = subprocess.list2cmdline(["-NoProfile", "-Command", payload])
    command = (
        f"$action = New-ScheduledTaskAction -Execute {quote(str(Path(shutil.which('powershell'))))} -Argument {quote(arguments)}; "
        "$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) "
        "-RepetitionInterval (New-TimeSpan -Minutes 5); "
        "Register-ScheduledTask -TaskName 'CodexWorkspaceSync' -Action $action "
        "-Trigger $trigger -Description 'Synchronize Codex settings, project material and Git' -Force | Out-Null"
    )
    run(["powershell", "-NoProfile", "-Command", command])


def protect_env(path: Path):
    if path.is_symlink():
        raise RuntimeError(f"Refusing a symlink env target: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    git_root = run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"], allowed=(0, 128))
    if git_root.returncode == 0:
        repo = Path(git_root.stdout.strip())
        relative = path.resolve().relative_to(repo.resolve()).as_posix()
        tracked = run(["git", "-C", str(repo), "ls-files", "--error-unmatch", "--", relative], allowed=(0, 1))
        if tracked.returncode == 0:
            raise RuntimeError(f"Env target is tracked by Git; refusing to write: {path}")
        if run(["git", "-C", str(repo), "check-ignore", "--quiet", "--", relative], allowed=(0, 1)).returncode:
            exclude = run(["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-path", "info/exclude"]).stdout.strip()
            with Path(exclude).open("a", encoding="utf-8") as output:
                output.write(f"\n/{relative}\n.codex-env-*/\n")


def write_env(path: Path, content: str, *, refresh=False):
    protect_env(path)
    if path.exists() and path.read_text(encoding="utf-8") != content and not refresh:
        raise RuntimeError(f"Kept differing local env: {path}; use --refresh-envs to explicitly replace it")
    with tempfile.TemporaryDirectory(prefix=".codex-env-", dir=path.parent) as directory:
        temporary = Path(directory) / "env"
        with temporary.open("w", encoding="utf-8", newline="") as output:
            if os.name != "nt":
                os.fchmod(output.fileno(), 0o600)
            output.write(content)
        os.replace(temporary, path)


@contextmanager
def vault_session(config):
    server = config["bitwarden"]["server"]
    status = json.loads(run(["bw", "status"]).stdout)
    if (status.get("serverUrl") or "https://vault.bitwarden.com") != server:
        if status["status"] != "unauthenticated":
            raise RuntimeError("Bitwarden is signed into another server; keep that session and use the intended account explicitly")
        run(["bw", "config", "server", server])
    environment = dict(os.environ)
    owned_session = False
    try:
        if status["status"] != "unlocked":
            action = "login" if status["status"] == "unauthenticated" else "unlock"
            print(f"Bitwarden {action}: enter credentials in your terminal (never in chat).", flush=True)
            result = subprocess.run(["bw", action, "--raw"], stdout=subprocess.PIPE, text=True)
            if result.returncode or not result.stdout.strip():
                raise RuntimeError("Bitwarden login/unlock did not complete")
            environment["BW_SESSION"] = result.stdout.strip()
            owned_session = True
        run(["bw", "sync", "--nointeraction"], env=environment)
        yield environment
    finally:
        if owned_session:
            run(["bw", "lock", "--nointeraction"], env=environment)
            environment.pop("BW_SESSION", None)


def vault_note(identifier: str, environment):
    if re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", identifier):
        return json.loads(run(["bw", "get", "item", identifier, "--nointeraction"], env=environment).stdout)
    matches = json.loads(run(["bw", "list", "items", "--search", identifier, "--nointeraction"], env=environment).stdout)
    matches = [entry for entry in matches if entry["name"] == identifier]
    if len(matches) > 1:
        raise RuntimeError("Ambiguous Bitwarden note name; configure its exact item ID")
    return matches[0] if matches else None


def sync_envs(root: Path, config, *, import_envs=False, refresh=False):
    if not config.get("envs"):
        raise RuntimeError("No env mappings configured in workspace.toml; add selected env paths and Bitwarden note names")
    for item in config["envs"]:
        protect_env(location(root, item["path"]))
    with vault_session(config) as environment:
        for item in config["envs"]:
            path = location(root, item["path"])
            entry = vault_note(item["item"], environment)
            if entry is None and import_envs:
                if not path.is_file():
                    raise RuntimeError(f"No local env to import: {path}")
                note = {"type": 2, "name": item["item"], "secureNote": {"type": 0},
                        "notes": path.read_text(encoding="utf-8")}
                encoded = base64.b64encode(json.dumps(note).encode()).decode()
                run(["bw", "create", "item", "--nointeraction"], env=environment, input=encoded)
                if os.name != "nt":
                    path.chmod(0o600)
                print(f"Imported selected env into Bitwarden: {path}")
                continue
            if entry is None:
                raise RuntimeError(f"Selected Bitwarden note is missing for {path}; import it on the source computer first")
            if entry.get("type") != 2 or not isinstance(entry.get("notes"), str) or not entry["notes"].strip():
                raise RuntimeError("Expected a nonempty Bitwarden secure note for the selected env")
            write_env(path, entry["notes"], refresh=refresh)
            print(f"Restored selected env: {path}")


@contextmanager
def sync_lock(state: Path):
    state.mkdir(parents=True, exist_ok=True)
    lock = state / "sync.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if os.name == "nt":
            import msvcrt
            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(descriptor)
        raise RuntimeError("Workspace sync is already running") from None
    try:
        yield
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("setup", "sync", "env"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--background", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--import-envs", action="store_true", help="Import selected local env files as secure notes when missing")
    parser.add_argument("--refresh-envs", action="store_true", help="Explicitly replace differing local env files")
    args = parser.parse_args()
    if args.background:
        command = [sys.executable, str(Path(__file__).resolve()), *[x for x in sys.argv[1:] if x != "--background"]]
        options = {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, **options)
        return
    root = Path(os.environ.get("CODEX_AI_ROOT", Path.home() / "ai")).expanduser().resolve()
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    os.environ["PATH"] = str(codex_home / "tools/bin") + os.pathsep + os.environ["PATH"]
    checkout = Path(os.environ.get("CODEX_SETTINGS_CHECKOUT", Path.home() / ".local/share/codex-settings")).expanduser().resolve()
    state = codex_home / "workspace-state"
    with sync_lock(state):
        if not args.dry_run and args.action != "env":
            sync_repo(checkout, SETTINGS_URL)
            apply_settings(checkout, codex_home)
        manifest = args.manifest or codex_home / "workspace.toml"
        if args.action == "setup" and not args.dry_run:
            ensure_tools(codex_home)
        if not args.manifest and not args.dry_run:
            previous_remote = read_manifest(manifest, root)["drive"]["remote"] if manifest.exists() else "codex-projects:Codex Projects"
            remote = os.environ.get("CODEX_DRIVE_REMOTE", previous_remote)
            if args.action == "setup":
                authorize_drive({"drive": {"remote": remote}})
            downloaded = run(["rclone", "cat", remote.rstrip("/") + "/workspace.toml"]).stdout
            pending = state / "workspace.pending.toml"
            pending.write_text(downloaded, encoding="utf-8")
            read_manifest(pending, root)
            os.replace(pending, manifest)
        config = read_manifest(manifest, root)
        if args.dry_run:
            print(f"Workspace: {root}")
            print(f"Configured: {len(config['materials'])} material paths, {len(config['repositories'])} Git repositories, {len(config.get('envs', []))} env notes")
            print("Dry run: no Git updates, cloud access, vault access, or env writes")
            return
        if args.action == "setup":
            authorize_drive(config)
            if args.manifest:
                # Initial migration: never overwrite a different cloud catalog.
                run(["rclone", "copyto", str(manifest), config["drive"]["remote"].rstrip("/") + "/workspace.toml", "--immutable"])
                if manifest.resolve() != (codex_home / "workspace.toml").resolve():
                    shutil.copy2(manifest, codex_home / "workspace.toml")
        if args.action != "env":
            for repo in config["repositories"]:
                sync_repo(location(root, repo["path"]), repo["url"],
                          materials=config["materials"] if repo["path"] == "." else ())
            sync_materials(root, config, state, initial=args.action == "setup")
            for repo in config["repositories"]:
                attach_project(root, repo)
        if args.action in {"setup", "env"}:
            sync_envs(root, config, import_envs=args.import_envs, refresh=args.refresh_envs)
        if args.action == "setup":
            (codex_home / ".workspace-configured").touch()
            install_autosync(checkout, codex_home, root)
            print("Workspace setup completed; background sync never unlocks Bitwarden or rewrites env files")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(f"Setup incomplete: {error}", file=sys.stderr)
        sys.exit(1)
