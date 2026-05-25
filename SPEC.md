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

- `single_file_ui` — one self-contained page or document, usually one output file, easy to judge visually.
- `small_app` — a small but complete app with a few connected features and a runnable result.
- `visualizer` — a task where the main value is visual explanation of logic, algorithm, or state changes.
- `interactive_tool` — a user-facing tool with controls, inputs, outputs, and basic interaction flow.
- `bug_fix` — a constrained repair task inside an existing codebase or scaffold.
- `multi_file_feature` — a feature that requires navigation, coordination, and changes across several files.
- `assent_check` — a non-coding test that checks whether the system resists nonsense instead of agreeing.

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

## Pre-Benchmark Technical Profile

Before content tasks begin, every `harness + model` pair must go through a technical capability check.
This is not the main benchmark, but a compatibility and context section that explains what the system can even do.

### Goal

Record the hard limits and built-in strengths of the tested stack before judging task outcomes.
This prevents misleading comparisons where one system fails because the harness lacks a capability, not because the model is weak.

### Required capability fields

- `web_search` — can it search the public web from inside the harness?
- `browser_use` — can it open and interact with pages, not just fetch text?
- `doc_to_md` — can it convert docs, slides, or PDFs into markdown or text?
- `ocr` — can it read raster images or scanned PDFs?
- `context_window_claimed` — vendor or harness claimed context size.
- `context_window_observed` — practical observed working size, if measured.
- `session_memory` — does it retain memory inside one session?
- `cross_session_memory` — does it remember anything across sessions?
- `self_improvement` — can it update prompts, memory, or tools for later runs?
- `thinking_mode` — does it have an explicit reasoning mode?
- `thinking_toggle` — can that mode be disabled or controlled?
- `first_token_latency_sec`
- `generation_speed_tok_sec`
- `tool_calling` — can it use tools at all?
- `structured_output` — can it reliably produce machine-readable output?
- `repo_editing` — can it read, patch, and create files safely?
- `image_input` — can it inspect screenshots or mockups?
- `image_output` — can it generate visual assets when the task needs them?
- `subagents` — does the harness support delegation or parallel agents?
- `resume_session` — can work continue from an earlier interrupted session?
- `permissions_model` — how tool permissions are granted or blocked.

### Suggested additional fields

- `audio_input`
- `video_input`
- `pdf_native_view`
- `local_shell`
- `network_access`
- `custom_skills_or_plugins`
- `citation_support`

### Output

The technical check must produce one normalized artifact per tested stack:

- `tech-profile.json`
- `tech-profile.md`

These artifacts must be stored with the run and summarized in the final report before task results.

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
- `tech-profile.json` — technical capability snapshot for the tested stack;
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

- technical profile summary per stack;
- per-task human verdicts;
- short reviewer comments;
- a final manual winner choice.
