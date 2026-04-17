"""Per-loop and per-role logging utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Role, RoleRunResult


class RunLogger:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def attempt_dir(self, loop_index: int, role: Role, attempt: int) -> Path:
        path = self.base_dir / f"loop_{loop_index:03d}" / f"{role.value}_attempt_{attempt}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_result(self, result: RoleRunResult) -> None:
        (result.output_dir / "prompt.md").write_text(result.prompt, encoding="utf-8")
        (result.output_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (result.output_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        (result.output_dir / "final_message.txt").write_text(result.final_message, encoding="utf-8")
        payload = {
            "role": result.role.value,
            "command": result.command,
            "returncode": result.returncode,
        }
        (result.output_dir / "result.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def write_metadata(self, loop_index: int, filename: str, payload: dict[str, Any]) -> None:
        loop_dir = self.base_dir / f"loop_{loop_index:03d}"
        loop_dir.mkdir(parents=True, exist_ok=True)
        (loop_dir / filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")

