from __future__ import annotations

import pytest

from project_agent_framework.exceptions import MutationPermissionError
from project_agent_framework.models import Role
from project_agent_framework.todo import validate_role_mutation
from project_agent_framework.todo import validate_todo_data


def _document() -> dict:
    return {
        "tasks": [
            {
                "id": "T-1",
                "title": "Task 1",
                "description": "desc",
                "acceptance_criteria": ["works"],
                "priority": 1,
                "status": "Ready",
                "qa_result": "Pending",
                "coder_note": "",
                "qa_note": "",
                "depends_on": [],
            }
        ]
    }


def test_coder_may_only_update_coder_note() -> None:
    before = validate_todo_data(_document())
    payload = _document()
    payload["tasks"][0]["coder_note"] = "done"
    after = validate_todo_data(payload)
    validate_role_mutation(Role.CODER, before, after, task_id="T-1")


def test_coder_cannot_change_status() -> None:
    before = validate_todo_data(_document())
    payload = _document()
    payload["tasks"][0]["status"] = "Done"
    after = validate_todo_data(payload)
    with pytest.raises(MutationPermissionError):
        validate_role_mutation(Role.CODER, before, after, task_id="T-1")


def test_qa_must_not_mutate_other_tasks() -> None:
    before_payload = _document()
    before_payload["tasks"].append(
        {
            "id": "T-2",
            "title": "Task 2",
            "description": "desc",
            "acceptance_criteria": ["works"],
            "priority": 2,
            "status": "Ready",
            "qa_result": "Pending",
            "coder_note": "",
            "qa_note": "",
            "depends_on": [],
        }
    )
    before = validate_todo_data(before_payload)
    after_payload = _document()
    after_payload["tasks"].append(
        {
            "id": "T-2",
            "title": "Task 2",
            "description": "desc",
            "acceptance_criteria": ["works"],
            "priority": 2,
            "status": "Ready",
            "qa_result": "Pass",
            "coder_note": "",
            "qa_note": "done",
            "depends_on": [],
        }
    )
    after = validate_todo_data(after_payload)
    with pytest.raises(MutationPermissionError):
        validate_role_mutation(Role.QA, before, after, task_id="T-1")


def test_architect_cannot_override_existing_qa_result() -> None:
    before_payload = _document()
    before_payload["tasks"][0]["qa_result"] = "Fail"
    before_payload["tasks"][0]["qa_note"] = "broken"
    before = validate_todo_data(before_payload)
    after_payload = _document()
    after_payload["tasks"][0]["qa_result"] = "Pass"
    after_payload["tasks"][0]["qa_note"] = "broken"
    after = validate_todo_data(after_payload)
    with pytest.raises(MutationPermissionError):
        validate_role_mutation(Role.ARCHITECT, before, after)

