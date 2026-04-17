"""Prompt builders for role-specific Codex CLI runs."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Role, Task, TodoDocument
from .resources import read_resource_text


def build_role_prompt(
    *,
    role: Role,
    project_dir: Path,
    prd_path: Path,
    todo_path: Path,
    project_prd: str,
    document: TodoDocument,
    retry_summary: str = "",
    task: Task | None = None,
    final_project_qa: bool = False,
    shared_agents_path: Path | None = None,
    architect_agents_path: Path | None = None,
    coder_agents_path: Path | None = None,
    qa_agents_path: Path | None = None,
) -> str:
    shared = _render_template(
        "shared.md",
        project_dir=project_dir,
        prd_path=prd_path,
        todo_path=todo_path,
    )
    shared_override = _override_text(shared_agents_path)
    if role is Role.ARCHITECT:
        return "\n\n".join(
            [
                shared,
                shared_override,
                _render_template(
                    "architect.md",
                    project_dir=project_dir,
                    prd_path=prd_path,
                    todo_path=todo_path,
                ),
                _override_text(architect_agents_path),
                _retry_block(retry_summary),
                "# Target Project PRD",
                project_prd,
                "# Current TODO State",
                _todo_block(document),
            ]
        ).strip()
    if role is Role.CODER:
        if task is None:
            raise ValueError("Coder prompt requires a task.")
        return "\n\n".join(
            [
                shared,
                shared_override,
                _render_template(
                    "coder.md",
                    project_dir=project_dir,
                    prd_path=prd_path,
                    todo_path=todo_path,
                    task_id=task.id,
                ),
                _override_text(coder_agents_path),
                _retry_block(retry_summary),
                "# Target Project PRD",
                project_prd,
                "# Selected Task",
                _task_block(task),
                "# Dependency Context",
                _dependency_context(document, task),
            ]
        ).strip()
    if final_project_qa:
        return "\n\n".join(
            [
                shared,
                shared_override,
                _render_template(
                    "qa.md",
                    project_dir=project_dir,
                    prd_path=prd_path,
                    todo_path=todo_path,
                    task_id="FINAL-PROJECT-QA",
                ),
                _override_text(qa_agents_path),
                _render_template(
                    "final_qa.md",
                    project_dir=project_dir,
                    prd_path=prd_path,
                    todo_path=todo_path,
                ),
                _retry_block(retry_summary),
                "# Target Project PRD",
                project_prd,
                "# Current TODO State",
                _todo_block(document),
            ]
        ).strip()
    if task is None:
        raise ValueError("QA prompt requires a task unless final_project_qa=True.")
    return "\n\n".join(
        [
            shared,
            shared_override,
            _render_template(
                "qa.md",
                project_dir=project_dir,
                prd_path=prd_path,
                todo_path=todo_path,
                task_id=task.id,
            ),
            _override_text(qa_agents_path),
            _retry_block(retry_summary),
            "# Target Project PRD",
            project_prd,
            "# Selected Task",
            _task_block(task),
            "# Dependency Context",
            _dependency_context(document, task),
        ]
    ).strip()


def _render_template(template_name: str, **context: object) -> str:
    template = read_resource_text("resources", "agents", template_name)
    normalized = {key: str(value) for key, value in context.items()}
    return template.format(**normalized).strip()


def _override_text(path: Path | None) -> str:
    if path is None:
        return ""
    return path.read_text(encoding="utf-8").strip()


def _retry_block(retry_summary: str) -> str:
    if not retry_summary:
        return ""
    return f"# Retry Context\nPrevious attempt failed for this reason:\n\n{retry_summary}"


def _todo_block(document: TodoDocument) -> str:
    return "```json\n" + json.dumps(document.to_dict(), indent=2) + "\n```"


def _task_block(task: Task) -> str:
    return "```json\n" + json.dumps(task.to_dict(), indent=2) + "\n```"


def _dependency_context(document: TodoDocument, task: Task) -> str:
    by_id = document.task_map()
    related = [by_id[dependency].to_dict() for dependency in task.depends_on]
    return "```json\n" + json.dumps(related, indent=2) + "\n```"
