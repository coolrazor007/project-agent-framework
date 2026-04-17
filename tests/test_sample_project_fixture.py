from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from project_agent_framework.demo import materialize_sample_project, run_demo
from project_agent_framework.models import Role
from project_agent_framework.prompts import build_role_prompt
from project_agent_framework.todo import load_todo_document


def _target_env(project_dir: Path) -> dict[str, str]:
    env = dict()
    target_src = project_dir / "src"
    env.update({"PYTHONPATH": str(target_src)})
    return env


def test_sample_target_project_fixture_runs_end_to_end(tmp_path: Path) -> None:
    project_dir = tmp_path / "sample_target_project"
    summary = run_demo(project_dir)

    assert summary.completed is True
    assert summary.final_project_qa == "Pass"

    document = load_todo_document(project_dir / "TODO.yml")
    assert [task.qa_result for task in document.tasks] == ["Pass", "Pass", "Pass"]
    assert document.project_qa.result == "Pass"

    cli_run = subprocess.run(
        [sys.executable, "-m", "inventory_report.cli", "data/items.yml"],
        cwd=project_dir,
        env=_target_env(project_dir),
        check=False,
        capture_output=True,
        text=True,
    )
    assert cli_run.returncode == 0
    assert "Total items: 3" in cli_run.stdout


def test_materialize_sample_project_creates_workspace(tmp_path: Path) -> None:
    project_dir = tmp_path / "materialized"
    materialize_sample_project(project_dir)
    assert (project_dir / "PRD.md").exists()
    assert (project_dir / "TODO.yml").exists()
    assert (project_dir / ".git").exists()


def test_prompt_includes_agent_override_content(tmp_path: Path) -> None:
    project_dir = tmp_path / "materialized"
    materialize_sample_project(project_dir)
    override_path = project_dir / "AGENTS.coder.md"
    override_path.write_text("# Coder Override\nUse pytest before exiting.\n", encoding="utf-8")
    document = load_todo_document(project_dir / "TODO.yml")
    prompt = build_role_prompt(
        role=Role.CODER,
        project_dir=project_dir,
        prd_path=project_dir / "PRD.md",
        todo_path=project_dir / "TODO.yml",
        project_prd=(project_dir / "PRD.md").read_text(encoding="utf-8"),
        document=document,
        task=document.tasks[0],
        coder_agents_path=override_path,
    )
    assert "Use pytest before exiting." in prompt
    assert str(project_dir / "TODO.yml") in prompt


def test_init_command_bootstraps_project_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "bootstrapped"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_framework.py",
            "init",
            "--project-dir",
            str(project_dir),
            "--write-agent-overrides",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (project_dir / "PRD.md").exists()
    assert (project_dir / "TODO.yml").exists()
    assert (project_dir / "AGENTS.shared.md").exists()
    assert (project_dir / "AGENTS.architect.md").exists()
    assert (project_dir / "AGENTS.coder.md").exists()
    assert (project_dir / "AGENTS.qa.md").exists()
