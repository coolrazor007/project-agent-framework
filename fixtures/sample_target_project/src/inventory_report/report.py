from __future__ import annotations

from pathlib import Path


def load_items(path: str | Path) -> list[dict[str, str]]:
    raise NotImplementedError("Implement in INV-001")


def count_by_status(items: list[dict[str, str]]) -> dict[str, int]:
    raise NotImplementedError("Implement in INV-001")


def format_summary_report(items: list[dict[str, str]]) -> str:
    raise NotImplementedError("Implement in INV-002")

