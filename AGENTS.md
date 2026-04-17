# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a clean scaffold, so adopt the following layout for contributions:

- `src/` – application code (group by feature, e.g., `src/agent/`, `src/core/`).
- `tests/` – automated tests aligned with `src/` paths (e.g., `tests/test_agent.py`).
- `assets/` – images, prompts, sample files, and non-runtime data.
- `docs/` – design notes, API specs, and release notes.
- `scripts/` – local utility scripts for setup and maintenance.

Use explicit paths in PRs when adding new modules so reviewers can quickly locate touched areas.

## Build, Test, and Development Commands
No build pipeline is defined yet in this repository. Use these baseline commands once dependencies are added:

- `python -m venv .venv && source .venv/bin/activate` – create an isolated environment.
- `pip install -r requirements.txt` (or lock-file equivalent) – install dependencies.
- `pytest` – run the full test suite.
- `pytest tests/test_<area>.py` – run targeted tests while developing.
- `python -m <entrypoint>` – run local services/CLI entrypoints.

When project tooling is introduced, keep these in a `Makefile` or `scripts/dev.sh` and document overrides there.

## Coding Style & Naming Conventions
- Use 4-space indentation and UTF-8 files.
- Keep files focused; prefer one primary responsibility per module.
- Naming: `snake_case` for files/functions/variables, `PascalCase` for classes/types.
- Use `snake_case` directory and module names unless project language convention differs.
- Formatters/linters: add and enforce in CI once available (`ruff`, `black`, `prettier`, `eslint`, etc.).

## Testing Guidelines
- Add tests for each functional change and bug fix.
- Test naming: `test_*.py` for Python (`pytest`) or `*.test.js`/`*.spec.ts` for JS/TS.
- Favor deterministic tests; mock external I/O and APIs.
- New behavior should include at least one positive and one edge/negative case.
- Target fast feedback locally; run targeted tests before full suite.

## Commit & Pull Request Guidelines
No commit history is present in this checkout, so follow Conventional Commit style:

- `feat(scope): ...`
- `fix(scope): ...`
- `docs(scope): ...`
- `test(scope): ...`

Each PR should include:
- Summary of what changed and why.
- Test commands executed and outcomes.
- Linked issue/plan reference.
- Notes on any configuration or migration impacts.

## Security & Configuration Notes
- Never commit secrets, credentials, API keys, `.env` files, or raw user data.
- Keep runtime config in environment variables or `.env.example`.
- Document required environment values in `docs/` before merging. 
