#!/usr/bin/env python3
"""Summarize local primary-turn model metadata without reading conversation bodies."""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import tomllib


def turn_metadata(path, offset, end_offset):
    """Read only bounded turn-start metadata; discard other records in chunks."""
    trigger = model = effort = None
    limit = min(offset + 1024 * 1024, end_offset or offset + 1024 * 1024)
    with Path(path).open("rb") as stream:
        stream.seek(offset)
        for _ in range(10):
            prefix = stream.readline(min(256, max(0, limit - stream.tell())))
            if not prefix:
                break
            match = re.search(rb'"type"\s*:\s*"([^"]+)"', prefix)
            kind = match.group(1) if match else None
            wanted = kind == b"turn_context" or (
                kind == b"event_msg" and b'"task_started"' in prefix
            )
            record = bytearray(prefix) if wanted else None
            chunk = prefix
            while not chunk.endswith(b"\n") and stream.tell() < limit:
                chunk = stream.readline(min(4096, limit - stream.tell()))
                if not chunk:
                    break
                if record is not None:
                    if len(record) + len(chunk) > 65536:
                        return trigger, None, None
                    record.extend(chunk)
            if not chunk.endswith(b"\n"):
                break
            if record is None:
                continue
            item = json.loads(record)
            payload = item.get("payload", {})
            if kind == b"event_msg":
                trigger = (payload.get("turn_attribution") or {}).get("turn_trigger")
            else:
                model = payload.get("model")
                effort = payload.get("effort")
                break
    return trigger, model, effort


def summarize(home, end, days):
    start = end - timedelta(days=days)
    report = {
        "period_utc": [start.isoformat(), end.isoformat()],
        "method": "Completed primary turns from bounded turn-start metadata; no message/tool bodies parsed",
        "scope": "Local Codex history only; not account-wide usage",
    }
    config = home / "config.toml"
    if config.exists():
        with config.open("rb") as stream:
            settings = tomllib.load(stream)
        report["configured_default"] = {
            "model": settings.get("model"),
            "effort": settings.get("model_reasoning_effort"),
            "measured_usage": False,
        }

    history = home / "thread_history_1.sqlite"
    state = home / "state_5.sqlite"
    counts, efforts, excluded, coverage = Counter(), Counter(), Counter(), Counter()
    directories, threads = Counter(), set()
    unknown_triggers = 0
    try:
        connection = sqlite3.connect(history.as_uri() + "?mode=ro", uri=True)
        try:
            connection.execute("ATTACH DATABASE ? AS state", (state.as_uri() + "?mode=ro",))
            connection.execute("PRAGMA query_only=ON")
            connection.execute("BEGIN")
            children = {
                row[0] for row in connection.execute("SELECT child_thread_id FROM state.thread_spawn_edges")
            }
            rows = connection.execute(
                "SELECT t.status,t.rollout_byte_offset,t.rollout_end_byte_offset,"
                "s.rollout_path,s.thread_source,s.source,t.thread_id,s.cwd "
                "FROM thread_turns t LEFT JOIN state.threads s ON s.id=t.thread_id "
                "WHERE t.started_at>=? AND t.started_at<?",
                (start.timestamp(), end.timestamp()),
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        report.update({"evidence_available": False, "error": str(error), "primary_model": None})
        return report

    for status, offset, end_offset, path, source, origin, thread_id, cwd in rows:
        if source == "subagent" or thread_id in children or '"subagent"' in (origin or ""):
            excluded["subagent"] += 1
            continue
        if source == "automation":
            excluded["scheduled"] += 1
            continue
        if status != "completed":
            excluded["not_completed"] += 1
            continue
        if offset is None or not path:
            coverage["missing_rollout_metadata"] += 1
            continue
        try:
            trigger, model, effort = turn_metadata(path, offset, end_offset)
        except (OSError, ValueError):
            coverage["unreadable_turn_metadata"] += 1
            continue
        if trigger and "automation" in trigger:
            excluded["scheduled"] += 1
            continue
        if not trigger:
            unknown_triggers += 1
        if not model:
            coverage["missing_turn_context"] += 1
            continue
        counts[model] += 1
        efforts[(model, effort)] += 1
        coverage["measured_primary_turns"] += 1
        directories[cwd] += 1
        threads.add(thread_id)

    leaders = [model for model, count in counts.items() if count == max(counts.values())] if counts else []
    report.update({
        "evidence_available": bool(counts),
        "primary_model": leaders[0] if len(leaders) == 1 else None,
        "primary_candidates": leaders,
        "database_turns": len(rows),
        "model_counts": dict(counts),
        "reasoning_counts": [
            {"model": model, "effort": effort, "turns": count}
            for (model, effort), count in efforts.items()
        ],
        "excluded": dict(excluded),
        "coverage": dict(coverage),
        "unknown_triggers_in_eligible_turns": unknown_triggers,
        "measured_threads": len(threads),
        "recent_directories": [{"path": path, "turns": count} for path, count in directories.most_common(10)],
    })
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--end", help="Audit end as ISO 8601 with UTC offset; defaults to now")
    args = parser.parse_args()
    if args.days <= 0:
        parser.error("--days must be positive")
    end = datetime.fromisoformat(args.end.replace("Z", "+00:00")) if args.end else datetime.now(timezone.utc)
    if end.tzinfo is None:
        parser.error("--end must include a UTC offset")
    result = summarize(args.codex_home.expanduser().resolve(), end.astimezone(timezone.utc), args.days)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
