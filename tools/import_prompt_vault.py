#!/usr/bin/env python3
"""Import the full Prompt-Vault corpus into normalized task packs."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


SOURCE_REPO = "https://github.com/w512/Prompt-Vault"


@dataclass(frozen=True)
class TaskMeta:
    """Static import metadata for a Prompt-Vault task."""

    slug: str
    task_type: str
    review_mode: str
    time_limit_sec: int
    submission_kind: str
    submission_paths: list[str]
    human_axes: list[str]


TASK_META = {
    "Easy/Bubble_Sort_Visualizer.md": TaskMeta(
        slug="easy-bubble-sort-visualizer",
        task_type="visualizer",
        review_mode="human_primary",
        time_limit_sec=1200,
        submission_kind="single_file",
        submission_paths=["index.html"],
        human_axes=["works", "looks_good", "spec_following", "clarity"],
    ),
    "Easy/ToDo_List.md": TaskMeta(
        slug="easy-todo-list",
        task_type="small_app",
        review_mode="human_primary",
        time_limit_sec=1200,
        submission_kind="single_file",
        submission_paths=["index.html"],
        human_axes=["works", "feels_finished", "spec_following", "restraint"],
    ),
    "Medium/Sorting_Visualization.md": TaskMeta(
        slug="medium-sorting-visualization",
        task_type="visualizer",
        review_mode="human_primary",
        time_limit_sec=1800,
        submission_kind="single_file",
        submission_paths=["index.html"],
        human_axes=["works", "looks_good", "feels_finished", "taste"],
    ),
    "Hard/Kanban_Board.md": TaskMeta(
        slug="hard-kanban-board",
        task_type="interactive_tool",
        review_mode="human_primary",
        time_limit_sec=2700,
        submission_kind="single_file",
        submission_paths=["index.html"],
        human_axes=["works", "feels_finished", "taste", "spec_following"],
    ),
    "Hard/Markdown_Editor_Desktop.md": TaskMeta(
        slug="hard-markdown-editor-desktop",
        task_type="multi_file_feature",
        review_mode="mixed",
        time_limit_sec=3600,
        submission_kind="project_dir",
        submission_paths=["."],
        human_axes=["works", "feels_finished", "clarity", "spec_following"],
    ),
    "Advanced/LLM_Speedometer.md": TaskMeta(
        slug="advanced-llm-speedometer",
        task_type="multi_file_feature",
        review_mode="mixed",
        time_limit_sec=3600,
        submission_kind="project_dir",
        submission_paths=["."],
        human_axes=["works", "clarity", "spec_following", "taste"],
    ),
}


def build_manifest(relative_path: str, title: str, meta: TaskMeta) -> dict:
    """Return a JSON-compatible manifest object."""

    requires_browser = meta.submission_kind == "single_file"
    requires_build = meta.submission_kind == "project_dir"
    return {
        "id": f"prompt-vault.{meta.slug}",
        "title": title,
        "source_family": "prompt-vault",
        "source_ref": relative_path,
        "task_type": meta.task_type,
        "difficulty": relative_path.split("/", 1)[0].lower(),
        "review_mode": meta.review_mode,
        "time_limit_sec": meta.time_limit_sec,
        "submission_contract": {
            "kind": meta.submission_kind,
            "paths": meta.submission_paths,
            "notes": "Leave the required artifact in the workspace root unless the task says otherwise.",
        },
        "requires_browser": requires_browser,
        "requires_build": requires_build,
        "machine_checks": [],
        "human_axes": meta.human_axes,
    }


def make_task_md(title: str, source_text: str) -> str:
    """Return the normalized benchmark task statement."""

    return (
        f"# {title}\n\n"
        "Use this task exactly as written. Follow the shared root `AGENTS.md` in addition to the task below.\n\n"
        "## Source Prompt\n\n"
        f"{source_text.strip()}\n"
    )


def make_source_md(relative_path: str, title: str, source_text: str) -> str:
    """Return provenance details for one imported task."""

    return (
        f"# Source\n\n"
        f"- Source corpus: Prompt-Vault\n"
        f"- Source repo: {SOURCE_REPO}\n"
        f"- Source path: `{relative_path}`\n"
        f"- Source page: {SOURCE_REPO}/blob/master/{relative_path}\n"
        f"- Imported title: {title}\n\n"
        "## Raw Prompt Snapshot\n\n"
        f"{source_text.strip()}\n"
    )


def make_starter_readme(manifest: dict) -> str:
    """Describe the initial workspace for a task."""

    contract = manifest["submission_contract"]
    return (
        "# Starter Workspace\n\n"
        "This starter workspace is intentionally empty.\n\n"
        "Create the deliverable required by the task pack in place.\n\n"
        f"- Submission kind: `{contract['kind']}`\n"
        f"- Expected paths: {', '.join(contract['paths'])}\n"
    )


def make_judge_readme(manifest: dict) -> str:
    """Describe how a human should review a task."""

    axes = ", ".join(manifest["human_axes"])
    return (
        "# Judge Notes\n\n"
        "Human review is primary for this task.\n\n"
        f"- Review mode: `{manifest['review_mode']}`\n"
        f"- Human axes: {axes}\n"
        "- Verify the required artifact exists.\n"
        "- Open the result and judge it on usefulness and finish quality.\n"
        "- Record short notes in the run review sheet.\n"
    )


def derive_title(source_path: Path, text: str) -> str:
    """Choose a stable human title for one source file."""

    first_line = text.splitlines()[0].strip()
    if first_line.startswith("#"):
        return first_line.lstrip("#").strip().strip("*")
    return source_path.stem.replace("_", " ")


def import_corpus(source_root: Path, target_root: Path) -> list[dict]:
    """Import all known Prompt-Vault markdown tasks."""

    imported: list[dict] = []
    for relative_path, meta in TASK_META.items():
        source_path = source_root / relative_path
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source task: {source_path}")

        text = source_path.read_text(encoding="utf-8").strip()
        title = derive_title(source_path, text)
        manifest = build_manifest(relative_path, title, meta)
        pack_dir = target_root / meta.slug

        if pack_dir.exists():
            shutil.rmtree(pack_dir)

        (pack_dir / "starter").mkdir(parents=True, exist_ok=True)
        (pack_dir / "judge").mkdir(parents=True, exist_ok=True)
        (pack_dir / "artifacts").mkdir(parents=True, exist_ok=True)

        (pack_dir / "TASK.md").write_text(make_task_md(title, text), encoding="utf-8")
        (pack_dir / "SOURCE.md").write_text(
            make_source_md(relative_path, title, text),
            encoding="utf-8",
        )
        (pack_dir / "manifest.yaml").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        (pack_dir / "starter" / "README.md").write_text(
            make_starter_readme(manifest),
            encoding="utf-8",
        )
        (pack_dir / "judge" / "README.md").write_text(
            make_judge_readme(manifest),
            encoding="utf-8",
        )

        imported.append(
            {
                "id": manifest["id"],
                "title": title,
                "source_ref": relative_path,
                "task_type": manifest["task_type"],
                "review_mode": manifest["review_mode"],
            }
        )

    return imported


def write_corpus_index(target_root: Path, imported: list[dict]) -> None:
    """Write corpus summary files."""

    rows = ["# Prompt-Vault Corpus\n", f"Imported tasks: {len(imported)}\n"]
    for item in imported:
        rows.append(
            f"- `{item['id']}` — {item['title']} "
            f"({item['task_type']}, {item['review_mode']}, source `{item['source_ref']}`)"
        )
    (target_root / "CORPUS.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (target_root / "corpus_index.json").write_text(
        json.dumps(imported, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Parse args and import Prompt-Vault."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--target-root", required=True)
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    target_root = Path(args.target_root).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    imported = import_corpus(source_root, target_root)
    write_corpus_index(target_root, imported)
    print(f"Imported {len(imported)} task packs into {target_root}")


if __name__ == "__main__":
    main()
