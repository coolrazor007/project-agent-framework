"""Structured models for project task state and orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Role(str, Enum):
    ARCHITECT = "architect"
    CODER = "coder"
    QA = "qa"


class TaskStatus(str, Enum):
    PENDING = "Pending"
    READY = "Ready"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    DONE = "Done"
    REMOVED = "Removed"


class QAResult(str, Enum):
    PENDING = "Pending"
    PASS = "Pass"
    FAIL = "Fail"
    BLOCKED = "Blocked"
    NOT_APPLICABLE = "Not Applicable"
    REMOVED = "Removed"


class ProjectQAResult(str, Enum):
    PENDING = "Pending"
    PASS = "Pass"
    FAIL = "Fail"
    BLOCKED = "Blocked"


TERMINAL_QA_RESULTS = {
    QAResult.PASS.value,
    QAResult.NOT_APPLICABLE.value,
    QAResult.REMOVED.value,
}

TASK_FIELDS = {
    "id",
    "title",
    "description",
    "acceptance_criteria",
    "priority",
    "status",
    "qa_result",
    "coder_note",
    "qa_note",
    "architect_note",
    "depends_on",
    "files_touched",
    "retry_count",
    "history",
}

REQUIRED_TASK_FIELDS = {
    "id",
    "title",
    "description",
    "acceptance_criteria",
    "priority",
    "status",
    "qa_result",
    "coder_note",
    "qa_note",
    "depends_on",
}


@dataclass(slots=True)
class Task:
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: int | str
    status: str
    qa_result: str
    coder_note: str
    qa_note: str
    architect_note: str = ""
    depends_on: list[str] = field(default_factory=list)
    files_touched: list[str] = field(default_factory=list)
    retry_count: dict[str, int] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": list(self.acceptance_criteria),
            "priority": self.priority,
            "status": self.status,
            "qa_result": self.qa_result,
            "coder_note": self.coder_note,
            "qa_note": self.qa_note,
            "architect_note": self.architect_note,
            "depends_on": list(self.depends_on),
            "files_touched": list(self.files_touched),
            "retry_count": dict(self.retry_count),
            "history": list(self.history),
        }


@dataclass(slots=True)
class ProjectQA:
    result: str = ProjectQAResult.PENDING.value
    note: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"result": self.result, "note": self.note}


@dataclass(slots=True)
class TodoDocument:
    tasks: list[Task]
    project_qa: ProjectQA = field(default_factory=ProjectQA)
    project: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tasks": [task.to_dict() for task in self.tasks],
            "project_qa": self.project_qa.to_dict(),
        }
        if self.project:
            payload["project"] = self.project
        return payload

    def task_map(self) -> dict[str, Task]:
        return {task.id: task for task in self.tasks}


@dataclass(slots=True)
class ProjectPaths:
    project_dir: Path
    prd_path: Path
    todo_path: Path
    backup_path: Path
    framework_dir: Path
    logs_dir: Path

    @classmethod
    def from_inputs(
        cls,
        project_dir: Path,
        prd_path: Path | None,
        todo_path: Path | None,
        backup_path: Path | None,
        framework_dirname: str,
        logs_dir: Path | None,
    ) -> "ProjectPaths":
        framework_dir = project_dir / framework_dirname
        resolved_prd = prd_path or (project_dir / "PRD.md")
        resolved_todo = todo_path or (project_dir / "TODO.yml")
        resolved_backup = backup_path or (project_dir / "TODO.yml.bak")
        resolved_logs_dir = logs_dir or (framework_dir / "logs")
        return cls(
            project_dir=project_dir,
            prd_path=resolved_prd,
            todo_path=resolved_todo,
            backup_path=resolved_backup,
            framework_dir=framework_dir,
            logs_dir=resolved_logs_dir,
        )


@dataclass(slots=True)
class RoleRunResult:
    role: Role
    command: list[str]
    prompt: str
    returncode: int
    stdout: str
    stderr: str
    final_message: str
    output_dir: Path

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(slots=True)
class RunSummary:
    completed: bool
    loops: int
    final_project_qa: str
    project_dir: Path


@dataclass(slots=True)
class OrchestratorConfig:
    project_dir: Path
    codex_bin: str
    max_retries: int
    runner_type: str
    prd_path: Path | None = None
    todo_path: Path | None = None
    backup_path: Path | None = None
    log_dir: Path | None = None
    shared_agents_path: Path | None = None
    architect_agents_path: Path | None = None
    coder_agents_path: Path | None = None
    qa_agents_path: Path | None = None
    skip_final_qa: bool = False
    loop_limit: int | None = None
    docker_image: str | None = None
    model: str | None = None
