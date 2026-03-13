"""Task discovery and frontmatter parsing helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import re

import yaml

from orchestrator.models import TaskSnapshot

EXCLUDED_DIR_NAMES = {"_archive", "_agents", "_providers", "_context"}
FRONTMATTER_PATTERN = re.compile(
    r"\A---\s*\r?\n(?P<metadata>.*?)(?:\r?\n)---\s*(?:\r?\n(?P<body>.*)|\Z)",
    re.DOTALL,
)


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Split a markdown document into frontmatter metadata and body.

    Args:
        text: Full markdown document contents.

    Returns:
        A tuple of parsed metadata and the remaining markdown body.

    Raises:
        ValueError: If the frontmatter block is malformed or not a YAML mapping.
    """

    if not text.startswith("---"):
        return {}, text

    match = FRONTMATTER_PATTERN.match(text)
    if match is None:
        raise ValueError("Unterminated YAML frontmatter block.")

    try:
        parsed_metadata = yaml.safe_load(match.group("metadata")) or {}
    except yaml.YAMLError as exc:
        raise ValueError("Invalid YAML frontmatter.") from exc

    if not isinstance(parsed_metadata, Mapping):
        raise ValueError("Frontmatter must be a YAML mapping.")

    body = match.group("body") or ""
    return dict(parsed_metadata), body


def parse_task_file(path: Path) -> TaskSnapshot:
    """Parse a task markdown file into a typed snapshot.

    Args:
        path: Path to the markdown task file.

    Returns:
        Parsed task snapshot.

    Raises:
        ValueError: If the file contains invalid frontmatter or metadata types.
    """

    text = path.read_text(encoding="utf-8")
    try:
        metadata, body = split_frontmatter(text)
    except ValueError as exc:
        raise ValueError(f"Invalid frontmatter in {path}: {exc}") from exc

    stage = _optional_str(metadata, "stage", path).strip().lower()
    agent = _optional_str(metadata, "agent", path).strip().lower()

    return TaskSnapshot(
        path=path,
        task_id=path.stem,
        project=_derive_project_name(path),
        stage=stage,
        agent=agent,
        bounces=_optional_int(metadata, "bounces", path),
        tags=_optional_string_list(metadata, "tags", path),
        contexts=_optional_string_list(metadata, "contexts", path),
        metadata=metadata,
        body=body,
        text=text,
    )


def discover_task_files(kanban_root: Path) -> list[Path]:
    """Discover task markdown files under the supported Kanban2Code roots.

    Args:
        kanban_root: Path to the `.kanban2code` root.

    Returns:
        Sorted list of markdown task file paths.
    """

    task_files: list[Path] = []
    for relative_root in ("inbox", "projects"):
        search_root = kanban_root / relative_root
        if not search_root.exists():
            continue
        for path in search_root.rglob("*.md"):
            if _is_excluded(path, kanban_root):
                continue
            task_files.append(path)

    return sorted(task_files, key=lambda item: item.relative_to(kanban_root).as_posix())


def scan_tasks(kanban_root: Path) -> list[TaskSnapshot]:
    """Scan the Kanban2Code workspace into task snapshots.

    Args:
        kanban_root: Path to the `.kanban2code` root.

    Returns:
        Sorted task snapshots.
    """

    return [parse_task_file(path) for path in discover_task_files(kanban_root)]


def index_tasks_by_project_and_stage(
    tasks: Sequence[TaskSnapshot],
) -> dict[str, dict[str, list[TaskSnapshot]]]:
    """Index tasks by project and stage while preserving input order.

    Args:
        tasks: Ordered task snapshots.

    Returns:
        Nested mapping of project to stage to task snapshots.
    """

    index: dict[str, dict[str, list[TaskSnapshot]]] = {}
    for task in tasks:
        project_bucket = index.setdefault(task.project, {})
        stage_bucket = project_bucket.setdefault(task.stage, [])
        stage_bucket.append(task)
    return index


def _derive_project_name(path: Path) -> str:
    parts = path.parts
    try:
        kanban_index = parts.index(".kanban2code")
    except ValueError as exc:
        raise ValueError(f"Task path is not inside .kanban2code: {path}") from exc

    relative_parts = parts[kanban_index + 1 :]
    if not relative_parts:
        raise ValueError(f"Cannot derive project name from task path: {path}")
    if relative_parts[0] == "inbox":
        return "inbox"
    if relative_parts[0] == "projects" and len(relative_parts) >= 2:
        return relative_parts[1]
    raise ValueError(f"Cannot derive project name from task path: {path}")


def _is_excluded(path: Path, kanban_root: Path) -> bool:
    relative_parts = path.relative_to(kanban_root).parts
    return any(part in EXCLUDED_DIR_NAMES for part in relative_parts)


def _optional_str(metadata: Mapping[str, object], key: str, path: Path) -> str:
    value = metadata.get(key, "")
    if value == "":
        return ""
    if not isinstance(value, str):
        raise ValueError(f"Invalid {key!r} value in {path}: expected str")
    return value


def _optional_int(metadata: Mapping[str, object], key: str, path: Path) -> int:
    value = metadata.get(key, 0)
    if value in ("", None):
        return 0
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid {key!r} value in {path}: expected int")
    return value


def _optional_string_list(metadata: Mapping[str, object], key: str, path: Path) -> list[str]:
    value = metadata.get(key, [])
    if value in ("", None):
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Invalid {key!r} value in {path}: expected list[str]")
    return list(value)
