# Inventory Summary CLI

## Purpose
Build a small Python command-line tool that reads `data/items.yml`, normalizes the item records, and prints a concise status summary for operators.

## Goals
- Load inventory records from YAML.
- Normalize missing or mixed-case fields into a consistent internal shape.
- Print a deterministic text summary grouped by status.
- Add regression tests for report generation and CLI output.

## Non-Goals
- No database integration.
- No web UI.
- No write-back editing of the input file.

## Acceptance Criteria
- `load_items()` returns normalized item dictionaries.
- `count_by_status()` returns accurate counts by normalized status.
- `python -m inventory_report.cli data/items.yml` exits successfully and prints a stable summary.
- Regression tests cover report and CLI behavior.
