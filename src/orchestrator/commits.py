"""Git commit helpers for accepted audit outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess


@dataclass(slots=True)
class CommitResult:
    """Outcome of a surgical audit commit."""

    committed: bool = False
    staged_files: list[str] = field(default_factory=list)
    commit_message: str | None = None
    warning: str | None = None
    branch_created: str | None = None


class CommitError(RuntimeError):
    """Raised when a commit operation fails."""


def commit_after_audit(
    *,
    repo_root: Path,
    task_path: Path,
    rating: int,
    model: str | None,
    bounces: int,
    branch_name: str | None = None,
) -> CommitResult:
    """Create a surgical git commit after a successful audit."""

    repo_root = Path(repo_root)
    task_path = Path(task_path)
    task_text = task_path.read_text(encoding="utf-8")
    staged_candidates = _parse_audit_paths(task_text, task_path.parent)
    staged_candidates.append(task_path)

    architecture_path = repo_root / ".kanban2code" / "_context" / "architecture.md"
    if architecture_path.exists():
        staged_candidates.append(architecture_path)

    unique_candidates = []
    seen: set[Path] = set()
    for path in staged_candidates:
        resolved = path.resolve()
        if resolved not in seen:
            unique_candidates.append(path)
            seen.add(resolved)

    changed_files = [path for path in unique_candidates if _is_changed(repo_root, path)]
    if not changed_files:
        return CommitResult(committed=False, warning="No changed files to stage.")

    for path in changed_files:
        _run_git(repo_root, "add", str(path))

    message = _build_commit_message(
        task_text=task_text,
        task_id=task_path.stem,
        rating=rating,
        model=model,
        file_count=len(changed_files),
        bounces=bounces,
    )
    _run_git(repo_root, "commit", "-m", message)

    created_branch: str | None = None
    if branch_name:
        existing = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if existing.returncode != 0:
            _run_git(repo_root, "branch", branch_name)
            created_branch = branch_name

    return CommitResult(
        committed=True,
        staged_files=[str(path) for path in changed_files],
        commit_message=message,
        branch_created=created_branch,
    )


def _build_commit_message(
    *,
    task_text: str,
    task_id: str,
    rating: int,
    model: str | None,
    file_count: int,
    bounces: int,
) -> str:
    description = "update task"
    for line in task_text.splitlines():
        if line.startswith("# "):
            description = line[2:].strip()
            break
    model_label = model or "unknown-model"
    return (
        f"feat({task_id}): {description}\n\n"
        f"Audited: {rating}/10 by {model_label}\n"
        f"Files: {file_count} files changed\n"
        f"Bounces: {bounces}"
    )


def _parse_audit_paths(task_text: str, task_dir: Path) -> list[Path]:
    lines = task_text.splitlines()
    in_audit = False
    paths: list[Path] = []
    for raw_line in lines:
        line = raw_line.strip()
        if raw_line.startswith("## "):
            in_audit = raw_line == "## Audit"
            continue
        if not in_audit or not line:
            continue
        normalized = line.lstrip("-* ").strip("`")
        if normalized:
            paths.append((task_dir / normalized).resolve())
    return paths


def _is_changed(repo_root: Path, path: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", str(path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CommitError(result.stderr.strip() or "Failed to query git status.")
    return bool(result.stdout.strip())


def _run_git(repo_root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CommitError(result.stderr.strip() or f"git {' '.join(args)} failed")
