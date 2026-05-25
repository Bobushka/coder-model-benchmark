"""Adapter registry helpers."""

from __future__ import annotations

from runner.adapters.base import HarnessAdapter
from runner.adapters.opencode import OpenCodeAdapter
from runner.adapters.stubs import (
    ClaudeCodeAdapter,
    CodexAdapter,
    GPTNativeAdapter,
)


def build_registry() -> dict[str, HarnessAdapter]:
    """Return the adapter registry for the first runner layer."""

    adapters = [
        CodexAdapter(),
        ClaudeCodeAdapter(),
        OpenCodeAdapter(),
        GPTNativeAdapter(),
    ]
    return {adapter.adapter_id: adapter for adapter in adapters}
