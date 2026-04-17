"""Git checkpoint helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .exceptions import GitCheckpointError


class GitClient:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    def ensure_repo(self) -> None:
        completed = self._run("rev-parse", "--is-inside-work-tree")
        if completed.returncode != 0 or completed.stdout.strip() != "true":
            raise GitCheckpointError(f"Target project is not a git repository: {self.project_dir}")

    def checkpoint(self, message: str) -> str | None:
        self._run("add", "-A", check=True)
        diff = self._run("diff", "--cached", "--quiet")
        if diff.returncode == 0:
            return None
        commit = self._run("commit", "-m", message, check=True)
        return commit.stdout.strip()

    def current_head(self) -> str:
        completed = self._run("rev-parse", "HEAD", check=True)
        return completed.stdout.strip()

    def _run(self, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.project_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and completed.returncode != 0:
            raise GitCheckpointError(
                f"git {' '.join(args)} failed: {completed.stderr.strip() or completed.stdout.strip()}"
            )
        return completed

