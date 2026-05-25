"""Task-pack loading helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SubmissionContract:
    """Normalized submission contract for a task pack."""

    kind: str
    paths: list[str]
    notes: str


@dataclass(frozen=True)
class TaskPack:
    """Loaded task-pack metadata."""

    pack_dir: Path
    task_id: str
    title: str
    source_family: str
    source_ref: str
    task_type: str
    review_mode: str
    time_limit_sec: int
    submission: SubmissionContract
    requires_browser: bool
    requires_build: bool
    machine_checks: list[str]
    human_axes: list[str]


def load_manifest(pack_dir: Path) -> dict:
    """Load a manifest written as JSON-compatible YAML."""

    manifest_path = pack_dir / "manifest.yaml"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_task_pack(pack_dir: str | Path) -> TaskPack:
    """Load one task pack from disk."""

    pack_dir = Path(pack_dir).resolve()
    data = load_manifest(pack_dir)
    submission = SubmissionContract(**data["submission_contract"])
    return TaskPack(
        pack_dir=pack_dir,
        task_id=data["id"],
        title=data["title"],
        source_family=data["source_family"],
        source_ref=data["source_ref"],
        task_type=data["task_type"],
        review_mode=data["review_mode"],
        time_limit_sec=int(data["time_limit_sec"]),
        submission=submission,
        requires_browser=bool(data["requires_browser"]),
        requires_build=bool(data["requires_build"]),
        machine_checks=list(data["machine_checks"]),
        human_axes=list(data["human_axes"]),
    )


def discover_task_packs(root: str | Path) -> list[TaskPack]:
    """Discover task packs below a root directory."""

    root = Path(root).resolve()
    task_packs: list[TaskPack] = []
    for manifest_path in sorted(root.rglob("manifest.yaml")):
        task_packs.append(load_task_pack(manifest_path.parent))
    return task_packs
