"""Role execution runners for Codex CLI."""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from .models import OrchestratorConfig, Role, RoleRunResult


class CodexRunner(ABC):
    @abstractmethod
    def run(
        self,
        *,
        role: Role,
        prompt: str,
        output_dir: Path,
        config: OrchestratorConfig,
    ) -> RoleRunResult:
        """Run a single role pass."""


class LocalCodexRunner(CodexRunner):
    def run(
        self,
        *,
        role: Role,
        prompt: str,
        output_dir: Path,
        config: OrchestratorConfig,
    ) -> RoleRunResult:
        final_message_path = output_dir / "last_message.txt"
        command = [config.codex_bin, "exec"]
        if config.model:
            command.extend(["--model", config.model])
        command.extend(
            [
                "--cd",
                str(config.project_dir),
                "--sandbox",
                "workspace-write",
                "--output-last-message",
                str(final_message_path),
                "-",
            ]
        )
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        final_message = ""
        if final_message_path.exists():
            final_message = final_message_path.read_text(encoding="utf-8")
        return RoleRunResult(
            role=role,
            command=command,
            prompt=prompt,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            final_message=final_message,
            output_dir=output_dir,
        )


class DockerCodexRunner(CodexRunner):
    def run(
        self,
        *,
        role: Role,
        prompt: str,
        output_dir: Path,
        config: OrchestratorConfig,
    ) -> RoleRunResult:
        if not config.docker_image:
            raise ValueError("docker_image is required when runner_type='docker'.")
        mounted_output_dir = Path("/workspace/.project_agent/logs") / output_dir.relative_to(
            config.project_dir / ".project_agent" / "logs"
        )
        final_message_path = output_dir / "last_message.txt"
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "-v",
            f"{config.project_dir}:/workspace",
            "-w",
            "/workspace",
            config.docker_image,
            config.codex_bin,
            "exec",
        ]
        if config.model:
            command.extend(["--model", config.model])
        command.extend(
            [
                "--cd",
                "/workspace",
                "--sandbox",
                "workspace-write",
                "--output-last-message",
                str(mounted_output_dir / "last_message.txt"),
                "-",
            ]
        )
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        final_message = ""
        if final_message_path.exists():
            final_message = final_message_path.read_text(encoding="utf-8")
        return RoleRunResult(
            role=role,
            command=command,
            prompt=prompt,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            final_message=final_message,
            output_dir=output_dir,
        )


def build_runner(runner_type: str) -> CodexRunner:
    if runner_type == "local":
        return LocalCodexRunner()
    if runner_type == "docker":
        return DockerCodexRunner()
    raise ValueError(f"Unsupported runner_type: {runner_type}")
