from __future__ import annotations

import pytest

from project_agent_framework.exceptions import TodoValidationError
from project_agent_framework.todo import validate_todo_data


def _base_task(task_id: str) -> dict:
    return {
        "id": task_id,
        "title": f"Task {task_id}",
        "description": "desc",
        "acceptance_criteria": ["works"],
        "priority": 1,
        "status": "Ready",
        "qa_result": "Pending",
        "coder_note": "",
        "qa_note": "",
        "depends_on": [],
    }


def test_validate_todo_accepts_minimal_document() -> None:
    document = validate_todo_data({"tasks": [_base_task("T-1")]})
    assert len(document.tasks) == 1
    assert document.project_qa.result == "Pending"


def test_validate_todo_rejects_duplicate_ids() -> None:
    with pytest.raises(TodoValidationError):
        validate_todo_data({"tasks": [_base_task("T-1"), _base_task("T-1")]})


def test_validate_todo_rejects_invalid_dependency_reference() -> None:
    task = _base_task("T-1")
    task["depends_on"] = ["T-404"]
    with pytest.raises(TodoValidationError):
        validate_todo_data({"tasks": [task]})


def test_validate_todo_rejects_dependency_cycles() -> None:
    first = _base_task("T-1")
    second = _base_task("T-2")
    first["depends_on"] = ["T-2"]
    second["depends_on"] = ["T-1"]
    with pytest.raises(TodoValidationError):
        validate_todo_data({"tasks": [first, second]})


def test_validate_todo_requires_qa_note_on_fail() -> None:
    task = _base_task("T-1")
    task["qa_result"] = "Fail"
    with pytest.raises(TodoValidationError):
        validate_todo_data({"tasks": [task]})

