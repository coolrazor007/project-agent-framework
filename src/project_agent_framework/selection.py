"""Deterministic task selection rules."""

from __future__ import annotations

from .exceptions import NoRunnableTasksError
from .models import Task, TodoDocument
from .todo import is_task_terminal


def select_next_task(document: TodoDocument) -> Task:
    by_id = document.task_map()
    for task in document.tasks:
        if is_task_terminal(task):
            continue
        if task.status == "Removed" or task.qa_result == "Removed":
            continue
        if task.status == "Blocked":
            continue
        if all(by_id[dependency].qa_result in {"Pass", "Not Applicable", "Removed"} for dependency in task.depends_on):
            return task
    raise NoRunnableTasksError("No runnable tasks remain, but the project is not task-complete.")

