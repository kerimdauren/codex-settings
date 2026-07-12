# /// script
# requires-python = ">=3.11"
# dependencies = ["tomlkit>=0.13,<1"]
# ///

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Mapping, MutableMapping
from copy import deepcopy
from pathlib import Path

import tomlkit


SHARED_CONFIG_NAME = "shared.config.toml"


def merge_shared_values(
    local: MutableMapping[str, object], shared: Mapping[str, object]
) -> None:
    for key, shared_value in shared.items():
        local_value = local.get(key)
        if isinstance(shared_value, Mapping) and isinstance(
            local_value, MutableMapping
        ):
            merge_shared_values(local_value, shared_value)
        else:
            local[key] = deepcopy(shared_value)


def trusted_projects(ai_root: Path) -> object:
    projects = tomlkit.table()
    project = tomlkit.table()
    project["trust_level"] = "trusted"
    projects[str(ai_root)] = project
    return projects


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def main() -> None:
    repository_root = Path(__file__).resolve().parent.parent
    source_shared = repository_root / SHARED_CONFIG_NAME
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    ai_root = (
        Path(os.environ.get("CODEX_AI_ROOT", Path.home() / "ai")).expanduser().resolve()
    )
    local_config = codex_home / "config.toml"
    target_shared = codex_home / SHARED_CONFIG_NAME

    shared = tomlkit.parse(source_shared.read_text(encoding="utf-8"))
    local = (
        tomlkit.parse(local_config.read_text(encoding="utf-8"))
        if local_config.exists()
        else tomlkit.document()
    )

    merge_shared_values(local, shared)
    local.pop("profile", None)
    local["projects"] = trusted_projects(ai_root)

    ai_root.mkdir(parents=True, exist_ok=True)
    codex_home.mkdir(parents=True, exist_ok=True)
    migration_backup = codex_home / "config.toml.pre-shared"
    if local_config.exists() and not migration_backup.exists():
        shutil.copy2(local_config, migration_backup)
    if source_shared.resolve() != target_shared.resolve():
        shutil.copy2(source_shared, target_shared)
    write_atomic(local_config, tomlkit.dumps(local))

    tomlkit.parse(local_config.read_text(encoding="utf-8"))
    tomlkit.parse(target_shared.read_text(encoding="utf-8"))
    print("Applied shared Codex settings")
    print(f"CODEX_HOME: {codex_home}")
    print(f"Trusted workspace: {ai_root}")


if __name__ == "__main__":
    main()
