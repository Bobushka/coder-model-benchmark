# Runner

This folder will hold the adapter-based runner.

## Design

The runner is responsible for comparability, not for flattening all harnesses into one fake shell.

Each adapter runs a task through its native harness while preserving the shared benchmark contract.

## Planned subfolders

- `adapters/` — one adapter per harness.
- `prompts/` — shared wrapper prompts and submission instructions.
- `schemas/` — run metadata schemas.

