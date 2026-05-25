"""Dataclasses for benchmark run artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass
class TechnicalProfile:
    """Capability snapshot for one harness + model pair."""

    model_id: str
    adapter_id: str
    web_search: bool | None = None
    browser_use: bool | None = None
    doc_to_md: bool | None = None
    ocr: bool | None = None
    context_window_claimed: int | None = None
    context_window_observed: int | None = None
    session_memory: bool | None = None
    cross_session_memory: bool | None = None
    self_improvement: bool | None = None
    thinking_mode: bool | None = None
    thinking_toggle: bool | None = None
    first_token_latency_sec: float | None = None
    generation_speed_tok_sec: float | None = None
    tool_calling: bool | None = None
    structured_output: bool | None = None
    repo_editing: bool | None = None
    image_input: bool | None = None
    image_output: bool | None = None
    subagents: bool | None = None
    resume_session: bool | None = None
    permissions_model: str | None = None
    audio_input: bool | None = None
    video_input: bool | None = None
    pdf_native_view: bool | None = None
    local_shell: bool | None = None
    network_access: bool | None = None
    custom_skills_or_plugins: bool | None = None
    citation_support: bool | None = None
    quantization_level: str | None = None
    parameter_size: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class RunArtifact:
    """Structured metadata for one benchmark run."""

    run_id: str
    model_id: str
    adapter_id: str
    task_pack_id: str
    status: str
    workspace_path: str
    transcript_path: str | None = None
    review_path: str | None = None
    screens_dir: str | None = None
    submission_present: bool | None = None
    technical_profile_path: str | None = None
    duration_sec: float | None = None
    first_output_sec: float | None = None
    returncode: int | None = None
    notes: list[str] = field(default_factory=list)


def write_json(path: str | Path, data: dict) -> None:
    """Write JSON with a stable formatting style."""

    path = Path(path)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_technical_profile(path: str | Path, profile: TechnicalProfile) -> None:
    """Write one technical profile JSON artifact."""

    write_json(path, asdict(profile))


def write_run_artifact(path: str | Path, run: RunArtifact) -> None:
    """Write one run artifact JSON file."""

    write_json(path, asdict(run))
