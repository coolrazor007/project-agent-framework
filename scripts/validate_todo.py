#!/usr/bin/env python3
"""Thin wrapper around the TODO validator."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from project_agent_framework.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["validate-todo", *sys.argv[1:]]))

