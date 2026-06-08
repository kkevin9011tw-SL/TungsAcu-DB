# TungsAcu-DB Workspace Rules

## Canonical workspace

The only writable development repository is:

```text
/Users/samue11in/Projects/TungsAcu-DB
```

The similarly named SynologyDrive repository is a historical/reference copy. Do not create or modify application code, CSV data, specs, plans, or work logs there.

Book source Markdown may be read from:

```text
/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/04-書籍資料庫
```

## Required preflight

Before writing project files:

1. Run `pwd` and `git rev-parse --show-toplevel`.
2. Confirm the Git root is exactly `/Users/samue11in/Projects/TungsAcu-DB`.
3. State the absolute output path before generating data or documentation.
4. If the Git root is under `SynologyDrive`, stop and switch to the canonical workspace.

Project-specific specs belong in `docs/specs/` in this repository. System-wide tools and cross-project specs belong under the cloud `99-工具與系統/` area.
