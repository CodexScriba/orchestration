from __future__ import annotations

from pathlib import Path
import subprocess

from orchestrator.commits import commit_after_audit


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(path: Path) -> None:
    _run(["git", "init"], path)
    _run(["git", "config", "user.email", "test@example.com"], path)
    _run(["git", "config", "user.name", "Test User"], path)


def test_commit_stages_only_specified_files_and_formats_message(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    tracked_file = repo_root / "src" / "file.py"
    tracked_file.parent.mkdir(parents=True)
    tracked_file.write_text("print('one')\n", encoding="utf-8")
    architecture_path = repo_root / ".kanban2code" / "_context" / "architecture.md"
    architecture_path.parent.mkdir(parents=True)
    architecture_path.write_text("architecture\n", encoding="utf-8")
    task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
    task_path.parent.mkdir(parents=True)
    task_path.write_text(
        (
            "---\nstage: completed\nagent: auditor\n---\n"
            "# Task 2: Single-Task Execution Engine\n\n"
            "## Audit\n"
            "../../../src/file.py\n"
        ),
        encoding="utf-8",
    )
    _run(["git", "add", str(tracked_file), str(task_path), str(architecture_path)], repo_root)
    _run(["git", "commit", "-m", "initial"], repo_root)

    tracked_file.write_text("print('two')\n", encoding="utf-8")
    architecture_path.write_text("architecture changed\n", encoding="utf-8")
    task_path.write_text(
        task_path.read_text(encoding="utf-8") + "Updated audit.\n",
        encoding="utf-8",
    )
    ignored_file = repo_root / "ignored.txt"
    ignored_file.write_text("ignore me\n", encoding="utf-8")

    result = commit_after_audit(
        repo_root=repo_root,
        task_path=task_path,
        rating=9,
        model="gpt-5.3-codex",
        bounces=1,
    )

    assert result.committed is True
    assert str(ignored_file) not in result.staged_files
    log_message = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "feat(task): Task 2: Single-Task Execution Engine" in log_message
    assert "Audited: 9/10 by gpt-5.3-codex" in log_message
    assert "Bounces: 1" in log_message


def test_commit_skips_when_no_files_changed(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
    task_path.parent.mkdir(parents=True)
    task_path.write_text("---\nstage: completed\nagent: auditor\n---\n# Task\n\n## Audit\n", encoding="utf-8")
    _run(["git", "add", str(task_path)], repo_root)
    _run(["git", "commit", "-m", "initial"], repo_root)

    result = commit_after_audit(
        repo_root=repo_root,
        task_path=task_path,
        rating=9,
        model="gpt",
        bounces=0,
    )

    assert result.committed is False
    assert result.warning == "No changed files to stage."


def test_commit_can_create_branch_when_requested(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    tracked_file = repo_root / "src" / "file.py"
    tracked_file.parent.mkdir(parents=True)
    tracked_file.write_text("print('one')\n", encoding="utf-8")
    task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
    task_path.parent.mkdir(parents=True)
    task_path.write_text(
        "---\nstage: completed\nagent: auditor\n---\n# Task\n\n## Audit\n../../../src/file.py\n",
        encoding="utf-8",
    )
    _run(["git", "add", str(tracked_file), str(task_path)], repo_root)
    _run(["git", "commit", "-m", "initial"], repo_root)
    tracked_file.write_text("print('two')\n", encoding="utf-8")

    result = commit_after_audit(
        repo_root=repo_root,
        task_path=task_path,
        rating=8,
        model="gpt",
        bounces=0,
        branch_name="milestone/phase2",
    )

    assert result.branch_created == "milestone/phase2"


def test_commit_module_never_uses_git_add_dot_variants() -> None:
    source = Path("src/orchestrator/commits.py").read_text(encoding="utf-8")
    assert "git add ." not in source
    assert "git add -A" not in source
