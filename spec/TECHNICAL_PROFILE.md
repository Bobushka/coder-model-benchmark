# Technical Profile

Every tested `harness + model` pair must be described before task results are judged.

## Why this exists

Two systems may differ not because one "codes worse", but because one has:

- web search and the other does not;
- OCR and the other does not;
- browser control and the other does not;
- cross-session memory and the other does not.

This benchmark treats those differences as part of the product reality.

## Required checks

- public web search
- browser interaction
- doc or PDF to markdown
- OCR on scans and images
- claimed context window
- observed practical context window
- memory inside one session
- memory across sessions
- self-improvement or self-updating mechanisms
- first-token latency
- generation speed
- tool use support
- structured output support
- repo editing support
- image input
- image output
- subagent support
- session resume
- permissions model
- explicit thinking mode
- thinking mode on/off control

## Reporting rule

The final report must begin with a technical profile section for every tested stack.
Task winners should be read in light of those capabilities, not in isolation.
