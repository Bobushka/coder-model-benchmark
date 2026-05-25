# Coder Model Benchmark

Standalone benchmark for evaluating coding models in their native harness.

## Purpose

This repository is the single source of truth for:

- benchmark scope and rules;
- task-pack format;
- native-harness runner contract;
- stored run results and human verdicts.

The benchmark compares the practical coding experience of:

- model + native harness;
- on the same task;
- under the same repo instructions;
- with the same submission contract.

## Core decisions

- Native harness is part of the product being evaluated.
- `AGENTS.md` must be the same across all tested harnesses.
- The main coding corpus comes from `Prompt-Vault`.
- A separate required block tests agreement / sycophancy resistance.
- Final ranking is primarily human and subjective, not formula-first.

## Direct sources

- `Prompt-Vault` corpus: <https://github.com/w512/Prompt-Vault/tree/master>
- `Bullshit Benchmark`: <https://petergpt.github.io/bullshit-benchmark/viewer/index.html>

## Repository layout

- `spec/` — first-layer documents: scope, rules, layout, scoring frame.
- `task-packs/` — normalized benchmark tasks and source policy.
- `runner/` — native-harness adapter contract, prompts, schemas.
- `results/` — raw runs, report snapshots, human score sheets.
- `models/` — tested-model registry and harness mapping.

See:

- `spec/README.md`
- `SPEC.md`
- `spec/TECHNICAL_PROFILE.md`

## Current status

- Layer 2 exists as normalized task packs under `task-packs/`.
- The full current `Prompt-Vault` corpus has been imported.
- The assent block has an initial baseline task.
- Layer 3 exists as a runner skeleton with task-pack discovery and native adapter stubs.

## Useful commands

Import Prompt-Vault:

```bash
python3 tools/import_prompt_vault.py \
  --source-root /path/to/Prompt-Vault \
  --target-root task-packs/prompt-vault
```

List task packs:

```bash
python3 runner/cli.py list-task-packs
```

List adapter ids:

```bash
python3 runner/cli.py list-adapters
```
