#!/usr/bin/env python3
"""Run a benchmark wave for local Ollama models via OpenCode."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runner.adapters.base import AdapterRunContext
from runner.adapters.opencode import OpenCodeAdapter, run_streaming_command
from runner.schemas.run_schema import (
    RunArtifact,
    TechnicalProfile,
    write_json,
    write_run_artifact,
    write_technical_profile,
)
from runner.task_pack import TaskPack, discover_task_packs


DEFAULT_TASKS = [
    "prompt-vault.easy-bubble-sort-visualizer",
    "prompt-vault.easy-todo-list",
    "prompt-vault.medium-sorting-visualization",
    "prompt-vault.hard-kanban-board",
    "assent.bullshit-benchmark-baseline",
]
OLLAMA_PS_URL = "http://localhost:11434/api/ps"
OLLAMA_SSH_HOST = "m128-L"


def slugify(value: str) -> str:
    """Make a filesystem-safe slug."""

    slug = value.lower()
    for old, new in [("/", "__"), (":", "_"), (".", "_")]:
        slug = slug.replace(old, new)
    return slug


def fetch_loaded_model_names() -> list[str]:
    """Return currently loaded local Ollama models."""

    request = urllib.request.Request(OLLAMA_PS_URL, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return [model["name"] for model in payload.get("models", [])]


def stop_ollama_models(model_names: list[str]) -> None:
    """Stop a list of remote Ollama models over SSH."""

    if not model_names:
        return
    commands = " ".join(
        f'/opt/homebrew/bin/ollama stop "{name}" >/dev/null 2>&1 || true;'
        for name in model_names
    )
    subprocess.run(
        ["ssh", OLLAMA_SSH_HOST, f"bash -lc '{commands}'"],
        check=True,
        capture_output=True,
        text=True,
    )


def wait_for_no_loaded_models(timeout_sec: int = 120) -> None:
    """Wait until Ollama reports no loaded models."""

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if not fetch_loaded_model_names():
            return
        time.sleep(2)
    raise RuntimeError(f"local models are still loaded: {fetch_loaded_model_names()}")


def load_task_map() -> dict[str, TaskPack]:
    """Load available task packs indexed by id."""

    task_packs = discover_task_packs(REPO_ROOT / "task-packs")
    return {pack.task_id: pack for pack in task_packs}


def copy_starter_tree(src: Path, dst: Path) -> None:
    """Copy starter contents into a new workspace."""

    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        target = dst / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)


def prepare_workspace(task_pack: TaskPack, workspace_dir: Path) -> None:
    """Create a runnable workspace for one task."""

    workspace_dir.mkdir(parents=True, exist_ok=True)
    copy_starter_tree(task_pack.pack_dir / "starter", workspace_dir)
    shutil.copy2(REPO_ROOT / "AGENTS.md", workspace_dir / "AGENTS.md")
    shutil.copy2(task_pack.pack_dir / "TASK.md", workspace_dir / "TASK.md")
    shutil.copy2(task_pack.pack_dir / "SOURCE.md", workspace_dir / "SOURCE.md")


def build_review_sheet(task_pack: TaskPack, path: Path) -> None:
    """Create a blank human review sheet."""

    axes = "\n".join(f"- {axis}: " for axis in task_pack.human_axes)
    text = (
        f"# Review: {task_pack.task_id}\n\n"
        f"Title: {task_pack.title}\n"
        f"Type: {task_pack.task_type}\n"
        f"Difficulty: {task_pack.difficulty or 'unknown'}\n"
        f"Review mode: {task_pack.review_mode}\n\n"
        "## Axes\n"
        f"{axes}\n\n"
        "## Overall verdict\n\n"
        "- winner feel: \n"
        "- notes: \n"
    )
    path.write_text(text, encoding="utf-8")


def submission_present(task_pack: TaskPack, workspace_dir: Path) -> bool:
    """Check whether required submission files exist."""

    return all((workspace_dir / rel_path).exists() for rel_path in task_pack.submission.paths)


def parse_adapter_notes(notes: tuple[str, ...]) -> tuple[float | None, float | None, int | None]:
    """Pull numeric values out of adapter note strings."""

    duration_sec = None
    first_output_sec = None
    returncode = None
    for note in notes:
        if note.startswith("duration_sec="):
            duration_sec = float(note.split("=", 1)[1])
        elif note.startswith("first_output_sec="):
            first_output_sec = float(note.split("=", 1)[1])
        elif note.startswith("returncode="):
            returncode = int(note.split("=", 1)[1])
    return duration_sec, first_output_sec, returncode


def write_technical_profile_markdown(profile: TechnicalProfile, path: Path) -> None:
    """Render a human-readable technical profile."""

    def fmt_bool(value: bool | None) -> str:
        if value is True:
            return "yes"
        if value is False:
            return "no"
        return "unknown"

    text = "\n".join(
        [
            f"# Technical Profile: {profile.model_id}",
            "",
            f"- adapter: `{profile.adapter_id}`",
            f"- parameter size: `{profile.parameter_size or 'unknown'}`",
            f"- quantization: `{profile.quantization_level or 'unknown'}`",
            f"- claimed context: `{profile.context_window_claimed or 'unknown'}`",
            f"- first token latency: `{profile.first_token_latency_sec or 'unknown'}`",
            f"- generation speed tok/sec: `{profile.generation_speed_tok_sec or 'unknown'}`",
            f"- web search: `{fmt_bool(profile.web_search)}`",
            f"- browser use: `{fmt_bool(profile.browser_use)}`",
            f"- doc/pdf to md: `{fmt_bool(profile.doc_to_md)}`",
            f"- OCR: `{fmt_bool(profile.ocr)}`",
            f"- repo editing: `{fmt_bool(profile.repo_editing)}`",
            f"- local shell: `{fmt_bool(profile.local_shell)}`",
            f"- cross-session memory: `{fmt_bool(profile.cross_session_memory)}`",
            f"- thinking mode: `{fmt_bool(profile.thinking_mode)}`",
            f"- structured output: `{fmt_bool(profile.structured_output)}`",
            f"- image input: `{fmt_bool(profile.image_input)}`",
            f"- image output: `{fmt_bool(profile.image_output)}`",
            f"- subagents: `{fmt_bool(profile.subagents)}`",
            f"- resume session: `{fmt_bool(profile.resume_session)}`",
            f"- permissions model: `{profile.permissions_model or 'unknown'}`",
            "",
            "## Notes",
            "",
            *[f"- {note}" for note in profile.notes],
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def render_report(run_root: Path, models: list[str], task_packs: list[TaskPack]) -> None:
    """Render the markdown report for the whole wave."""

    lines = [
        "# OpenCode Light Wave Report",
        "",
        f"- run root: `{run_root}`",
        "- harness: `opencode run --pure --dangerously-skip-permissions`",
        "- suite: `light-wave`",
        "",
        "## Scope",
        "",
        "- Models were compared through the same OpenCode invocation pattern.",
        "- This wave uses the light visual subset plus the assent check, not the full corpus.",
        "- Human review is still required for final winner choice on visual tasks.",
        "",
        "## Technical Profile",
        "",
    ]

    for model_id in models:
        model_dir = run_root / slugify(model_id)
        profile = json.loads((model_dir / "tech-profile.json").read_text(encoding="utf-8"))
        probe = json.loads((model_dir / "probe.json").read_text(encoding="utf-8"))
        lines.extend(
            [
                f"### {model_id}",
                "",
                f"- parameter size: `{profile.get('parameter_size') or 'unknown'}`",
                f"- quantization: `{profile.get('quantization_level') or 'unknown'}`",
                f"- claimed context: `{profile.get('context_window_claimed') or 'unknown'}`",
                f"- first token latency: `{profile.get('first_token_latency_sec') or 'unknown'}`",
                f"- generation speed tok/sec: `{profile.get('generation_speed_tok_sec') or 'unknown'}`",
                f"- preflight probe: `{probe.get('status')}`",
                f"- preflight duration sec: `{probe.get('duration_sec')}`",
                f"- web search: `{profile.get('web_search')}`",
                f"- browser use: `{profile.get('browser_use')}`",
                f"- doc/pdf to md: `{profile.get('doc_to_md')}`",
                f"- OCR: `{profile.get('ocr')}`",
                f"- local shell: `{profile.get('local_shell')}`",
                f"- repo editing: `{profile.get('repo_editing')}`",
                "",
            ]
        )

    lines.extend(["## Task Results", ""])
    for task_pack in task_packs:
        lines.extend([f"### {task_pack.task_id}", "", f"- title: `{task_pack.title}`", f"- type: `{task_pack.task_type}`", ""])
        for model_id in models:
            model_dir = run_root / slugify(model_id)
            task_dir = model_dir / slugify(task_pack.task_id)
            artifact = json.loads((task_dir / "run.json").read_text(encoding="utf-8"))
            lines.extend(
                [
                    f"- {model_id}: status=`{artifact['status']}`, submission_present=`{artifact['submission_present']}`, duration_sec=`{artifact.get('duration_sec')}`",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## Next Human Step",
            "",
            "- Open each task workspace and judge the result visually.",
            "- Fill in each `review.md` sheet.",
            "- Choose the winner manually after human review, not from automation alone.",
            "",
        ]
    )
    report_path = run_root / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_probe_smoke(model_id: str, out_dir: Path) -> dict:
    """Run a tiny OpenCode smoke prompt so the report has a harness-level proof of life."""

    workspace_dir = out_dir / "probe"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / "AGENTS.md").write_text("Create probe.txt with the text OK.\n", encoding="utf-8")
    (workspace_dir / "TASK.md").write_text("Create `probe.txt` containing exactly `OK`.\n", encoding="utf-8")
    _, model_name = model_id.split("/", 1)
    with tempfile.TemporaryDirectory() as config_root, tempfile.TemporaryDirectory() as home_root:
        config_dir = Path(config_root) / "opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_payload = {
            "provider": {
                "ollama": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "Ollama isolated",
                    "options": {"baseURL": "http://localhost:11434/v1"},
                    "models": {model_name: {"name": model_name}},
                }
            },
            "model": model_id,
        }
        (config_dir / "opencode.json").write_text(
            json.dumps(config_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["HOME"] = home_root
        env["XDG_CONFIG_HOME"] = config_root
        result = run_streaming_command(
            command=[
                "opencode",
                "run",
                "--pure",
                "--dangerously-skip-permissions",
                "--print-logs",
                "-m",
                model_id,
                (
                    "Read AGENTS.md and TASK.md in the current directory. "
                    "You must create probe.txt containing exactly OK using the write or edit tool. "
                    "A text reply alone is invalid. Stop after the file exists."
                ),
            ],
            cwd=workspace_dir,
            log_path=workspace_dir / "probe-transcript.log",
            timeout_sec=60,
            env=env,
        )
    probe_payload = {
        "status": "ok" if (workspace_dir / "probe.txt").exists() and result.returncode == 0 else "failed",
        "probe_file_present": (workspace_dir / "probe.txt").exists(),
        "returncode": result.returncode,
        "duration_sec": result.duration_sec,
        "first_output_sec": result.first_output_sec,
        "timed_out": result.timed_out,
    }
    write_json(out_dir / "probe.json", probe_payload)
    return probe_payload


def run_wave(models: list[str], task_ids: list[str], label: str, max_time_sec: int | None) -> Path:
    """Run the full benchmark wave."""

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{label}"
    run_root = REPO_ROOT / "results" / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    task_map = load_task_map()
    task_packs = [task_map[task_id] for task_id in task_ids]
    adapter = OpenCodeAdapter()

    for model_id in models:
        stop_ollama_models(fetch_loaded_model_names())
        wait_for_no_loaded_models()
        model_dir = run_root / slugify(model_id)
        model_dir.mkdir(parents=True, exist_ok=True)
        profile_payload = adapter.profile(model_id)
        profile = TechnicalProfile(**profile_payload)
        write_technical_profile(model_dir / "tech-profile.json", profile)
        write_technical_profile_markdown(profile, model_dir / "tech-profile.md")
        probe_payload = run_probe_smoke(model_id, model_dir)
        if probe_payload["status"] != "ok":
            for task_pack in task_packs:
                task_dir = model_dir / slugify(task_pack.task_id)
                task_dir.mkdir(parents=True, exist_ok=True)
                artifact = RunArtifact(
                    run_id=run_id,
                    model_id=model_id,
                    adapter_id=adapter.adapter_id,
                    task_pack_id=task_pack.task_id,
                    status="environment_error",
                    workspace_path=str(task_dir / "workspace"),
                    technical_profile_path=str(model_dir / "tech-profile.json"),
                    duration_sec=probe_payload["duration_sec"],
                    first_output_sec=probe_payload["first_output_sec"],
                    returncode=probe_payload["returncode"],
                    notes=[
                        "Skipped because OpenCode preflight probe failed.",
                        f"probe_timed_out={probe_payload['timed_out']}",
                    ],
                )
                write_run_artifact(task_dir / "run.json", artifact)
            continue

        for task_pack in task_packs:
            task_dir = model_dir / slugify(task_pack.task_id)
            workspace_dir = task_dir / "workspace"
            prepare_workspace(task_pack, workspace_dir)
            review_path = task_dir / "review.md"
            build_review_sheet(task_pack, review_path)

            ctx = AdapterRunContext(
                run_id=run_id,
                model_id=model_id,
                workspace_dir=workspace_dir,
                task_pack=task_pack,
                shared_agents_path=REPO_ROOT / "AGENTS.md",
                time_limit_sec=min(task_pack.time_limit_sec, max_time_sec) if max_time_sec else task_pack.time_limit_sec,
            )
            result = adapter.run_task(ctx)
            present = submission_present(task_pack, workspace_dir)
            status = result.status
            if status == "completed":
                status = "review_pending" if present else "submission_missing"
            duration_sec, first_output_sec, returncode = parse_adapter_notes(result.notes)
            artifact = RunArtifact(
                run_id=run_id,
                model_id=model_id,
                adapter_id=adapter.adapter_id,
                task_pack_id=task_pack.task_id,
                status=status,
                workspace_path=str(workspace_dir),
                transcript_path=str(result.transcript_path) if result.transcript_path else None,
                review_path=str(review_path),
                submission_present=present,
                technical_profile_path=str(model_dir / "tech-profile.json"),
                duration_sec=duration_sec,
                first_output_sec=first_output_sec,
                returncode=returncode,
                notes=list(result.notes),
            )
            write_run_artifact(task_dir / "run.json", artifact)

    stop_ollama_models(fetch_loaded_model_names())
    wait_for_no_loaded_models()
    render_report(run_root, models, task_packs)
    return run_root


def build_parser() -> argparse.ArgumentParser:
    """Build CLI arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        required=True,
        help="Model id in provider/name form, for example ollama/qwen2.5-coder:7b-instruct-q4_K_M",
    )
    parser.add_argument(
        "--task",
        action="append",
        dest="tasks",
        default=[],
        help="Task pack id. If omitted, the default light-wave suite is used.",
    )
    parser.add_argument(
        "--label",
        default="opencode-light-wave",
        help="Run label appended to the timestamped run id.",
    )
    parser.add_argument(
        "--max-time-sec",
        type=int,
        default=900,
        help="Optional per-task timeout clamp.",
    )
    return parser


def main() -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args()
    task_ids = args.tasks or DEFAULT_TASKS
    run_root = run_wave(args.models, task_ids, args.label, args.max_time_sec)
    print(run_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
