# Sample Target Project

This fixture is a realistic target repository for exercising the project agent framework.

The project goal is to build a small Python CLI that reads `data/items.yml` and prints an inventory summary grouped by status.

It intentionally starts incomplete:

- `src/inventory_report/report.py` has unimplemented reporting functions
- `src/inventory_report/cli.py` has an unimplemented CLI entrypoint
- `TODO.yml` defines three dependent tasks that the framework should drive to completion

