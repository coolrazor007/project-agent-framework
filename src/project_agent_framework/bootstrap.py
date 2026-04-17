"""Project bootstrap helpers for new target repositories."""

from __future__ import annotations

from pathlib import Path

import yaml


STARTER_PRD = """# Project Title

## Purpose
Describe the product or feature you want the framework to build.

## Goals
- State the main outcomes.

## Non-Goals
- State what should stay out of scope.

## Acceptance Criteria
- List concrete, verifiable outcomes.
"""


def starter_todo() -> dict:
    return {
        "tasks": [
            {
                "id": "BOOT-001",
                "title": "Replace bootstrap plan",
                "description": "Review PRD.md and replace this starter task list with a real project backlog.",
                "acceptance_criteria": [
                    "TODO.yml contains real tasks derived from the target project's PRD",
                ],
                "priority": 1,
                "status": "Ready",
                "qa_result": "Pending",
                "coder_note": "",
                "qa_note": "",
                "architect_note": "",
                "depends_on": [],
            }
        ],
        "project_qa": {"result": "Pending", "note": ""},
    }


def init_project(
    *,
    prd_path: Path,
    todo_path: Path,
    shared_agents_path: Path | None = None,
    architect_agents_path: Path | None = None,
    coder_agents_path: Path | None = None,
    qa_agents_path: Path | None = None,
    force: bool = False,
) -> dict[str, str]:
    created: dict[str, str] = {}
    _write_text(prd_path, STARTER_PRD, force=force)
    created["prd"] = str(prd_path)
    _write_text(
        todo_path,
        yaml.safe_dump(starter_todo(), sort_keys=False, allow_unicode=False),
        force=force,
    )
    created["todo"] = str(todo_path)

    override_map = {
        "shared_agents": (shared_agents_path, _override_template("Shared")),
        "architect_agents": (architect_agents_path, _override_template("Architect")),
        "coder_agents": (coder_agents_path, _override_template("Coder")),
        "qa_agents": (qa_agents_path, _override_template("QA")),
    }
    for key, (path, content) in override_map.items():
        if path is None:
            continue
        _write_text(path, content, force=force)
        created[key] = str(path)
    return created


def _write_text(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _override_template(role_name: str) -> str:
    return (
        f"# {role_name} Override\n\n"
        "Add project-specific constraints, conventions, or tooling notes here.\n"
    )
