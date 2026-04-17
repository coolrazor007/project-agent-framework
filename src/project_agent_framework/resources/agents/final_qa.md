# Final Project QA Instructions

Run a whole-project QA pass. Re-check integration and broader smoke behavior.

Constraints:
- Do not edit source code.
- Do not edit tasks.
- Update only the top-level `project_qa` state using:
  `project-agent project-qa-update --project-dir {project_dir} --todo {todo_path} --role qa --result <Pass|Fail|Blocked> --note 'integration summary'`
