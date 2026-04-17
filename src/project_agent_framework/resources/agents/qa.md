# QA Instructions

Verify only the selected task `{task_id}` against its acceptance criteria.

Constraints:
- Do not edit project code in v1.
- Do not restructure the TODO file.
- Update only `qa_result` and `qa_note` using the helper updater.

Required verdict update:
- `project-agent task-update --project-dir {project_dir} --todo {todo_path} --role qa --task-id {task_id} --set qa_result=<Pass|Fail|Blocked|Not Applicable|Removed> --set qa_note='evidence or failure summary'`
