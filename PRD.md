# PRD.md

## Title
Loop-Centric Codex CLI Agent Framework

## Purpose
Build a simple, programmatic, project-based agent framework that uses Codex CLI in a deterministic loop to implement software projects from a `PRD.md` and a structured `TODO.yml`.

The framework should emphasize:

- simplicity over cleverness
- deterministic orchestration over autonomous improvisation
- project progress through structured tasks
- strong guardrails around task updates
- clear separation of responsibilities between Architect, Coder, and QA roles

This is not intended to be a general autonomous agent platform in v1. It is intended to be a practical, loop-driven project executor for real repositories.

---

## Problem Statement
Interactive coding agents are useful, but they are often too open-ended for repeatable project execution. They can drift from the project plan, mutate task lists in unsafe ways, lose track of completion state, or make changes outside their intended role.

A simpler and more reliable approach is needed:

- start from a project `PRD.md`
- maintain a structured `TODO.yml`
- run role-specific agent passes in a fixed loop
- keep the orchestrator in control
- allow progress, retries, pivots, and completion to be determined programmatically

---

## Goals

### Primary Goals
1. Use `PRD.md` as the project intent document.
2. Use `TODO.yml` as the authoritative structured task backlog.
3. Run a deterministic loop of:
   - Architect Agent
   - Coder Agent
   - QA Agent
4. Enforce role-specific responsibilities and permitted task mutations.
5. End the loop programmatically when all tasks reach terminal QA outcomes.
6. Keep implementation simple and debuggable.
7. Support safe retries with summarized failure context.
8. Use Git checkpoints heavily for rollback and traceability.
9. Minimize unnecessary context sent to each agent.
10. Be implementable in Python first.

### Secondary Goals
1. Support optional Docker-based isolation for agent execution.
2. Support a final whole-project QA pass after task-level completion.
3. Leave room for future browser/UI verification without making it a v1 dependency.

---

## Non-Goals
The following are explicitly out of scope for v1:

1. Multi-project orchestration
2. Distributed execution across many machines
3. Complex autonomous planning beyond task management
4. Dynamic team composition or extra agent roles
5. Human-in-the-loop approval workflows
6. Rich web dashboard or GUI
7. Sophisticated memory systems
8. Full-blown browser automation as a required dependency
9. General-purpose plugin framework
10. Replacing Codex CLI with Codex SDK in v1

---

## Target User
The target user is a technical developer or operator who:

- works in a real source repository
- prefers deterministic automation over chat-first workflows
- wants agents to operate within strict role boundaries
- is comfortable with Python and Git
- may optionally prefer Docker-based isolation
- wants project progress to be measurable from files on disk

---

## Core Concept
The framework runs a loop around a repository.

The loop is controlled by a Python orchestrator script. The orchestrator reads `PRD.md` and `TODO.yml`, decides what stage to run next, invokes Codex CLI with the appropriate role instructions, validates outputs, performs retries if needed, writes logs, and checkpoints with Git.

Each role has a narrow responsibility:

- **Architect Agent**
  - manages the task backlog in `TODO.yml`
  - ensures work remains aligned to `PRD.md`
  - may add, remove, reorder, split, or revise tasks
  - may pivot implementation approach when needed
  - must preserve structured validity

- **Coder Agent**
  - implements one selected task at a time
  - focuses only on that task
  - may edit project code and related files
  - may update only the task's `coder_note` through approved mechanisms
  - may explain blockers or design issues through `coder_note`

- **QA Agent**
  - verifies one selected task at a time
  - validates functionally against acceptance criteria
  - may perform light test and smoke verification
  - may update only `qa_result` and `qa_note` through approved mechanisms

The orchestrator remains the trusted controller.

---

## Key Principles

### 1. KISS First
The framework must prefer the simplest implementation that works. If a feature introduces complexity without materially improving reliability, it should be deferred.

### 2. Structured State
Project task state must live in `TODO.yml`, not in freeform markdown.

### 3. Orchestrator Authority
Agents do work. The orchestrator validates and controls state transitions.

### 4. Narrow Prompts
Each agent should receive only the minimum relevant project/task context necessary.

### 5. Role Isolation
Each role should have distinct instructions and restricted permissions.

### 6. Safe Mutation
Changes to `TODO.yml` should be validated and ideally mediated through helper scripts.

### 7. Heavy Traceability
All important actions should be logged and checkpointed.

### 8. Programmatic Completion
Project completion must be determined by code, not by agent opinion.

---

## Functional Requirements

## FR-1: Project Inputs
The framework must operate on a project directory containing at minimum:

- `PRD.md`
- `TODO.yml`

Optional files may include:

- `TODO.yml.bak`
- shared and role-specific `AGENTS.md` files
- orchestrator support scripts
- project codebase

### Acceptance Criteria
- Framework fails clearly if `PRD.md` or `TODO.yml` is missing.
- Framework validates that `TODO.yml` is parseable before execution.
- Framework can initialize backup state if `TODO.yml.bak` does not exist.

---

## FR-2: TODO.yml as Source of Truth
The framework must treat `TODO.yml` as the authoritative project backlog and task state file.

Each task must be machine-readable and include required structured fields.

### Minimum Required Task Fields
- `id`
- `title`
- `description`
- `acceptance_criteria`
- `priority`
- `status`
- `qa_result`
- `coder_note`
- `qa_note`
- `depends_on`

### Acceptance Criteria
- Framework validates required fields on load.
- Framework rejects malformed tasks or invalid enum values.
- Framework detects duplicate task IDs.
- Framework can determine task completion status programmatically.

---

## FR-3: TODO Backup
The framework must maintain a backup copy of the task file as `TODO.yml.bak`.

### Acceptance Criteria
- Backup is refreshed before or during Architect processing.
- On invalid mutation or corruption, framework can restore from backup.
- Backup behavior is automated and requires no manual intervention.

---

## FR-4: Architect Agent
The framework must support an Architect role responsible for backlog management and alignment with `PRD.md`.

### Architect Responsibilities
- review `PRD.md`
- review current `TODO.yml`
- ensure tasks remain aligned to project goals
- add/remove/revise/reorder tasks as needed
- preserve logical implementation order
- handle pivots when Coder or QA feedback reveals a mismatch or blocker
- avoid unnecessary churn

### Architect Constraints
- should not modify source code in v1
- should not mark tasks as QA-passed without QA verification
- must preserve valid task structure

### Acceptance Criteria
- Architect run can revise task plan without corrupting `TODO.yml`.
- Architect can respond to blocker notes from other roles.
- Architect can make conservative pivots while preserving PRD intent.

---

## FR-5: Coder Agent
The framework must support a Coder role that works one task at a time.

### Coder Responsibilities
- receive one selected task
- implement that task thoroughly
- run relevant local commands when appropriate
- update only task-specific coding feedback via approved mechanism
- explain blockers or invalid assumptions in `coder_note`

### Coder Constraints
- must not edit unrelated tasks
- must not edit `qa_result`
- must not restructure backlog
- must remain focused on the selected task

### Acceptance Criteria
- Coder receives only necessary task context.
- Coder can modify project files as needed for implementation.
- Coder can leave a clear `coder_note` when implementation reveals issues.

---

## FR-6: QA Agent
The framework must support a QA role that verifies one selected task at a time.

### QA Responsibilities
- validate against task acceptance criteria
- run tests or lightweight checks where possible
- perform limited smoke/UI verification when practical
- set `qa_result`
- write `qa_note` when needed

### QA Constraints
- should not restructure tasks
- should not edit project code in v1
- should keep UI/UX expectations modest in task-level QA
- must provide useful feedback on Fail or Blocked results

### Acceptance Criteria
- QA can mark a task as Pass, Fail, Blocked, Not Applicable, or Removed.
- QA writes explanatory notes for non-pass results.
- QA does not modify unrelated task fields.

---

## FR-7: Task Selection
The framework must programmatically select the next task for the Coder and QA stages.

### Initial v1 Selection Rule
Tasks should be processed in logical order as maintained by the Architect, using simple ordered selection.

A task is eligible when:
- it is not already terminal
- it is not removed
- its dependencies are satisfied
- it is not blocked by unresolved prerequisites

### Acceptance Criteria
- Selection logic is deterministic.
- Dependency satisfaction is checked before assignment.
- Framework can detect when no runnable tasks remain.

---

## FR-8: Programmatic Completion
The framework must determine project completion from `TODO.yml`.

### v1 Terminal QA Results
Accepted terminal values:
- `Pass`
- `Not Applicable`
- `Removed`

The project is considered task-complete when all tasks have terminal `qa_result` values.

### Acceptance Criteria
- Completion check is code-based.
- No agent is allowed to unilaterally declare the whole project complete.
- Framework transitions to full-project QA after task-complete condition is met.

---

## FR-9: Full Project QA Pass
After all tasks reach terminal QA status, the framework must support a final whole-project QA pass.

### Purpose
Task-by-task verification may miss integration or regression issues. A final project pass provides a broader confidence check.

### Expected Scope
- re-check completed tasks at a higher level
- run broader smoke tests
- validate integration behavior where practical
- optionally capture screenshots or evidence in future iterations

### Acceptance Criteria
- Framework can launch a final QA review stage.
- Issues found in final QA can reopen or spawn follow-up tasks.
- Project is not truly complete until full-project QA passes.

---

## FR-10: Retry Handling
The framework must retry failed role runs up to 3 times.

### Retry Behavior
Each retry should receive a compact failure summary describing why the previous attempt failed.

Examples of retry causes:
- invalid file mutation
- invalid enum values
- missing required field updates
- command failure
- parsing failure
- test failure
- invalid role behavior

### Acceptance Criteria
- Maximum retries per run is configurable and defaults to 3.
- Retry prompts include previous failure summaries.
- Framework stops retrying after limit is reached and escalates appropriately.

---

## FR-11: Helper Scripts for Safe State Updates
The framework should use helper scripts to safely read and update structured task state.

### Expected Helper Utilities
- task reader utility
- task updater utility
- YAML validator utility
- failure summarizer utility

### Purpose
Reduce prompt size, reduce YAML corruption risk, enforce role-based field permissions, and improve determinism.

### Acceptance Criteria
- Helper scripts can be invoked by orchestrator and/or agents.
- Field-level update permissions are enforceable.
- Invalid updates are rejected clearly.

---

## FR-12: Git Checkpointing
The framework must use Git checkpoints heavily.

### Expected Checkpoint Moments
- before Architect stage
- after successful Architect updates
- after Coder stage
- after QA stage
- before/after final project QA as needed

### Acceptance Criteria
- Checkpoints are automatic.
- Commit messages are structured and readable.
- Framework can restore to a known-good state on failure.

---

## FR-13: Logging and Run History
The framework must record enough artifacts to debug and audit each loop.

### Required Logged Data
- prompts or prompt references
- stdout/stderr for each run
- summarized result metadata
- retry history
- loop-level summary

### Acceptance Criteria
- Each loop iteration creates a traceable run record.
- Failures are inspectable after the fact.
- Logs are organized per role and per loop.

---

## FR-14: Role-Specific Instructions
The framework must support distinct role instructions.

### v1 Requirement
Each role should have its own instruction file or equivalent role-specific prompt layer.

### Acceptance Criteria
- Architect, Coder, and QA each receive role-appropriate guidance.
- Shared project rules can be combined with role-specific rules.
- Swapping role instructions does not require changing orchestration logic.

---

## FR-15: Optional Docker Isolation
The framework should support optional containerized agent execution.

### Purpose
Provide a safer execution environment and allow mount-based access control.

### Desired Characteristics
- orchestrator may run on host
- roles may run in containers
- bind mounts can constrain writable files
- backup files can be isolated from non-owner roles

### Acceptance Criteria
- Framework can be run locally without Docker in v1.
- Framework can optionally use Docker Compose or equivalent runner isolation.
- Role execution can be abstracted behind a runner interface.

---

## Data Model Requirements

## Task Fields
Each task in `TODO.yml` should support the following v1 fields:

- `id`: stable unique identifier
- `title`: short human-readable title
- `description`: implementation-oriented description
- `acceptance_criteria`: list of verifiable outcomes
- `priority`: numeric or simple ordered field
- `status`: current planning/execution state
- `qa_result`: QA verdict
- `coder_note`: coder-only implementation note
- `qa_note`: QA-only verification note
- `architect_note`: optional architect note
- `depends_on`: list of task IDs
- `files_touched`: optional list for audit/debugging
- `retry_count`: optional per-role retry tracking
- `history`: optional structured event history

## Enum Requirements

### status
Allowed v1 values:
- `Pending`
- `Ready`
- `In Progress`
- `Blocked`
- `Done`
- `Removed`

### qa_result
Allowed v1 values:
- `Pending`
- `Pass`
- `Fail`
- `Blocked`
- `Not Applicable`
- `Removed`

---

## Orchestration Flow

## High-Level Loop
1. Validate required project files.
2. Load and validate `TODO.yml`.
3. Refresh `TODO.yml.bak`.
4. Run Architect Agent.
5. Validate Architect output.
6. Check project completion state.
7. If not complete, select next eligible task.
8. Run Coder Agent for one task.
9. Validate post-Coder state.
10. Run QA Agent for the same task.
11. Validate post-QA state.
12. Create Git checkpoint(s).
13. Repeat until task-complete.
14. Run full-project QA.
15. End only after full-project QA passes.

### Acceptance Criteria
- Loop is deterministic.
- All critical state transitions are validated.
- Failure and retry paths are explicit.
- End condition is code-based.

---

## Failure Handling

## Failure Categories
1. Invalid YAML
2. Forbidden field mutation
3. Missing required field update
4. Duplicate IDs
5. Dependency cycle or invalid dependency reference
6. Codex CLI command failure
7. Build/test failure
8. QA verification failure
9. No runnable tasks
10. Repeated agent noncompliance

## Expected Framework Response
Depending on category, framework should:
- retry with failure summary
- restore from backup
- restore from Git checkpoint
- escalate to Architect
- mark task blocked
- abort with clear error when necessary

### Acceptance Criteria
- Failure handling paths are explicit in code.
- Framework prefers recovery before aborting.
- Repeated noncompliance does not silently corrupt project state.

---

## UX Expectations for v1

### Operator Experience
The operator should be able to:
- point the framework at a project directory
- run a single Python command to start the loop
- inspect logs and Git history when something goes wrong
- understand current state from `TODO.yml` and loop output

### v1 UX Constraints
- no rich GUI required
- CLI-first operation is acceptable
- human readability of YAML and logs matters
- boring is good

---

## Technical Constraints
1. Implementation language should be Python.
2. Task state should use YAML, not JSON.
3. Codex CLI should be the initial execution mechanism.
4. Framework should work with one Git branch and many commits.
5. Role boundaries should be enforced programmatically where possible.
6. Task-level UI verification should remain limited in v1.
7. Full browser automation should be optional and deferred.

---

## Success Criteria

The project is successful when:

1. A repository with `PRD.md` and `TODO.yml` can be processed by the framework.
2. Architect can maintain a valid structured backlog.
3. Coder can implement one task at a time without mutating task structure.
4. QA can verify one task at a time and set structured outcomes.
5. Retries work with summarized prior failure context.
6. Git checkpoints provide recovery and traceability.
7. Full-project QA can run after task-level completion.
8. The framework ends automatically when completion conditions are satisfied.
9. The system remains understandable without needing a diagram the size of a pirate treasure map.

---

## Nice-to-Have Future Enhancements
These are explicitly deferred beyond v1:

1. richer browser/UI automation
2. screenshot-based QA evidence
3. role-specific model selection policies
4. parallelizable future task analysis
5. richer dependency planning
6. metrics dashboards
7. human approval gates
8. Codex SDK migration
9. persistent analytics across many projects
10. smarter project templates and bootstrapping

---

## Open Questions
These may be resolved during implementation but should not block v1:

1. Should helper scripts be called directly by agents, or should agents emit structured intent that the orchestrator applies?
2. How strict should write access be for containerized roles?
3. Should `status` be mostly orchestrator-driven, agent-driven, or mixed?
4. How much project context should be passed to Coder and QA beyond the current task?
5. What minimal smoke-test strategy should QA use for UI-heavy projects?
6. Should final project QA reopen existing tasks or create new regression tasks?

---

## Recommended v1 Delivery Scope
The first usable version should include:

- Python orchestrator
- YAML schema validation
- backup/restore logic
- Architect/Coder/QA role loop
- deterministic task selection
- per-role retries with failure summaries
- helper scripts for task reading/updating
- Git checkpointing
- final whole-project QA pass
- optional but not required Docker runner abstraction

Anything beyond that should be treated as v2 unless it materially improves reliability without increasing complexity much.

---
