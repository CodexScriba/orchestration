"""Session execution helpers for provider invocations."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import time

from orchestrator.models import SessionResult, StageTimeoutConfig


class SessionError(RuntimeError):
    """Raised when a provider session cannot be started or monitored."""


class TmuxSessionManager:
    """Run commands in monitorable sessions with timeout enforcement."""

    def __init__(
        self,
        *,
        repo_root: Path,
        poll_interval: float = 0.2,
        grace_seconds: float = 5.0,
        monotonic: callable | None = None,
        sleeper: callable | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.poll_interval = poll_interval
        self.grace_seconds = grace_seconds
        self._monotonic = monotonic or time.monotonic
        self._sleeper = sleeper or time.sleep

    def create_session_name(self, run_id: str, task_id: str, stage: str) -> str:
        """Create a normalized session name."""

        raw_name = f"orch-{run_id}-{task_id}-{stage}"
        return re.sub(r"[^a-zA-Z0-9_.-]+", "-", raw_name)

    def run_command(
        self,
        *,
        session_name: str,
        command: list[str],
        prompt: str,
        task_path: Path,
        output_dir: Path,
        timeouts: StageTimeoutConfig,
    ) -> SessionResult:
        """Run a command while monitoring for exit and file activity."""

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = output_dir / "prompt.md"
        output_path = output_dir / "session.log"
        exit_code_path = output_dir / "exit_code.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        task_path = Path(task_path)
        initial_task_mtime = task_path.stat().st_mtime if task_path.exists() else None
        output_file = output_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=self.repo_root,
            stdin=subprocess.PIPE,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if process.stdin is None:
            output_file.close()
            raise SessionError("Failed to open provider stdin.")

        process.stdin.write(prompt)
        process.stdin.close()

        started_at = self._monotonic()
        last_activity = started_at
        last_output_size = output_path.stat().st_size if output_path.exists() else 0
        task_mutated = False
        timeout_type: str | None = None

        while True:
            exit_code = process.poll()
            current_output_size = output_path.stat().st_size if output_path.exists() else 0
            current_task_mtime = task_path.stat().st_mtime if task_path.exists() else None

            if current_output_size != last_output_size:
                last_output_size = current_output_size
                last_activity = self._monotonic()

            if current_task_mtime != initial_task_mtime:
                task_mutated = True
                initial_task_mtime = current_task_mtime
                last_activity = self._monotonic()

            if exit_code is not None:
                break

            now = self._monotonic()
            if timeouts.wall_seconds and now - started_at > timeouts.wall_seconds:
                timeout_type = "wall"
                self._terminate_process(process)
                exit_code = process.wait()
                break
            if timeouts.idle_seconds and now - last_activity > timeouts.idle_seconds:
                timeout_type = "idle"
                self._terminate_process(process)
                exit_code = process.wait()
                break

            self._sleeper(self.poll_interval)

        output_file.close()
        exit_code_path.write_text(str(exit_code), encoding="utf-8")
        final_message = _read_final_message(output_path)

        return SessionResult(
            ok=bool(exit_code == 0 and timeout_type is None),
            session_name=session_name,
            exit_code=exit_code,
            timeout_type=timeout_type,
            output_path=str(output_path),
            prompt_path=str(prompt_path),
            exit_code_path=str(exit_code_path),
            task_mutated=task_mutated,
            final_message=final_message,
            command=list(command),
        )

    def cleanup_session(self, _session_name: str) -> None:
        """Placeholder cleanup hook for the local test runner."""

    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        process.terminate()
        deadline = self._monotonic() + self.grace_seconds
        while process.poll() is None and self._monotonic() < deadline:
            self._sleeper(min(self.poll_interval, 0.05))
        if process.poll() is None:
            process.kill()


def _read_final_message(path: Path) -> str | None:
    if not path.exists():
        return None

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    return lines[-1]
