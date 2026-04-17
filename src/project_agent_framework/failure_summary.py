"""Compact failure summaries for retries and logs."""

from __future__ import annotations

from pathlib import Path


def summarize_failure(*parts: str, limit: int = 600) -> str:
    cleaned: list[str] = []
    for part in parts:
        if not part:
            continue
        for line in part.splitlines():
            stripped = line.strip()
            if stripped:
                cleaned.append(stripped)
    message = " | ".join(cleaned)
    return message[:limit] if len(message) > limit else message


def summarize_failure_files(*paths: Path, limit: int = 600) -> str:
    content = []
    for path in paths:
        if path.exists():
            content.append(path.read_text(encoding="utf-8"))
    return summarize_failure(*content, limit=limit)

