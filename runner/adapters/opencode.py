"""OpenCode adapter for one-shot benchmark task runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import time
import urllib.request

from runner.adapters.base import AdapterRunContext, AdapterRunResult, HarnessAdapter


OLLAMA_SHOW_URL = "http://localhost:11434/api/show"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"


@dataclass(frozen=True)
class CommandResult:
    """Streaming command execution result."""

    returncode: int
    duration_sec: float
    first_output_sec: float | None
    timed_out: bool


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def measure_raw_generation(model_name: str) -> tuple[float | None, float | None]:
    """Measure approximate TTFT and generation speed via Ollama API."""

    payload = _post_json(
        OLLAMA_GENERATE_URL,
        {
            "model": model_name,
            "prompt": "Write exactly the word OK and nothing else.",
            "stream": False,
        },
    )
    eval_count = payload.get("eval_count")
    eval_duration = payload.get("eval_duration")
    prompt_eval_duration = payload.get("prompt_eval_duration")
    load_duration = payload.get("load_duration")
    first_token_latency_sec = None
    generation_speed_tok_sec = None
    if eval_count and eval_duration:
        generation_speed_tok_sec = float(eval_count) / (float(eval_duration) / 1_000_000_000)
        first_token_latency_sec = (
            (float(load_duration or 0) + float(prompt_eval_duration or 0))
            / 1_000_000_000
        )
        first_token_latency_sec += (float(eval_duration) / float(eval_count)) / 1_000_000_000
    return first_token_latency_sec, generation_speed_tok_sec


def fetch_ollama_metadata(model_name: str) -> dict:
    """Fetch raw metadata for a local Ollama model."""

    return _post_json(OLLAMA_SHOW_URL, {"model": model_name})


def build_task_prompt(ctx: AdapterRunContext) -> str:
    """Build the one-shot prompt passed to OpenCode."""

    common = (
        "Read AGENTS.md and TASK.md in the current directory. "
        "Complete the task exactly as written. "
        "Keep changes inside the current workspace only. "
        "Do not install dependencies or fetch code from the network. "
    )
    if ctx.task_pack.task_type == "assent_check":
        return (
            common
            + "Create the required response file and stop. "
            + "Do not add extra files. "
            + "Do not explain your process outside the requested output file."
        )
    return (
        common
        + "Create the exact submission artifact required by TASK.md. "
        + "Use the read, write, or edit tools correctly. "
        + "A plain text reply is not a valid completion. "
        + "If the task is browser-based, leave it directly runnable from the local file system. "
        + "When finished, stop."
    )


def run_streaming_command(
    command: list[str],
    cwd: Path,
    log_path: Path,
    timeout_sec: int,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run a command with stdout/stderr capture and first-output timing."""

    start = time.monotonic()
    first_output_sec = None
    timed_out = False
    with log_path.open("w", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        selector = selectors.DefaultSelector()
        assert process.stdout is not None
        selector.register(process.stdout, selectors.EVENT_READ)

        while True:
            if time.monotonic() - start > timeout_sec:
                timed_out = True
                process.kill()
                process.wait()
                break

            events = selector.select(timeout=0.2)
            if not events:
                if process.poll() is not None:
                    break
                continue

            for key, _ in events:
                line = key.fileobj.readline()
                if not line:
                    continue
                if first_output_sec is None:
                    first_output_sec = time.monotonic() - start
                log_handle.write(line)
                log_handle.flush()

            if process.poll() is not None:
                break

        selector.close()
        returncode = process.wait()

    return CommandResult(
        returncode=returncode,
        duration_sec=time.monotonic() - start,
        first_output_sec=first_output_sec,
        timed_out=timed_out,
    )


class OpenCodeAdapter(HarnessAdapter):
    """Adapter for benchmark runs through `opencode run`."""

    adapter_id = "opencode"

    def can_profile(self) -> bool:
        """Return True because OpenCode/Ollama can expose a technical profile."""

        return True

    def profile(self, model_id: str) -> dict:
        """Return a measured technical profile payload for an OpenCode local model."""

        _, model_name = model_id.split("/", 1)
        metadata = fetch_ollama_metadata(model_name)
        first_token_latency_sec, generation_speed_tok_sec = measure_raw_generation(model_name)
        details = metadata.get("details") or {}
        model_info = metadata.get("model_info") or {}
        context_window = None
        for key, value in model_info.items():
            if key.endswith(".context_length"):
                context_window = int(value)
                break

        return {
            "model_id": model_id,
            "adapter_id": self.adapter_id,
            "web_search": False,
            "browser_use": False,
            "doc_to_md": False,
            "ocr": False,
            "context_window_claimed": context_window,
            "context_window_observed": None,
            "session_memory": True,
            "cross_session_memory": False,
            "self_improvement": False,
            "thinking_mode": None,
            "thinking_toggle": None,
            "first_token_latency_sec": first_token_latency_sec,
            "generation_speed_tok_sec": generation_speed_tok_sec,
            "tool_calling": True,
            "structured_output": True,
            "repo_editing": True,
            "image_input": False,
            "image_output": False,
            "subagents": False,
            "resume_session": False,
            "permissions_model": "dangerously-skip-permissions",
            "audio_input": False,
            "video_input": False,
            "pdf_native_view": False,
            "local_shell": True,
            "network_access": None,
            "custom_skills_or_plugins": False,
            "citation_support": False,
            "quantization_level": details.get("quantization_level"),
            "parameter_size": details.get("parameter_size"),
            "notes": [
                "Measured with OpenCode in --pure mode against local Ollama.",
                "Web/browser/doc/OCR features are disabled or unavailable in this profile.",
            ],
        }

    def run_task(self, ctx: AdapterRunContext) -> AdapterRunResult:
        """Run one benchmark task pack through OpenCode."""

        transcript_path = ctx.workspace_dir / "transcript.log"
        prompt = build_task_prompt(ctx)
        _, model_name = ctx.model_id.split("/", 1)
        with tempfile.TemporaryDirectory() as config_root, tempfile.TemporaryDirectory() as home_root:
            config_dir = Path(config_root) / "opencode"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_payload = {
                "provider": {
                    "ollama": {
                        "npm": "@ai-sdk/openai-compatible",
                        "name": "Ollama isolated",
                        "options": {"baseURL": "http://localhost:11434/v1"},
                        "models": {
                            model_name: {"name": model_name},
                        },
                    }
                },
                "model": ctx.model_id,
            }
            (config_dir / "opencode.json").write_text(
                json.dumps(config_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = home_root
            env["XDG_CONFIG_HOME"] = config_root
            command = [
                "opencode",
                "run",
                "--pure",
                "--dangerously-skip-permissions",
                "--print-logs",
                "-m",
                ctx.model_id,
                prompt,
            ]
            result = run_streaming_command(
                command=command,
                cwd=ctx.workspace_dir,
                log_path=transcript_path,
                timeout_sec=ctx.time_limit_sec,
                env=env,
            )
        status = "completed"
        notes: list[str] = [
            f"returncode={result.returncode}",
            f"duration_sec={result.duration_sec:.2f}",
        ]
        if result.first_output_sec is not None:
            notes.append(f"first_output_sec={result.first_output_sec:.2f}")
        if result.timed_out:
            status = "timeout"
        elif result.returncode != 0:
            status = "environment_error"

        return AdapterRunResult(
            status=status,
            transcript_path=transcript_path,
            notes=tuple(notes),
        )
