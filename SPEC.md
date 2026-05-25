# SPEC

This document specifies layer 2 and layer 3 of the benchmark architecture.

## Layer 2: Task Packs

### Goal

Task packs define the benchmark corpus in a reproducible format.
Each task must be runnable against any native harness without changing the task itself.

### Source policy

- Main source: the full `Prompt-Vault` corpus.
- Extra required source: one separate assent / anti-sycophancy block derived from the user's Obsidian note about `Bullshit Benchmark`.
- Exclusions are allowed only for:
  - duplicate tasks;
  - broken or unavailable source files;
  - tasks that cannot be normalized into a runnable benchmark unit.

### Directory shape

Each task pack lives in:

`task-packs/<source>/<task-id>/`

Required files:

- `TASK.md` — frozen task statement shown to all harnesses.
- `SOURCE.md` — source provenance and normalization notes.
- `manifest.yaml` — benchmark metadata.
- `starter/` — initial workspace copied before each run.
- `judge/` — optional machine checks, smoke checks, or open instructions for human review.
- `artifacts/` — expected output examples only when needed for visual comparison.

### Manifest fields

Minimum manifest fields:

- `id`
- `title`
- `source_family`
- `source_ref`
- `task_type`
- `review_mode`
- `time_limit_sec`
- `submission_contract`
- `requires_browser`
- `requires_build`
- `machine_checks`
- `human_axes`

### Task types

Initial task types:

- `single_file_ui`
- `small_app`
- `visualizer`
- `interactive_tool`
- `bug_fix`
- `multi_file_feature`
- `assent_check`

### Review modes

- `human_primary` — human visual judgment is the main verdict.
- `human_only` — no meaningful machine check exists.
- `mixed` — smoke checks first, human verdict final.

### Submission contract

Every task must define exactly what the harness must leave behind.

Examples:

- one `index.html`;
- a runnable folder with `README.md`;
- a generated demo artifact;
- a final text answer for assent-check tasks.

### Human review axes

Task packs must declare which axes the reviewer scores.
Allowed initial axes:

- `works`
- `looks_good`
- `feels_finished`
- `spec_following`
- `clarity`
- `taste`
- `restraint`
- `non_agreement`

These axes are intentionally plain-language because the final verdict is user-led.

## Layer 3: Runner

### Goal

The runner executes the same task against different native harnesses while preserving:

- the same task text;
- the same `AGENTS.md`;
- the same start files;
- the same time box;
- the same output contract.

### Runner model

The runner is adapter-based.
Each tested harness gets its own adapter.

Example adapters:

- `codex`
- `claude-code`
- `opencode`
- `gpt-native`

### Adapter responsibilities

Each adapter must know how to:

- start its native harness;
- inject the shared `AGENTS.md`;
- provide the benchmark task text;
- point the harness at the copied workspace;
- capture stdout/stderr or transcript;
- enforce timeout;
- detect runner-side failure vs model-side failure;
- collect produced files for review.

### Shared runner inputs

For every run, the runner receives:

- `model_id`
- `adapter_id`
- `task_pack_id`
- `run_id`
- `workspace_copy`
- `shared_agents_path`
- `time_limit_sec`

### Shared runner outputs

Each run must produce:

- `run.json` — structured metadata;
- `transcript.log` — native harness transcript if available;
- `workspace/` — final produced files;
- `review.md` — blank or prefilled reviewer sheet;
- `screens/` — screenshots for visual tasks when capture is supported.

### Run statuses

Allowed statuses:

- `completed`
- `timeout`
- `adapter_error`
- `environment_error`
- `submission_missing`
- `review_pending`
- `reviewed`

No artificial pass/fail is final until human review is complete on human-primary tasks.

### Shared AGENTS policy

The benchmark stores one canonical `AGENTS.md` at repo root.
Before each run, the runner copies it into the task workspace.
Adapters may not replace or rewrite it.

### Review flow

The runner does not decide the winner.
It prepares comparable artifacts for the human reviewer:

- runnable output;
- screenshots;
- transcript;
- minimal smoke-check result;
- blank score sheet.

### Reporting

The runner may compute convenience summaries, but the final public conclusion is based on:

- per-task human verdicts;
- short reviewer comments;
- a final manual winner choice.

