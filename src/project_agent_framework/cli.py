"""CLI entrypoints for orchestration and helper utilities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bootstrap import init_project
from .constants import DEFAULT_CODEX_BIN, DEFAULT_MAX_RETRIES
from .demo import materialize_sample_project, run_demo
from .failure_summary import summarize_failure, summarize_failure_files
from .models import Role
from .orchestrator import Orchestrator, make_default_config
from .todo import load_todo_document, task_snapshot, update_project_qa, update_task_fields


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project-agent",
        description="Deterministic loop-driven Codex CLI agent framework.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the orchestrator against a target project.")
    _add_project_arg(run_parser)
    _add_prd_arg(run_parser)
    _add_todo_arg(run_parser)
    run_parser.add_argument("--todo-backup", type=Path)
    run_parser.add_argument("--log-dir", type=Path)
    _add_agent_override_args(run_parser)
    run_parser.add_argument("--codex-bin", default=DEFAULT_CODEX_BIN)
    run_parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    run_parser.add_argument("--runner", choices=("local", "docker"), default="local")
    run_parser.add_argument("--docker-image")
    run_parser.add_argument("--model")
    run_parser.add_argument("--skip-final-qa", action="store_true")
    run_parser.add_argument("--loop-limit", type=int)

    init_parser = subparsers.add_parser("init", help="Bootstrap a new target repo with starter PRD/TODO files.")
    _add_project_arg(init_parser)
    _add_prd_arg(init_parser)
    _add_todo_arg(init_parser)
    _add_agent_override_args(init_parser)
    init_parser.add_argument("--write-agent-overrides", action="store_true")
    init_parser.add_argument("--force", action="store_true")

    demo_parser = subparsers.add_parser(
        "demo",
        help="Materialize the bundled sample target project and run the loop with a deterministic demo runner.",
    )
    demo_parser.add_argument("--workspace", type=Path, required=True)
    demo_parser.add_argument("--force", action="store_true")
    demo_parser.add_argument("--codex-bin", default=DEFAULT_CODEX_BIN)
    demo_parser.add_argument("--max-retries", type=int, default=2)
    demo_parser.add_argument("--model")

    materialize_parser = subparsers.add_parser(
        "materialize-demo",
        help="Copy the bundled sample target project into a workspace without running the loop.",
    )
    materialize_parser.add_argument("--workspace", type=Path, required=True)
    materialize_parser.add_argument("--force", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Validate PRD/TODO inputs for a target project.")
    _add_project_arg(validate_parser)
    _add_prd_arg(validate_parser)
    _add_todo_arg(validate_parser)

    validate_todo_parser = subparsers.add_parser("validate-todo", help="Backward-compatible alias for validate.")
    _add_project_arg(validate_todo_parser)
    _add_todo_arg(validate_todo_parser)

    read_parser = subparsers.add_parser("task-read", help="Print one task or the full TODO state as JSON.")
    _add_project_arg(read_parser)
    _add_todo_arg(read_parser)
    read_parser.add_argument("--task-id")

    update_parser = subparsers.add_parser("task-update", help="Role-safe task field update helper.")
    _add_project_arg(update_parser)
    _add_todo_arg(update_parser)
    update_parser.add_argument("--role", choices=("coder", "qa"), required=True)
    update_parser.add_argument("--task-id", required=True)
    update_parser.add_argument(
        "--set",
        action="append",
        required=True,
        help="Field update in key=value form. Allowed keys depend on role.",
    )

    project_qa_parser = subparsers.add_parser("project-qa-update", help="Update top-level project QA state.")
    _add_project_arg(project_qa_parser)
    _add_todo_arg(project_qa_parser)
    project_qa_parser.add_argument("--role", choices=("qa",), required=True)
    project_qa_parser.add_argument("--result", required=True)
    project_qa_parser.add_argument("--note", default="")

    summary_parser = subparsers.add_parser("failure-summary", help="Summarize failure text or log files.")
    summary_parser.add_argument("--message")
    summary_parser.add_argument("--file", type=Path, action="append")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        project_dir = args.project_dir.resolve()
        config = make_default_config(
            project_dir=project_dir,
            prd_path=_resolve_path(project_dir, args.prd, default_name="PRD.md"),
            todo_path=_resolve_path(project_dir, args.todo, default_name="TODO.yml"),
            backup_path=_resolve_path(project_dir, args.todo_backup, default_name="TODO.yml.bak"),
            log_dir=_resolve_path(project_dir, args.log_dir),
            shared_agents_path=_resolve_path(project_dir, args.shared_agents),
            architect_agents_path=_resolve_path(project_dir, args.architect_agents),
            coder_agents_path=_resolve_path(project_dir, args.coder_agents),
            qa_agents_path=_resolve_path(project_dir, args.qa_agents),
            codex_bin=args.codex_bin,
            max_retries=args.max_retries,
            runner_type=args.runner,
            skip_final_qa=args.skip_final_qa,
            loop_limit=args.loop_limit,
            docker_image=args.docker_image,
            model=args.model,
        )
        summary = Orchestrator(config).run()
        print(
            json.dumps(
                {
                    "completed": summary.completed,
                    "loops": summary.loops,
                    "final_project_qa": summary.final_project_qa,
                    "project_dir": str(summary.project_dir),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "init":
        project_dir = args.project_dir.resolve()
        shared_agents = None
        architect_agents = None
        coder_agents = None
        qa_agents = None
        if args.write_agent_overrides:
            shared_agents = _resolve_path(project_dir, args.shared_agents, default_name="AGENTS.shared.md")
            architect_agents = _resolve_path(project_dir, args.architect_agents, default_name="AGENTS.architect.md")
            coder_agents = _resolve_path(project_dir, args.coder_agents, default_name="AGENTS.coder.md")
            qa_agents = _resolve_path(project_dir, args.qa_agents, default_name="AGENTS.qa.md")
        created = init_project(
            prd_path=_resolve_path(project_dir, args.prd, default_name="PRD.md"),
            todo_path=_resolve_path(project_dir, args.todo, default_name="TODO.yml"),
            shared_agents_path=shared_agents,
            architect_agents_path=architect_agents,
            coder_agents_path=coder_agents,
            qa_agents_path=qa_agents,
            force=args.force,
        )
        print(json.dumps(created, indent=2))
        return 0

    if args.command == "demo":
        summary = run_demo(
            args.workspace.resolve(),
            force=args.force,
            codex_bin=args.codex_bin,
            max_retries=args.max_retries,
            model=args.model,
        )
        print(
            json.dumps(
                {
                    "completed": summary.completed,
                    "loops": summary.loops,
                    "final_project_qa": summary.final_project_qa,
                    "workspace": str(args.workspace.resolve()),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "materialize-demo":
        workspace = materialize_sample_project(args.workspace.resolve(), force=args.force)
        print(json.dumps({"workspace": str(workspace)}, indent=2))
        return 0

    if args.command in {"validate", "validate-todo"}:
        project_dir = args.project_dir.resolve()
        prd_path = _resolve_path(project_dir, getattr(args, "prd", None), default_name="PRD.md")
        todo_path = _resolve_path(project_dir, args.todo, default_name="TODO.yml")
        if args.command == "validate" and not prd_path.exists():
            raise SystemExit(f"Missing PRD file: {prd_path}")
        document = load_todo_document(todo_path)
        print(
            json.dumps(
                {
                    "valid": True,
                    "project_dir": str(project_dir),
                    "prd": str(prd_path),
                    "todo": str(todo_path),
                    "task_count": len(document.tasks),
                    "project_qa": document.project_qa.to_dict(),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "task-read":
        todo_path = _resolve_path(args.project_dir.resolve(), args.todo, default_name="TODO.yml")
        document = load_todo_document(todo_path)
        payload = task_snapshot(document, args.task_id) if args.task_id else document.to_dict()
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "task-update":
        updates = _parse_updates(args.set)
        document = update_task_fields(
            _resolve_path(args.project_dir.resolve(), args.todo, default_name="TODO.yml"),
            args.task_id,
            Role(args.role),
            updates,
        )
        print(json.dumps(document.to_dict(), indent=2))
        return 0

    if args.command == "project-qa-update":
        document = update_project_qa(
            _resolve_path(args.project_dir.resolve(), args.todo, default_name="TODO.yml"),
            Role(args.role),
            args.result,
            args.note,
        )
        print(json.dumps(document.to_dict(), indent=2))
        return 0

    if args.command == "failure-summary":
        if args.file:
            print(summarize_failure_files(*args.file))
        else:
            print(summarize_failure(args.message or ""))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _parse_updates(items: list[str]) -> dict[str, str]:
    updates: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Invalid update '{item}'. Expected key=value.")
        key, value = item.split("=", 1)
        updates[key] = value
    return updates


def _add_project_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-dir", type=Path, default=Path("."))


def _add_prd_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prd", type=Path)


def _add_todo_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--todo", type=Path)


def _add_agent_override_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--shared-agents", type=Path)
    parser.add_argument("--architect-agents", type=Path)
    parser.add_argument("--coder-agents", type=Path)
    parser.add_argument("--qa-agents", type=Path)


def _resolve_path(project_dir: Path, value: Path | None, *, default_name: str | None = None) -> Path | None:
    if value is None:
        if default_name is None:
            return None
        return (project_dir / default_name).resolve()
    if value.is_absolute():
        return value.resolve()
    return (project_dir / value).resolve()


if __name__ == "__main__":
    sys.exit(main())
