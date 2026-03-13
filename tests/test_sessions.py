from __future__ import annotations

from pathlib import Path
import sys

from orchestrator.models import StageTimeoutConfig
from orchestrator.sessions import TmuxSessionManager


def test_session_creates_expected_name() -> None:
    manager = TmuxSessionManager(repo_root=Path("."))

    session_name = manager.create_session_name("run123", "task1.1", "plan")

    assert session_name == "orch-run123-task1.1-plan"


def test_session_detects_process_exit_and_task_mutation(tmp_path: Path) -> None:
    task_path = tmp_path / "task.md"
    task_path.write_text("before\n", encoding="utf-8")
    manager = TmuxSessionManager(repo_root=tmp_path)
    command = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; "
            "import sys; "
            "data = sys.stdin.read(); "
            "task = Path(sys.argv[1]); "
            "task.write_text(task.read_text() + data, encoding='utf-8'); "
            "print('finished')"
        ),
        str(task_path),
    ]

    result = manager.run_command(
        session_name="orch-run123-task-plan",
        command=command,
        prompt="\nchanged\n",
        task_path=task_path,
        output_dir=tmp_path / "out",
        timeouts=StageTimeoutConfig(wall_seconds=5, idle_seconds=5),
    )

    assert result.ok is True
    assert result.exit_code == 0
    assert result.task_mutated is True
    assert result.final_message == "finished"


def test_session_wall_timeout_triggers_kill(tmp_path: Path) -> None:
    task_path = tmp_path / "task.md"
    task_path.write_text("before\n", encoding="utf-8")
    manager = TmuxSessionManager(repo_root=tmp_path, poll_interval=0.05, grace_seconds=0.05)
    command = [sys.executable, "-c", "import time; time.sleep(1)"]

    result = manager.run_command(
        session_name="orch-run123-task-code",
        command=command,
        prompt="",
        task_path=task_path,
        output_dir=tmp_path / "out",
        timeouts=StageTimeoutConfig(wall_seconds=0.1, idle_seconds=0),
    )

    assert result.ok is False
    assert result.timeout_type == "wall"


def test_session_idle_timeout_triggers_kill(tmp_path: Path) -> None:
    task_path = tmp_path / "task.md"
    task_path.write_text("before\n", encoding="utf-8")
    manager = TmuxSessionManager(repo_root=tmp_path, poll_interval=0.05, grace_seconds=0.05)
    command = [sys.executable, "-c", "import time; time.sleep(1)"]

    result = manager.run_command(
        session_name="orch-run123-task-audit",
        command=command,
        prompt="",
        task_path=task_path,
        output_dir=tmp_path / "out",
        timeouts=StageTimeoutConfig(wall_seconds=0, idle_seconds=0.1),
    )

    assert result.ok is False
    assert result.timeout_type == "idle"


def test_session_cleanup_is_safe_noop() -> None:
    manager = TmuxSessionManager(repo_root=Path("."))
    manager.cleanup_session("orch-run123-task-plan")
