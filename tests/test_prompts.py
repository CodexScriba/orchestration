from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.config import load_config
from orchestrator.models import TaskSnapshot
from orchestrator.prompts import PromptAssemblyError, assemble_prompt


def test_assemble_prompt_includes_verbatim_inputs(tmp_path: Path) -> None:
    repo_root = tmp_path
    kanban_root = repo_root / ".kanban2code"
    (kanban_root / "_agents").mkdir(parents=True)
    (kanban_root / "_context" / "skills").mkdir(parents=True)
    (kanban_root / "_agents" / "coder.md").write_text("# Coder Role\n", encoding="utf-8")
    (kanban_root / "_context" / "ai-guide.md").write_text("# AI Guide\n", encoding="utf-8")
    (kanban_root / "_context" / "skills" / "python-core-skills.md").write_text(
        "# Python Skill\n",
        encoding="utf-8",
    )
    task_path = kanban_root / "projects" / "orch" / "task.md"
    task_path.parent.mkdir(parents=True)
    task_path.write_text("---\nstage: code\nagent: coder\n---\n# Task\n", encoding="utf-8")
    config_path = repo_root / "config.json"
    config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

    prompt = assemble_prompt(
        repo_root=repo_root,
        config=load_config(config_path),
        task_snapshot=TaskSnapshot(
            path=task_path,
            task_id="task",
            project="orch",
            stage="code",
            agent="coder",
            contexts=["skills/python-core-skills"],
        ),
        run_id="run-123",
        current_stage="code",
    )

    assert "# Run Metadata" in prompt
    assert "Run ID: run-123" in prompt
    assert "# Coder Role" in prompt
    assert "# AI Guide" in prompt
    assert "# Task" in prompt
    assert "# Python Skill" in prompt
    assert "Expected Transition: code -> audit (auditor)" in prompt


def test_assemble_prompt_raises_for_missing_context(tmp_path: Path) -> None:
    repo_root = tmp_path
    kanban_root = repo_root / ".kanban2code"
    (kanban_root / "_agents").mkdir(parents=True)
    (kanban_root / "_context").mkdir(parents=True)
    (kanban_root / "_agents" / "coder.md").write_text("# Coder Role\n", encoding="utf-8")
    (kanban_root / "_context" / "ai-guide.md").write_text("# AI Guide\n", encoding="utf-8")
    task_path = kanban_root / "projects" / "orch" / "task.md"
    task_path.parent.mkdir(parents=True)
    task_path.write_text("---\nstage: code\nagent: coder\n---\n# Task\n", encoding="utf-8")
    config_path = repo_root / "config.json"
    config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(PromptAssemblyError, match="Missing context file"):
        assemble_prompt(
            repo_root=repo_root,
            config=load_config(config_path),
            task_snapshot=TaskSnapshot(
                path=task_path,
                task_id="task",
                project="orch",
                stage="code",
                agent="coder",
                contexts=["missing-context"],
            ),
            run_id="run-123",
            current_stage="code",
        )
