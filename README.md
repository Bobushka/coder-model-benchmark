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

## Repository layout

- `spec/` — first-layer documents: scope, rules, layout, scoring frame.
- `task-packs/` — normalized benchmark tasks and source policy.
- `runner/` — native-harness adapter contract, prompts, schemas.
- `results/` — raw runs, report snapshots, human score sheets.
- `models/` — tested-model registry and harness mapping.

See:

- `spec/README.md`
- `SPEC.md`

