from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.scanner import (
    discover_task_files,
    parse_task_file,
    scan_tasks,
    split_frontmatter,
)
from orchestrator.state import build_board_index, build_board_state


def test_discover_task_files_scans_supported_locations_and_excludes_system_dirs(
    tmp_path: Path,
) -> None:
    kanban_root = tmp_path / ".kanban2code"
    _write_file(kanban_root / "inbox" / "inbox-task.md", "# Inbox\n")
    _write_file(
        kanban_root / "projects" / "orchestration" / "phase1" / "task1.2.md",
        "# Project task\n",
    )
    _write_file(kanban_root / "_archive" / "old.md", "# archived\n")
    _write_file(kanban_root / "_agents" / "agent.md", "# agent\n")
    _write_file(kanban_root / "_providers" / "provider.md", "# provider\n")
    _write_file(kanban_root / "_context" / "ctx.md", "# context\n")
    _write_file(
        kanban_root / "projects" / "orchestration" / "_context" / "nested.md",
        "# nested context\n",
    )

    task_files = discover_task_files(kanban_root)

    assert [path.relative_to(kanban_root).as_posix() for path in task_files] == [
        "inbox/inbox-task.md",
        "projects/orchestration/phase1/task1.2.md",
    ]


def test_parse_task_file_extracts_typed_metadata_and_normalizes_strings(tmp_path: Path) -> None:
    task_path = tmp_path / ".kanban2code" / "projects" / "orchestration" / "phase1" / "task.md"
    _write_file(
        task_path,
        """---
stage: CODE
agent: Coder
bounces: 2
tags: [feature, p1]
contexts:
  - skills/python-core-skills
  - .kanban2code/how-it-works.md
---
# Task

Body text.
""",
    )

    task = parse_task_file(task_path)

    assert task.task_id == "task"
    assert task.project == "orchestration"
    assert task.stage == "code"
    assert task.agent == "coder"
    assert task.bounces == 2
    assert task.tags == ["feature", "p1"]
    assert task.contexts == [
        "skills/python-core-skills",
        ".kanban2code/how-it-works.md",
    ]
    assert task.body.startswith("# Task")


def test_parse_task_file_defaults_optional_fields_when_frontmatter_is_missing(tmp_path: Path) -> None:
    task_path = tmp_path / ".kanban2code" / "inbox" / "todo.md"
    _write_file(task_path, "# Todo\n\nBody.\n")

    task = parse_task_file(task_path)

    assert task.project == "inbox"
    assert task.stage == ""
    assert task.agent == ""
    assert task.bounces == 0
    assert task.tags == []
    assert task.contexts == []
    assert task.metadata == {}


def test_parse_task_file_raises_path_aware_error_for_non_mapping_frontmatter(tmp_path: Path) -> None:
    task_path = tmp_path / ".kanban2code" / "projects" / "orchestration" / "bad.md"
    _write_file(
        task_path,
        """---
- not
- a
- mapping
---
# Invalid
""",
    )

    with pytest.raises(ValueError, match=r"Invalid frontmatter in .*bad\.md"):
        parse_task_file(task_path)


def test_split_frontmatter_returns_metadata_and_body_for_inline_and_block_yaml() -> None:
    metadata, body = split_frontmatter(
        """---
stage: plan
tags:
  - feature
contexts: [one, two]
---
Body
"""
    )

    assert metadata["stage"] == "plan"
    assert metadata["tags"] == ["feature"]
    assert metadata["contexts"] == ["one", "two"]
    assert body == "Body\n"


def test_scan_tasks_and_board_state_preserve_deterministic_order(tmp_path: Path) -> None:
    kanban_root = tmp_path / ".kanban2code"
    _write_file(
        kanban_root / "projects" / "orchestration" / "phase1" / "task1.2.md",
        """---
stage: plan
agent: planner
---
# T1
""",
    )
    _write_file(
        kanban_root / "projects" / "orchestration" / "phase1" / "task1.3.md",
        """---
stage: audit
agent: auditor
---
# T2
""",
    )
    _write_file(
        kanban_root / "projects" / "roadmap" / "roadmap.md",
        """---
stage: completed
agent: auditor
---
# Roadmap
""",
    )

    tasks = scan_tasks(kanban_root)
    board_index = build_board_index(tasks)
    board_state = build_board_state(tasks)

    assert [task.task_id for task in tasks] == ["task1.2", "task1.3", "roadmap"]
    assert [task.task_id for task in board_index["orchestration"]["plan"]] == ["task1.2"]
    assert [task.task_id for task in board_index["orchestration"]["audit"]] == ["task1.3"]
    assert board_state == {
        "orchestration": {
            "plan": ["task1.2"],
            "audit": ["task1.3"],
        },
        "roadmap": {
            "completed": ["roadmap"],
        },
    }


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
