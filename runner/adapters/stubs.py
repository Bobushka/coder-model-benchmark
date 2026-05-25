"""Stub adapters for the first runner layer."""

from __future__ import annotations

from runner.adapters.base import AdapterRunContext, AdapterRunResult, HarnessAdapter


class _StubAdapter(HarnessAdapter):
    """Shared stub implementation until native adapters are wired."""

    adapter_id = "stub"

    def can_profile(self) -> bool:
        """Return True because stubs can still emit empty capability docs."""

        return True

    def profile(self, model_id: str) -> dict:
        """Return a placeholder technical profile payload."""

        return {
            "model_id": model_id,
            "adapter_id": self.adapter_id,
            "notes": ["Adapter not implemented yet."],
        }

    def run_task(self, ctx: AdapterRunContext) -> AdapterRunResult:
        """Return a placeholder result instead of executing a real harness."""

        return AdapterRunResult(
            status="adapter_error",
            notes=("Adapter not implemented yet.", f"adapter={self.adapter_id}"),
        )


class CodexAdapter(_StubAdapter):
    """Stub for Codex native harness."""

    adapter_id = "codex"


class ClaudeCodeAdapter(_StubAdapter):
    """Stub for Claude Code native harness."""

    adapter_id = "claude-code"


class OpenCodeAdapter(_StubAdapter):
    """Stub for OpenCode native harness."""

    adapter_id = "opencode"


class GPTNativeAdapter(_StubAdapter):
    """Stub for a GPT native harness distinct from Codex if needed."""

    adapter_id = "gpt-native"
