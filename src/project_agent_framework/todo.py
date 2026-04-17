"""YAML-backed TODO document handling and mutation controls."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path
from typing import Any

import yaml

from .exceptions import MutationPermissionError, TodoValidationError
from .models import (
    QAResult,
    REQUIRED_TASK_FIELDS,
    TASK_FIELDS,
    TERMINAL_QA_RESULTS,
    ProjectQA,
    ProjectQAResult,
    Role,
    Task,
    TaskStatus,
    TodoDocument,
)


ROOT_FIELDS = {"tasks", "project_qa", "project"}


def load_todo_document(path: Path) -> TodoDocument:
    if not path.exists():
        raise TodoValidationError(f"Missing TODO file: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TodoValidationError(f"Failed to parse YAML at {path}: {exc}") from exc
    return validate_todo_data(raw)


def validate_todo_data(raw: Any) -> TodoDocument:
    if raw is None:
        raise TodoValidationError("TODO.yml is empty.")
    if isinstance(raw, list):
        payload = {"tasks": raw}
    elif isinstance(raw, dict):
        unknown = set(raw) - ROOT_FIELDS
        if unknown:
            raise TodoValidationError(
                f"Unknown root fields in TODO.yml: {', '.join(sorted(unknown))}"
            )
        payload = raw
    else:
        raise TodoValidationError("TODO.yml root must be a mapping or a task list.")

    tasks_raw = payload.get("tasks")
    if not isinstance(tasks_raw, list):
        raise TodoValidationError("TODO.yml must contain a 'tasks' list.")

    tasks = [_parse_task(item, index) for index, item in enumerate(tasks_raw)]
    _validate_task_uniqueness(tasks)
    _validate_dependencies(tasks)

    project_qa_raw = payload.get("project_qa") or {}
    if not isinstance(project_qa_raw, dict):
        raise TodoValidationError("project_qa must be a mapping when present.")
    result = project_qa_raw.get("result", ProjectQAResult.PENDING.value)
    note = project_qa_raw.get("note", "")
    _validate_enum(
        "project_qa.result",
        result,
        {item.value for item in ProjectQAResult},
    )
    if not isinstance(note, str):
        raise TodoValidationError("project_qa.note must be a string.")

    project = payload.get("project") or {}
    if not isinstance(project, dict):
        raise TodoValidationError("project must be a mapping when present.")

    return TodoDocument(tasks=tasks, project_qa=ProjectQA(result=result, note=note), project=project)


def save_todo_document(document: TodoDocument, path: Path) -> None:
    path.write_text(
        yaml.safe_dump(document.to_dict(), sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def refresh_backup(todo_path: Path, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(todo_path, backup_path)


def restore_backup(todo_path: Path, backup_path: Path) -> None:
    if not backup_path.exists():
        raise TodoValidationError(f"Backup does not exist: {backup_path}")
    shutil.copy2(backup_path, todo_path)


def is_task_terminal(task: Task) -> bool:
    return task.qa_result in TERMINAL_QA_RESULTS


def is_project_task_complete(document: TodoDocument) -> bool:
    return all(is_task_terminal(task) for task in document.tasks)


def task_snapshot(document: TodoDocument, task_id: str) -> dict[str, Any]:
    for task in document.tasks:
        if task.id == task_id:
            return task.to_dict()
    raise TodoValidationError(f"Task not found: {task_id}")


def update_task_fields(path: Path, task_id: str, role: Role, updates: dict[str, Any]) -> TodoDocument:
    document = load_todo_document(path)
    if task_id not in document.task_map():
        raise TodoValidationError(f"Task not found: {task_id}")
    _validate_task_update_role(role, updates)
    mutated = copy.deepcopy(document)
    task = mutated.task_map()[task_id]
    for key, value in updates.items():
        if key == "qa_result":
            _validate_enum("qa_result", value, {item.value for item in QAResult})
        setattr(task, key, value)
    _validate_note_requirements(task)
    save_todo_document(mutated, path)
    return load_todo_document(path)


def update_project_qa(path: Path, role: Role, result: str, note: str) -> TodoDocument:
    if role is not Role.QA:
        raise MutationPermissionError("Only QA may update project_qa.")
    _validate_enum("project_qa.result", result, {item.value for item in ProjectQAResult})
    document = load_todo_document(path)
    document.project_qa.result = result
    document.project_qa.note = note
    save_todo_document(document, path)
    return load_todo_document(path)


def validate_role_mutation(
    role: Role,
    before: TodoDocument,
    after: TodoDocument,
    *,
    task_id: str | None = None,
    final_project_qa: bool = False,
) -> None:
    if role is Role.ARCHITECT:
        _validate_architect_mutation(before, after)
        return

    before_ids = [task.id for task in before.tasks]
    after_ids = [task.id for task in after.tasks]
    if before_ids != after_ids:
        raise MutationPermissionError(f"{role.value} may not add, remove, or reorder tasks.")
    if before.project != after.project:
        raise MutationPermissionError(f"{role.value} may not mutate project metadata.")

    before_map = before.task_map()
    after_map = after.task_map()

    if final_project_qa:
        if role is not Role.QA:
            raise MutationPermissionError("Only QA may run final project QA.")
        if any(before_map[key].to_dict() != after_map[key].to_dict() for key in before_map):
            raise MutationPermissionError("Final project QA may not mutate tasks.")
        return

    if task_id is None:
        raise MutationPermissionError(f"{role.value} mutation validation requires a task_id.")
    if before.project_qa.to_dict() != after.project_qa.to_dict():
        raise MutationPermissionError(f"{role.value} may not mutate project_qa during task execution.")
    if task_id not in before_map:
        raise MutationPermissionError(f"Task not found for mutation validation: {task_id}")

    allowed_fields = {
        Role.CODER: {"coder_note"},
        Role.QA: {"qa_result", "qa_note"},
    }[role]

    for current_task_id, before_task in before_map.items():
        after_task = after_map[current_task_id]
        changed_fields = {
            key
            for key, value in before_task.to_dict().items()
            if after_task.to_dict()[key] != value
        }
        if current_task_id != task_id and changed_fields:
            raise MutationPermissionError(
                f"{role.value} may not mutate unrelated task '{current_task_id}'."
            )
        if current_task_id == task_id:
            disallowed = changed_fields - allowed_fields
            if disallowed:
                raise MutationPermissionError(
                    f"{role.value} mutated forbidden fields on '{task_id}': {', '.join(sorted(disallowed))}"
                )
            if role is Role.QA:
                _validate_note_requirements(after_task)


def _validate_architect_mutation(before: TodoDocument, after: TodoDocument) -> None:
    if before.project_qa.to_dict() != after.project_qa.to_dict():
        raise MutationPermissionError("Architect may not mutate project_qa.")
    if before.project != after.project:
        raise MutationPermissionError("Architect may not mutate project metadata.")

    before_map = before.task_map()
    after_map = after.task_map()
    for task_id in set(before_map) & set(after_map):
        old = before_map[task_id]
        new = after_map[task_id]
        if old.coder_note != new.coder_note:
            raise MutationPermissionError(f"Architect may not edit coder_note for task '{task_id}'.")
        if old.qa_note != new.qa_note:
            raise MutationPermissionError(f"Architect may not edit qa_note for task '{task_id}'.")
        if old.qa_result != new.qa_result:
            removed_pair = (
                new.status == TaskStatus.REMOVED.value
                and new.qa_result == QAResult.REMOVED.value
            )
            if not removed_pair:
                raise MutationPermissionError(
                    f"Architect may not change qa_result for task '{task_id}' except when removing the task."
                )

    for task_id in set(after_map) - set(before_map):
        new = after_map[task_id]
        if new.qa_result != QAResult.PENDING.value:
            raise MutationPermissionError(
                f"New architect-created tasks must start with qa_result=Pending: '{task_id}'."
            )
        if new.coder_note or new.qa_note:
            raise MutationPermissionError(
                f"New architect-created tasks must start with empty coder_note and qa_note: '{task_id}'."
            )


def _validate_task_update_role(role: Role, updates: dict[str, Any]) -> None:
    allowed_fields = {
        Role.CODER: {"coder_note"},
        Role.QA: {"qa_result", "qa_note"},
    }.get(role)
    if allowed_fields is None:
        raise MutationPermissionError("task-update supports only coder and qa roles.")
    unknown = set(updates) - allowed_fields
    if unknown:
        raise MutationPermissionError(
            f"{role.value} may not update fields: {', '.join(sorted(unknown))}"
        )


def _parse_task(item: Any, index: int) -> Task:
    if not isinstance(item, dict):
        raise TodoValidationError(f"Task at index {index} must be a mapping.")
    missing = REQUIRED_TASK_FIELDS - set(item)
    if missing:
        raise TodoValidationError(
            f"Task at index {index} is missing required fields: {', '.join(sorted(missing))}"
        )
    unknown = set(item) - TASK_FIELDS
    if unknown:
        raise TodoValidationError(
            f"Task '{item.get('id', index)}' has unknown fields: {', '.join(sorted(unknown))}"
        )

    acceptance_criteria = item["acceptance_criteria"]
    depends_on = item["depends_on"]
    files_touched = item.get("files_touched") or []
    retry_count = item.get("retry_count") or {}
    history = item.get("history") or []

    if not isinstance(acceptance_criteria, list) or not all(
        isinstance(entry, str) for entry in acceptance_criteria
    ):
        raise TodoValidationError(
            f"Task '{item['id']}' acceptance_criteria must be a list of strings."
        )
    if not isinstance(depends_on, list) or not all(isinstance(entry, str) for entry in depends_on):
        raise TodoValidationError(f"Task '{item['id']}' depends_on must be a list of strings.")
    if not isinstance(files_touched, list) or not all(
        isinstance(entry, str) for entry in files_touched
    ):
        raise TodoValidationError(f"Task '{item['id']}' files_touched must be a list of strings.")
    if not isinstance(retry_count, dict):
        raise TodoValidationError(f"Task '{item['id']}' retry_count must be a mapping.")
    if not isinstance(history, list):
        raise TodoValidationError(f"Task '{item['id']}' history must be a list.")

    for field_name in ("id", "title", "description", "coder_note", "qa_note"):
        if not isinstance(item[field_name], str):
            raise TodoValidationError(f"Task '{item.get('id', index)}' field '{field_name}' must be a string.")
    if "architect_note" in item and not isinstance(item.get("architect_note"), str):
        raise TodoValidationError(f"Task '{item['id']}' architect_note must be a string.")

    _validate_enum("status", item["status"], {item.value for item in TaskStatus})
    _validate_enum("qa_result", item["qa_result"], {item.value for item in QAResult})

    task = Task(
        id=item["id"],
        title=item["title"],
        description=item["description"],
        acceptance_criteria=acceptance_criteria,
        priority=item["priority"],
        status=item["status"],
        qa_result=item["qa_result"],
        coder_note=item["coder_note"],
        qa_note=item["qa_note"],
        architect_note=item.get("architect_note", ""),
        depends_on=depends_on,
        files_touched=files_touched,
        retry_count=retry_count,
        history=history,
    )
    _validate_note_requirements(task)
    return task


def _validate_task_uniqueness(tasks: list[Task]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for task in tasks:
        if task.id in seen:
            duplicates.append(task.id)
        seen.add(task.id)
    if duplicates:
        raise TodoValidationError(f"Duplicate task ids detected: {', '.join(sorted(set(duplicates)))}")


def _validate_dependencies(tasks: list[Task]) -> None:
    ids = {task.id for task in tasks}
    for task in tasks:
        unknown = set(task.depends_on) - ids
        if unknown:
            raise TodoValidationError(
                f"Task '{task.id}' has invalid dependency references: {', '.join(sorted(unknown))}"
            )

    adjacency = {task.id: task.depends_on for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            raise TodoValidationError(f"Dependency cycle detected involving task '{task_id}'.")
        visiting.add(task_id)
        for dependency in adjacency[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in adjacency:
        visit(task_id)


def _validate_enum(field_name: str, value: Any, allowed: set[str]) -> None:
    if value not in allowed:
        raise TodoValidationError(
            f"{field_name} has invalid value '{value}'. Allowed values: {', '.join(sorted(allowed))}"
        )


def _validate_note_requirements(task: Task) -> None:
    if task.qa_result in {QAResult.FAIL.value, QAResult.BLOCKED.value} and not task.qa_note.strip():
        raise TodoValidationError(
            f"Task '{task.id}' must provide qa_note when qa_result is {task.qa_result}."
        )
