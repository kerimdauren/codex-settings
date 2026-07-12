# /// script
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def platform_name() -> str:
    names = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    return names.get(platform.system().lower(), platform.system().lower())


def command_path(*names: str) -> str | None:
    for name in names:
        if path := shutil.which(name):
            return path
    return None


def command_succeeds(command: list[str]) -> bool:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def command_output(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return f"{result.stdout}\n{result.stderr}" if result.returncode == 0 else ""


def read_toml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("rb") as source:
            return tomllib.load(source)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def shared_values_match(local: object, shared: object) -> bool:
    if isinstance(shared, Mapping):
        return isinstance(local, Mapping) and all(
            key in local and shared_values_match(local[key], value)
            for key, value in shared.items()
        )
    return local == shared


def string_values(value: object, prefix: str = "") -> list[tuple[str, str]]:
    if isinstance(value, Mapping):
        values: list[tuple[str, str]] = []
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            values.extend(string_values(item, child))
        return values
    if isinstance(value, list):
        values = []
        for index, item in enumerate(value):
            values.extend(string_values(item, f"{prefix}[{index}]"))
        return values
    return [(prefix, value)] if isinstance(value, str) else []


def incompatible_paths(system: str, config: Mapping[str, Any] | None) -> list[str]:
    if not config:
        return []
    issues: list[str] = []
    for key, value in string_values(config):
        mac_path = any(
            token in value for token in ("/Applications/", "/Users/", "/MacOS/")
        )
        windows_path = bool(re.match(r"^[A-Za-z]:[\\/]", value))
        if system != "macos" and mac_path:
            issues.append(f"config.toml:{key} contains a macOS path")
        if system != "windows" and windows_path:
            issues.append(f"config.toml:{key} contains a Windows path")
    return sorted(set(issues))


def inspect_environment() -> dict[str, Any]:
    system = platform_name()
    codex_home = (
        Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        .expanduser()
        .resolve()
    )
    ai_root = (
        Path(os.environ.get("CODEX_AI_ROOT", Path.home() / "ai")).expanduser().resolve()
    )
    local_config = read_toml(codex_home / "config.toml")
    shared_config = read_toml(codex_home / "shared.config.toml")

    tools = {
        "codex": command_path("codex"),
        "git": command_path("git"),
        "uv": command_path("uv"),
        "uvx": command_path("uvx"),
        "python": command_path("python3", "python") or sys.executable,
        "node": command_path("node", "nodejs"),
        "powershell": command_path("pwsh", "powershell")
        if system == "windows"
        else None,
    }
    required_names = ("codex", "git", "uv", "uvx")
    optional_names = ("node",) + (("powershell",) if system == "windows" else ())
    required_missing = [name for name in required_names if not tools[name]]
    optional_missing = [name for name in optional_names if not tools[name]]

    expected_projects = {str(ai_root): {"trust_level": "trusted"}}
    shared_applied = bool(
        local_config
        and shared_config
        and shared_values_match(local_config, shared_config)
    )
    trusted_workspace_valid = bool(
        local_config and local_config.get("projects") == expected_projects
    )
    authenticated = bool(
        tools["codex"] and command_succeeds(["codex", "login", "status"])
    )
    mcp_output = command_output(["codex", "mcp", "list"]) if tools["codex"] else ""
    code_review_graph_ready = "code-review-graph" in mcp_output
    incompatible = incompatible_paths(system, local_config)

    planned_actions: list[str] = []
    if "git" in required_missing:
        planned_actions.append("Install Git")
    if "uv" in required_missing or "uvx" in required_missing:
        planned_actions.append("Install uv with uvx support")
    if not local_config or not shared_applied or not trusted_workspace_valid:
        script = "bootstrap-windows.ps1" if system == "windows" else "bootstrap-unix.sh"
        planned_actions.append(f"Run scripts/{script}")
    if not authenticated:
        planned_actions.append("Run codex login")
    if not code_review_graph_ready:
        planned_actions.append("Verify code-review-graph with codex mcp list")
    if incompatible:
        planned_actions.append(
            "Remove configuration paths from another operating system"
        )

    ready = not any(
        (
            required_missing,
            not shared_applied,
            not trusted_workspace_valid,
            not authenticated,
            not code_review_graph_ready,
            incompatible,
        )
    )
    marker = codex_home / ".setup-complete"
    return {
        "platform": system,
        "architecture": platform.machine(),
        "home": str(Path.home()),
        "codex_home": str(codex_home),
        "ai_root": str(ai_root),
        "shell": os.environ.get("SHELL") or os.environ.get("COMSPEC"),
        "tools": tools,
        "authenticated": authenticated,
        "shared_config_present": shared_config is not None,
        "local_config_present": local_config is not None,
        "shared_config_applied": shared_applied,
        "trusted_workspace_valid": trusted_workspace_valid,
        "code_review_graph_ready": code_review_graph_ready,
        "hooks_present": (codex_home / "hooks.json").exists(),
        "rules_present": (codex_home / "rules" / "default.rules").exists(),
        "required_missing": required_missing,
        "optional_missing": optional_missing,
        "incompatible": incompatible,
        "planned_actions": planned_actions,
        "ready": ready,
        "setup_complete": marker.exists(),
    }


def print_human(report: Mapping[str, Any]) -> None:
    print(f"Platform: {report['platform']} ({report['architecture']})")
    print(f"CODEX_HOME: {report['codex_home']}")
    print(f"AI workspace: {report['ai_root']}")
    print(f"Ready: {'yes' if report['ready'] else 'no'}")
    for title, key in (
        ("Required missing", "required_missing"),
        ("Optional missing", "optional_missing"),
        ("Incompatible", "incompatible"),
        ("Planned actions", "planned_actions"),
    ):
        values = report[key]
        if values:
            print(f"{title}:")
            for value in values:
                print(f"- {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the local Codex setup")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "--mark-complete",
        action="store_true",
        help="Create the local setup marker after all checks pass",
    )
    args = parser.parse_args()
    report = inspect_environment()

    if args.mark_complete:
        if not report["ready"]:
            print_human(report)
            raise SystemExit("Setup is incomplete; marker was not created")
        marker = Path(report["codex_home"]) / ".setup-complete"
        marker.write_text(
            json.dumps(
                {
                    "platform": report["platform"],
                    "architecture": report["architecture"],
                    "completed_at": datetime.now(UTC).isoformat(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        report["setup_complete"] = True

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
