# Project Agent Framework

`project-agent-framework` is a Python package and CLI for running a deterministic Codex loop against a target repository. The intended distribution model is PyPI:

```bash
pip install project-agent-framework
```

It exposes the `project-agent` command.

This repository's own [PRD.md](/mnt/c/Users/razor/OneDrive/Documents/repos/project_agent_framework/PRD.md) describes the framework itself. When you use the tool on your own project, you point it at your project's own PRD and TODO files.

## Core Model

- The target repo owns `PRD.md` and `TODO.yml`.
- The framework owns orchestration, validation, retries, logs, and git checkpoints.
- Architect can revise backlog structure.
- Coder can implement one selected task and update only `coder_note`.
- QA can verify one selected task and update only `qa_result` and `qa_note`.

Runtime artifacts are written under `.project_agent/` in the target repo unless you override the log path.

## Installation

Published-package workflow:

```bash
pip install project-agent-framework
```

Local development workflow from this checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

You can also run directly from the checkout without installing:

```bash
python scripts/run_framework.py <command> ...
```

## New Project Workflow

Bootstrap a fresh repository:

```bash
project-agent init --project-dir /path/to/project --write-agent-overrides
```

That creates starter files:

- `PRD.md`
- `TODO.yml`
- `AGENTS.shared.md`
- `AGENTS.architect.md`
- `AGENTS.coder.md`
- `AGENTS.qa.md`

Initialize git in the target repo if needed:

```bash
cd /path/to/project
git init
```

Then run the framework:

```bash
project-agent run --project-dir /path/to/project
```

## Important CLI Arguments

The normal command is:

```bash
project-agent run --project-dir /path/to/project
```

Useful overrides:

```bash
project-agent run \
  --project-dir /path/to/project \
  --prd docs/PRD.product.md \
  --todo planning/TODO.yml \
  --todo-backup planning/TODO.backup.yml \
  --shared-agents AGENTS.shared.md \
  --architect-agents AGENTS.architect.md \
  --coder-agents AGENTS.coder.md \
  --qa-agents AGENTS.qa.md \
  --model gpt-5.4 \
  --max-retries 3 \
  --loop-limit 20
```

Available commands:

- `project-agent init`
- `project-agent run`
- `project-agent validate`
- `project-agent task-read`
- `project-agent task-update`
- `project-agent project-qa-update`
- `project-agent demo`
- `project-agent materialize-demo`

## AGENTS Overrides

The package ships with default role instructions inside the wheel. You can layer project-specific constraints on top of them by passing:

- `--shared-agents`
- `--architect-agents`
- `--coder-agents`
- `--qa-agents`

Those files are appended to the packaged defaults before each agent run.

## Minimal TODO.yml

```yaml
tasks:
  - id: T-001
    title: Build CLI entrypoint
    description: Implement the operator-facing command.
    acceptance_criteria:
      - Command exits with status 0
    priority: 1
    status: Ready
    qa_result: Pending
    coder_note: ""
    qa_note: ""
    depends_on: []
project_qa:
  result: Pending
  note: ""
```

Allowed `status` values:

- `Pending`
- `Ready`
- `In Progress`
- `Blocked`
- `Done`
- `Removed`

Allowed `qa_result` values:

- `Pending`
- `Pass`
- `Fail`
- `Blocked`
- `Not Applicable`
- `Removed`

## Demo

Run the packaged sample project demo without spending live Codex calls:

```bash
project-agent demo --workspace /tmp/project-agent-demo --force
```

From a raw checkout:

```bash
python scripts/run_demo.py --workspace /tmp/project-agent-demo --force
```

The demo materializes a bundled sample target repo, initializes git, runs a deterministic Architect/Coder/QA loop, and leaves logs in the demo workspace.

## Publishing Notes

This repo is structured for GitHub Actions Trusted Publishing. The release workflow is [release.yml](/mnt/c/Users/razor/OneDrive/Documents/repos/project_agent_framework/.github/workflows/release.yml), and the step-by-step release runbook is [PUBLISHING.md](/mnt/c/Users/razor/OneDrive/Documents/repos/project_agent_framework/PUBLISHING.md).
