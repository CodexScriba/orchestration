"""Prompt assembly helpers for provider stage execution."""

from __future__ import annotations

from pathlib import Path

from orchestrator.config import OrchestratorConfig
from orchestrator.models import TaskSnapshot


class PromptAssemblyError(RuntimeError):
    """Raised when prompt assembly cannot resolve required inputs."""


def assemble_prompt(
    *,
    repo_root: Path,
    config: OrchestratorConfig,
    task_snapshot: TaskSnapshot,
    run_id: str,
    current_stage: str,
    role_path: Path | None = None,
    ai_guide_path: Path | None = None,
) -> str:
    """Assemble a full stage prompt with verbatim file contents."""

    repo_root = Path(repo_root)
    kanban_root = repo_root / ".kanban2code"
    resolved_role_path = role_path or kanban_root / "_agents" / f"{task_snapshot.agent}.md"
    resolved_ai_guide_path = ai_guide_path or kanban_root / "_context" / "ai-guide.md"
    expected_transition = _expected_transition_text(config, current_stage)

    role_content = _read_required_file(resolved_role_path, "role file")
    ai_guide_content = _read_required_file(resolved_ai_guide_path, "ai-guide")
    task_content = _read_required_file(task_snapshot.path, "task file")

    context_blocks: list[str] = []
    for context_name in task_snapshot.contexts:
        context_path = resolve_context_path(kanban_root, context_name)
        context_content = _read_required_file(context_path, f"context file {context_name}")
        context_blocks.append(_render_file_block(f"Context: {context_name}", context_path, context_content))

    metadata_lines = [
        "# Run Metadata",
        "",
        f"- Run ID: {run_id}",
        f"- Repo Root: {repo_root}",
        f"- Task Path: {task_snapshot.path}",
        f"- Current Stage: {current_stage}",
        f"- Expected Transition: {expected_transition}",
    ]

    sections = [
        "\n".join(metadata_lines),
        _render_file_block("Role", resolved_role_path, role_content),
        _render_file_block("AI Guide", resolved_ai_guide_path, ai_guide_content),
        _render_file_block("Task", task_snapshot.path, task_content),
        *context_blocks,
    ]
    return "\n\n".join(sections).strip() + "\n"


def resolve_context_path(kanban_root: Path, context_name: str) -> Path:
    """Resolve a task `contexts:` entry to a concrete file path."""

    context_value = Path(context_name)
    candidates: list[Path] = []
    if context_value.is_absolute():
        candidates.append(context_value)
    else:
        base_context_root = kanban_root / "_context"
        candidates.append(base_context_root / context_value)
        if context_value.suffix != ".md":
            candidates.append((base_context_root / context_value).with_suffix(".md"))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise PromptAssemblyError(
        f"Missing context file for {context_name!r}. Checked: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def _expected_transition_text(config: OrchestratorConfig, current_stage: str) -> str:
    if current_stage == "plan":
        route = config.stage_routing["plan"]
        return f"{current_stage} -> {route.success_stage} ({route.success_agent})"
    if current_stage == "code":
        route = config.stage_routing["code"]
        return f"{current_stage} -> {route.success_stage} ({route.success_agent})"
    if current_stage == "audit":
        route = config.stage_routing["audit"]
        return (
            f"{current_stage} -> {route.accepted_stage} ({route.accepted_agent}) "
            f"when rating >= {route.accepted_rating}; otherwise -> {route.rework_stage} "
            f"({route.rework_agent})"
        )
    raise PromptAssemblyError(f"Unsupported stage for prompt assembly: {current_stage}")


def _read_required_file(path: Path, label: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PromptAssemblyError(f"Missing {label}: {path}") from exc


def _render_file_block(title: str, path: Path, content: str) -> str:
    return "\n".join(
        [
            f"## {title}",
            "",
            f"Path: {path}",
            "",
            "```md",
            content.rstrip(),
            "```",
        ]
    )
