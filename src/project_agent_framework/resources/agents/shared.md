# Shared Instructions

You are operating inside the target project at `{project_dir}`.

Use the target project's own PRD at `{prd_path}` and TODO at `{todo_path}`. Do not confuse those inputs with this framework repository's internal development files.

Keep changes deterministic and role-specific. Prefer the narrowest change that satisfies the current role.

Useful helper commands:
- `project-agent validate --project-dir {project_dir} --prd {prd_path} --todo {todo_path}`
- `project-agent task-read --project-dir {project_dir} --todo {todo_path} --task-id <TASK_ID>`
- `project-agent task-update --project-dir {project_dir} --todo {todo_path} --role coder --task-id <TASK_ID> --set coder_note='...'`
- `project-agent task-update --project-dir {project_dir} --todo {todo_path} --role qa --task-id <TASK_ID> --set qa_result=Pass --set qa_note='...'`
- `project-agent project-qa-update --project-dir {project_dir} --todo {todo_path} --role qa --result Pass --note '...'`

Do not mutate fields outside your role permissions.
