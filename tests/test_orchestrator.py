from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from project_agent_framework.models import OrchestratorConfig, ProjectQAResult, Role, RoleRunResult
from project_agent_framework.orchestrator import Orchestrator
from project_agent_framework.runners import CodexRunner
from project_agent_framework.todo import load_todo_document


def _write_target_project(project_dir: Path) -> None:
    (project_dir / "PRD.md").write_text("# Target PRD\n", encoding="utf-8")
    (project_dir / "TODO.yml").write_text(
        yaml.safe_dump(
            {
                "tasks": [
                    {
                        "id": "T-1",
                        "title": "Create artifact",
                        "description": "Write the artifact file.",
                        "acceptance_criteria": ["artifact exists"],
                        "priority": 1,
                        "status": "Ready",
                        "qa_result": "Pending",
                        "coder_note": "",
                        "qa_note": "",
                        "depends_on": [],
                    }
                ],
                "project_qa": {"result": "Pending", "note": ""},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_dir, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_dir, check=True, capture_output=True)


class FakeRunner(CodexRunner):
    def run(
        self,
        *,
        role: Role,
        prompt: str,
        output_dir: Path,
        config: OrchestratorConfig,
    ) -> RoleRunResult:
        todo_path = config.todo_path or (config.project_dir / "TODO.yml")
        document = load_todo_document(todo_path)
        if role is Role.ARCHITECT:
            pass
        elif role is Role.CODER:
            task = document.tasks[0]
            task.coder_note = "Implemented artifact file."
            (config.project_dir / "artifact.txt").write_text("done\n", encoding="utf-8")
            with open(todo_path, "w", encoding="utf-8") as handle:
                yaml.safe_dump(document.to_dict(), handle, sort_keys=False)
        elif role is Role.QA and document.project_qa.result == ProjectQAResult.PENDING.value:
            if document.tasks[0].qa_result == "Pending":
                document.tasks[0].qa_result = "Pass"
                document.tasks[0].qa_note = "artifact.txt exists"
            else:
                document.project_qa.result = "Pass"
                document.project_qa.note = "Final integration check passed."
            with open(todo_path, "w", encoding="utf-8") as handle:
                yaml.safe_dump(document.to_dict(), handle, sort_keys=False)
        return RoleRunResult(
            role=role,
            command=["fake"],
            prompt=prompt,
            returncode=0,
            stdout="ok",
            stderr="",
            final_message="done",
            output_dir=output_dir,
        )


def test_orchestrator_runs_task_and_final_qa(tmp_path: Path) -> None:
    project_dir = tmp_path / "target"
    project_dir.mkdir()
    _write_target_project(project_dir)
    config = OrchestratorConfig(
        project_dir=project_dir,
        codex_bin="codex",
        max_retries=2,
        runner_type="local",
        docker_image=None,
        model=None,
    )
    summary = Orchestrator(config, runner=FakeRunner()).run()
    assert summary.completed is True
    assert summary.final_project_qa == "Pass"
    assert (project_dir / "artifact.txt").exists()
    final_doc = load_todo_document(project_dir / "TODO.yml")
    assert final_doc.tasks[0].qa_result == "Pass"
    assert final_doc.project_qa.result == "Pass"


def test_orchestrator_accepts_explicit_path_overrides(tmp_path: Path) -> None:
    project_dir = tmp_path / "target"
    project_dir.mkdir()
    prd_path = project_dir / "docs" / "product.md"
    todo_path = project_dir / "planning" / "tasks.yml"
    prd_path.parent.mkdir()
    todo_path.parent.mkdir()
    prd_path.write_text("# Target PRD\n", encoding="utf-8")
    todo_path.write_text(
        yaml.safe_dump(
            {
                "tasks": [
                    {
                        "id": "T-1",
                        "title": "Create artifact",
                        "description": "Write the artifact file.",
                        "acceptance_criteria": ["artifact exists"],
                        "priority": 1,
                        "status": "Ready",
                        "qa_result": "Pending",
                        "coder_note": "",
                        "qa_note": "",
                        "depends_on": [],
                    }
                ],
                "project_qa": {"result": "Pending", "note": ""},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_dir, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_dir, check=True, capture_output=True)
    config = OrchestratorConfig(
        project_dir=project_dir,
        prd_path=prd_path,
        todo_path=todo_path,
        codex_bin="codex",
        max_retries=2,
        runner_type="local",
        docker_image=None,
        model=None,
    )
    summary = Orchestrator(config, runner=FakeRunner()).run()
    assert summary.completed is True
