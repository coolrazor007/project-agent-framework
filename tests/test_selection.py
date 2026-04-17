from __future__ import annotations

from project_agent_framework.selection import select_next_task
from project_agent_framework.todo import validate_todo_data


def test_select_next_task_skips_unsatisfied_dependencies() -> None:
    document = validate_todo_data(
        {
            "tasks": [
                {
                    "id": "T-1",
                    "title": "Base",
                    "description": "desc",
                    "acceptance_criteria": ["works"],
                    "priority": 1,
                    "status": "Ready",
                    "qa_result": "Pending",
                    "coder_note": "",
                    "qa_note": "",
                    "depends_on": ["T-2"],
                },
                {
                    "id": "T-2",
                    "title": "Dependency",
                    "description": "desc",
                    "acceptance_criteria": ["works"],
                    "priority": 2,
                    "status": "Ready",
                    "qa_result": "Pending",
                    "coder_note": "",
                    "qa_note": "",
                    "depends_on": [],
                },
            ]
        }
    )
    assert select_next_task(document).id == "T-2"


def test_select_next_task_returns_first_eligible_task() -> None:
    document = validate_todo_data(
        {
            "tasks": [
                {
                    "id": "T-1",
                    "title": "Done",
                    "description": "desc",
                    "acceptance_criteria": ["works"],
                    "priority": 1,
                    "status": "Done",
                    "qa_result": "Pass",
                    "coder_note": "",
                    "qa_note": "",
                    "depends_on": [],
                },
                {
                    "id": "T-2",
                    "title": "Next",
                    "description": "desc",
                    "acceptance_criteria": ["works"],
                    "priority": 2,
                    "status": "Ready",
                    "qa_result": "Pending",
                    "coder_note": "",
                    "qa_note": "",
                    "depends_on": [],
                },
            ]
        }
    )
    assert select_next_task(document).id == "T-2"

