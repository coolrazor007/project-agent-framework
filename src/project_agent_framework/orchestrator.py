"""Deterministic orchestration loop for Architect, Coder, and QA."""

from __future__ import annotations

from pathlib import Path

from .constants import (
    DEFAULT_CODEX_BIN,
    DEFAULT_MAX_RETRIES,
    FRAMEWORK_DIRNAME,
)
from .exceptions import AgentRunError, FrameworkError, TodoValidationError
from .failure_summary import summarize_failure
from .git_tools import GitClient
from .logging_utils import RunLogger
from .models import OrchestratorConfig, ProjectPaths, ProjectQAResult, Role, RunSummary
from .prompts import build_role_prompt
from .runners import CodexRunner, build_runner
from .selection import select_next_task
from .todo import (
    is_project_task_complete,
    load_todo_document,
    refresh_backup,
    restore_backup,
    validate_role_mutation,
)


class Orchestrator:
    def __init__(
        self,
        config: OrchestratorConfig,
        *,
        runner: CodexRunner | None = None,
        git_client: GitClient | None = None,
    ) -> None:
        self.config = config
        self.paths = ProjectPaths.from_inputs(
            config.project_dir,
            config.prd_path,
            config.todo_path,
            config.backup_path,
            FRAMEWORK_DIRNAME,
            config.log_dir,
        )
        self.runner = runner or build_runner(config.runner_type)
        self.git_client = git_client or GitClient(config.project_dir)
        self.logger = RunLogger(self.paths.logs_dir)

    def run(self) -> RunSummary:
        self._validate_inputs()
        self.git_client.ensure_repo()
        loop_index = 1

        while True:
            if self.config.loop_limit is not None and loop_index > self.config.loop_limit:
                raise FrameworkError(f"Loop limit exceeded before project completion: {self.config.loop_limit}")
            refresh_backup(self.paths.todo_path, self.paths.backup_path)
            architect_doc = self._run_role_with_retries(role=Role.ARCHITECT, loop_index=loop_index)
            self.git_client.checkpoint(f"chore(agent): architect loop {loop_index}")

            if is_project_task_complete(architect_doc):
                if self.config.skip_final_qa:
                    return RunSummary(
                        completed=True,
                        loops=loop_index,
                        final_project_qa=architect_doc.project_qa.result,
                        project_dir=self.config.project_dir,
                    )
                if architect_doc.project_qa.result == ProjectQAResult.PASS.value:
                    return RunSummary(
                        completed=True,
                        loops=loop_index,
                        final_project_qa=architect_doc.project_qa.result,
                        project_dir=self.config.project_dir,
                    )

                final_doc = self._run_role_with_retries(
                    role=Role.QA,
                    loop_index=loop_index,
                    final_project_qa=True,
                )
                self.git_client.checkpoint(f"chore(agent): final qa loop {loop_index}")
                if final_doc.project_qa.result == ProjectQAResult.PASS.value:
                    return RunSummary(
                        completed=True,
                        loops=loop_index,
                        final_project_qa=final_doc.project_qa.result,
                        project_dir=self.config.project_dir,
                    )
                loop_index += 1
                continue

            task = select_next_task(architect_doc)
            self.logger.write_metadata(
                loop_index,
                "selected_task.json",
                {"task_id": task.id, "title": task.title},
            )
            self._run_role_with_retries(role=Role.CODER, loop_index=loop_index, task_id=task.id)
            self.git_client.checkpoint(f"chore(agent): coder {task.id} loop {loop_index}")
            self._run_role_with_retries(role=Role.QA, loop_index=loop_index, task_id=task.id)
            self.git_client.checkpoint(f"chore(agent): qa {task.id} loop {loop_index}")
            loop_index += 1

    def _validate_inputs(self) -> None:
        if not self.paths.prd_path.exists():
            raise FrameworkError(f"Target project is missing PRD.md: {self.paths.prd_path}")
        if not self.paths.todo_path.exists():
            raise FrameworkError(f"Target project is missing TODO.yml: {self.paths.todo_path}")
        load_todo_document(self.paths.todo_path)
        self.paths.framework_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        if not self.paths.backup_path.exists():
            refresh_backup(self.paths.todo_path, self.paths.backup_path)

    def _run_role_with_retries(
        self,
        *,
        role: Role,
        loop_index: int,
        task_id: str | None = None,
        final_project_qa: bool = False,
    ):
        retry_summary = ""
        project_prd = self.paths.prd_path.read_text(encoding="utf-8")

        for attempt in range(1, self.config.max_retries + 1):
            before = load_todo_document(self.paths.todo_path)
            task = before.task_map().get(task_id) if task_id else None
            prompt = build_role_prompt(
                role=role,
                project_dir=self.config.project_dir,
                prd_path=self.paths.prd_path,
                todo_path=self.paths.todo_path,
                project_prd=project_prd,
                document=before,
                retry_summary=retry_summary,
                task=task,
                final_project_qa=final_project_qa,
                shared_agents_path=self.config.shared_agents_path,
                architect_agents_path=self.config.architect_agents_path,
                coder_agents_path=self.config.coder_agents_path,
                qa_agents_path=self.config.qa_agents_path,
            )
            output_dir = self.logger.attempt_dir(loop_index, role, attempt)
            result = self.runner.run(
                role=role,
                prompt=prompt,
                output_dir=output_dir,
                config=self.config,
            )
            self.logger.write_result(result)

            if not result.succeeded:
                retry_summary = summarize_failure(
                    f"{role.value} exit code {result.returncode}",
                    result.stderr,
                    result.stdout,
                    result.final_message,
                )
                self.logger.write_metadata(
                    loop_index,
                    f"{role.value}_retry_{attempt}.json",
                    {"failure_summary": retry_summary},
                )
                continue

            try:
                after = load_todo_document(self.paths.todo_path)
                validate_role_mutation(
                    role,
                    before,
                    after,
                    task_id=task_id,
                    final_project_qa=final_project_qa,
                )
            except (TodoValidationError, FrameworkError) as exc:
                restore_backup(self.paths.todo_path, self.paths.backup_path)
                retry_summary = summarize_failure(str(exc), result.stderr, result.final_message)
                self.logger.write_metadata(
                    loop_index,
                    f"{role.value}_retry_{attempt}.json",
                    {"failure_summary": retry_summary},
                )
                continue

            refresh_backup(self.paths.todo_path, self.paths.backup_path)
            return after

        raise AgentRunError(
            f"{role.value} failed after {self.config.max_retries} attempts. Last failure: {retry_summary}"
        )


def make_default_config(
    *,
    project_dir: Path,
    prd_path: Path | None = None,
    todo_path: Path | None = None,
    backup_path: Path | None = None,
    log_dir: Path | None = None,
    shared_agents_path: Path | None = None,
    architect_agents_path: Path | None = None,
    coder_agents_path: Path | None = None,
    qa_agents_path: Path | None = None,
    codex_bin: str = DEFAULT_CODEX_BIN,
    max_retries: int = DEFAULT_MAX_RETRIES,
    runner_type: str = "local",
    skip_final_qa: bool = False,
    loop_limit: int | None = None,
    docker_image: str | None = None,
    model: str | None = None,
) -> OrchestratorConfig:
    return OrchestratorConfig(
        project_dir=project_dir,
        prd_path=prd_path,
        todo_path=todo_path,
        backup_path=backup_path,
        log_dir=log_dir,
        shared_agents_path=shared_agents_path,
        architect_agents_path=architect_agents_path,
        coder_agents_path=coder_agents_path,
        qa_agents_path=qa_agents_path,
        codex_bin=codex_bin,
        max_retries=max_retries,
        runner_type=runner_type,
        skip_final_qa=skip_final_qa,
        loop_limit=loop_limit,
        docker_image=docker_image,
        model=model,
    )
