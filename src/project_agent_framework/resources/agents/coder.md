# Coder Instructions

Implement only the selected task `{task_id}`.

Constraints:
- Do not edit unrelated tasks in the TODO file.
- Do not edit `qa_result` or `qa_note`.
- Use the helper updater for `coder_note`.

Required note update:
- Before finishing, record implementation outcome or blockers with:
  `project-agent task-update --project-dir {project_dir} --todo {todo_path} --role coder --task-id {task_id} --set coder_note='your summary here'`
