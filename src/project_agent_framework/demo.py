"""Runnable demo support built around the bundled sample target project."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .models import OrchestratorConfig, Role, RoleRunResult, RunSummary
from .orchestrator import Orchestrator, make_default_config
from .resources import copy_resource_tree
from .runners import CodexRunner
from .selection import select_next_task
from .todo import load_todo_document, update_project_qa, update_task_fields


REPORT_IMPLEMENTATION = """from __future__ import annotations

from pathlib import Path

import yaml


def load_items(path: str | Path) -> list[dict[str, str]]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    items = payload.get("items", [])
    normalized: list[dict[str, str]] = []
    for item in items:
        normalized.append(
            {
                "name": str(item["name"]).strip(),
                "status": str(item.get("status", "unknown")).strip().lower(),
                "owner": str(item.get("owner", "unassigned")).strip().lower(),
            }
        )
    return normalized


def count_by_status(items: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = item["status"]
        counts[status] = counts.get(status, 0) + 1
    return counts


def format_summary_report(items: list[dict[str, str]]) -> str:
    counts = count_by_status(items)
    lines = [f"Total items: {len(items)}"]
    for status in sorted(counts):
        lines.append(f"{status}: {counts[status]}")
    return "\\n".join(lines)
"""

CLI_IMPLEMENTATION = """from __future__ import annotations

import sys
from pathlib import Path

from .report import format_summary_report, load_items


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        print("Usage: python -m inventory_report.cli <path-to-items.yml>", file=sys.stderr)
        return 1
    data_path = Path(args[0]).resolve()
    items = load_items(data_path)
    print(format_summary_report(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

TEST_IMPLEMENTATION = """from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from inventory_report.report import count_by_status, load_items


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "items.yml"


def test_count_by_status_aggregates_normalized_values() -> None:
    items = load_items(DATA_PATH)
    assert count_by_status(items) == {"active": 2, "retired": 1}


def test_cli_prints_expected_summary() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_report.cli", str(DATA_PATH)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip().splitlines() == [
        "Total items: 3",
        "active: 2",
        "retired: 1",
    ]
"""

README_APPEND = """

## Local Usage

Run the CLI locally with:

```bash
PYTHONPATH=src python -m inventory_report.cli data/items.yml
```
"""


class DemoRunner(CodexRunner):
    """Deterministic built-in runner for the sample project demo."""

    def run(
        self,
        *,
        role: Role,
        prompt: str,
        output_dir: Path,
        config: OrchestratorConfig,
    ) -> RoleRunResult:
        if role is Role.ARCHITECT:
            return _result(role, prompt, output_dir)

        if role is Role.CODER:
            task = select_next_task(load_todo_document(config.project_dir / "TODO.yml"))
            self._implement_task(config.project_dir, task.id)
            update_task_fields(
                config.project_dir / "TODO.yml",
                task.id,
                Role.CODER,
                {"coder_note": f"Implemented {task.id} in demo runner."},
            )
            return _result(role, prompt, output_dir)

        if "Final Project QA Instructions" in prompt:
            self._run_final_project_qa(config.project_dir)
            return _result(role, prompt, output_dir)

        task = select_next_task(load_todo_document(config.project_dir / "TODO.yml"))
        self._run_task_qa(config.project_dir, task.id)
        return _result(role, prompt, output_dir)

    def _implement_task(self, project_dir: Path, task_id: str) -> None:
        if task_id == "INV-001":
            (project_dir / "src" / "inventory_report" / "report.py").write_text(
                REPORT_IMPLEMENTATION,
                encoding="utf-8",
            )
            return
        if task_id == "INV-002":
            (project_dir / "src" / "inventory_report" / "cli.py").write_text(
                CLI_IMPLEMENTATION,
                encoding="utf-8",
            )
            return
        if task_id == "INV-003":
            tests_dir = project_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            (tests_dir / "test_inventory_report.py").write_text(TEST_IMPLEMENTATION, encoding="utf-8")
            readme_path = project_dir / "README.md"
            readme_path.write_text(
                readme_path.read_text(encoding="utf-8") + README_APPEND,
                encoding="utf-8",
            )
            return
        raise AssertionError(f"Unexpected task id: {task_id}")

    def _run_task_qa(self, project_dir: Path, task_id: str) -> None:
        if task_id == "INV-001":
            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; "
                    "from inventory_report.report import load_items, count_by_status; "
                    "items = load_items(Path('data/items.yml')); "
                    "assert count_by_status(items) == {'active': 2, 'retired': 1}",
                ],
                cwd=project_dir,
                env=_target_env(project_dir),
                text=True,
                capture_output=True,
                check=False,
            )
            _check_completed(completed)
            note = "Verified normalized loading and aggregate counts."
        elif task_id == "INV-002":
            completed = _run_cli(project_dir)
            _check_completed(completed)
            if completed.stdout.strip().splitlines() != [
                "Total items: 3",
                "active: 2",
                "retired: 1",
            ]:
                raise AssertionError(f"Unexpected CLI output:\n{completed.stdout}")
            note = "Verified CLI output and exit status."
        elif task_id == "INV-003":
            completed = _run_pytest(project_dir)
            _check_completed(completed)
            note = "Verified target project pytest suite and README usage note."
        else:
            raise AssertionError(f"Unexpected task id: {task_id}")

        update_task_fields(
            project_dir / "TODO.yml",
            task_id,
            Role.QA,
            {"qa_result": "Pass", "qa_note": note},
        )

    def _run_final_project_qa(self, project_dir: Path) -> None:
        _check_completed(_run_pytest(project_dir))
        _check_completed(_run_cli(project_dir))
        update_project_qa(
            project_dir / "TODO.yml",
            Role.QA,
            "Pass",
            "Project-level pytest and CLI smoke checks passed.",
        )


def run_demo(
    workspace: Path,
    *,
    force: bool = False,
    codex_bin: str = "codex",
    max_retries: int = 2,
    model: str | None = None,
) -> RunSummary:
    materialize_sample_project(workspace, force=force)
    config = make_default_config(
        project_dir=workspace,
        codex_bin=codex_bin,
        max_retries=max_retries,
        runner_type="local",
        model=model,
    )
    return Orchestrator(config, runner=DemoRunner()).run()


def materialize_sample_project(workspace: Path, *, force: bool = False) -> Path:
    if workspace.exists():
        if not force:
            raise FileExistsError(f"Workspace already exists: {workspace}")
        shutil.rmtree(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    copy_resource_tree(workspace, "resources", "demo_project")
    _initialize_git_repo(workspace)
    return workspace


def bundled_fixture_dir() -> Path:
    return Path("resources/demo_project")


def _initialize_git_repo(project_dir: Path) -> None:
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "demo@example.com"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Project Agent Demo"], cwd=project_dir, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init demo fixture"], cwd=project_dir, check=True, capture_output=True)


def _run_cli(project_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "inventory_report.cli", "data/items.yml"],
        cwd=project_dir,
        env=_target_env(project_dir),
        text=True,
        capture_output=True,
        check=False,
    )


def _run_pytest(project_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=project_dir,
        env=_target_env(project_dir),
        text=True,
        capture_output=True,
        check=False,
    )


def _target_env(project_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    target_src = project_dir / "src"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(target_src) if not existing else f"{target_src}{os.pathsep}{existing}"
    return env


def _check_completed(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)


def _result(role: Role, prompt: str, output_dir: Path) -> RoleRunResult:
    return RoleRunResult(
        role=role,
        command=["demo-runner"],
        prompt=prompt,
        returncode=0,
        stdout="ok",
        stderr="",
        final_message="done",
        output_dir=output_dir,
    )
