"""Base adapter contract for native harness integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from runner.task_pack import TaskPack


@dataclass(frozen=True)
class AdapterRunContext:
    """Inputs shared by all harness adapters."""

    run_id: str
    model_id: str
    workspace_dir: Path
    task_pack: TaskPack
    shared_agents_path: Path
    time_limit_sec: int


@dataclass(frozen=True)
class AdapterRunResult:
    """Raw result returned by one adapter invocation."""

    status: str
    transcript_path: Path | None = None
    notes: tuple[str, ...] = ()


class HarnessAdapter(ABC):
    """Abstract adapter for one native harness."""

    adapter_id: str

    @abstractmethod
    def can_profile(self) -> bool:
        """Return whether this adapter can produce a technical profile."""

    @abstractmethod
    def profile(self, model_id: str) -> dict:
        """Return a technical capability snapshot for a model."""

    @abstractmethod
    def run_task(self, ctx: AdapterRunContext) -> AdapterRunResult:
        """Run one task pack in the native harness."""
