from __future__ import annotations

from pathlib import Path

from orchestrator.config import load_config
from orchestrator.dispatcher import Dispatcher
from orchestrator.models import RunState, StageResult
from orchestrator.state import load_run_state


def _write_task(path: Path, *, stage: str, agent: str, body: str = "# Task\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstage: {stage}\nagent: {agent}\n---\n{body}", encoding="utf-8")


class ScriptedDispatcher(Dispatcher):
    def __init__(self, *args, scripted_results: list[StageResult], task_path: Path, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._scripted_results = scripted_results
        self._task_path = task_path
        self.commit_calls: list[tuple[int, str | None, int]] = []

    def dispatch_stage(self, *, task_path: Path, run_id: str) -> StageResult:
        assert task_path == self._task_path
        return self._scripted_results.pop(0)


def test_run_loop_processes_single_task_to_completion(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    config_path = repo_root / "config.json"
    config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")
    task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
    _write_task(task_path, stage="plan", agent="planner")
    state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

    scripted_results = [
        StageResult(kind="success", stage="plan", success=True, after_stage="code"),
        StageResult(kind="success", stage="code", success=True, after_stage="audit"),
        StageResult(
            kind="success",
            stage="audit",
            success=True,
            after_stage="completed",
            audit_rating=9,
            provider_model="gpt",
        ),
    ]

    def fake_dispatch(self, *, task_path: Path, run_id: str) -> StageResult:
        result = scripted_results.pop(0)
        if result.after_stage == "code":
            _write_task(task_path, stage="code", agent="coder", body="## Refined Prompt\nx\n## Context\ny\n")
        elif result.after_stage == "audit":
            _write_task(task_path, stage="audit", agent="auditor", body="## Audit\nsrc/file.py\n")
        elif result.after_stage == "completed":
            _write_task(task_path, stage="completed", agent="auditor", body="## Review\nRating: 9\n## Audit\nsrc/file.py\n")
        return result

    commit_calls: list[dict[str, object]] = []

    def fake_commit_after_audit(**kwargs):
        commit_calls.append(kwargs)
        return None

    monkeypatch.setattr("orchestrator.dispatcher.Dispatcher.dispatch_stage", fake_dispatch)
    monkeypatch.setattr("orchestrator.dispatcher.commit_after_audit", fake_commit_after_audit)

    dispatcher = Dispatcher(repo_root=repo_root, config=load_config(config_path), run_state_path=state_path)
    run_state = dispatcher.run(ordered_tasks=[task_path])

    assert run_state.status == "completed"
    assert run_state.task_states[str(task_path)].status == "completed"
    assert commit_calls[0]["rating"] == 9


def test_bounce_counter_increments_and_third_cycle_handoffs(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    config_path = repo_root / "config.json"
    config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")
    task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
    _write_task(task_path, stage="audit", agent="auditor", body="## Review\nRating: 6\n")
    state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
    scripted_results = [
        StageResult(kind="quality_failure", stage="audit", after_stage="code", audit_rating=6),
        StageResult(kind="quality_failure", stage="audit", after_stage="code", audit_rating=6),
        StageResult(kind="quality_failure", stage="audit", after_stage="code", audit_rating=6),
    ]

    def fake_dispatch(self, *, task_path: Path, run_id: str) -> StageResult:
        _write_task(task_path, stage="audit", agent="auditor", body="## Review\nRating: 6\n")
        return scripted_results.pop(0)

    monkeypatch.setattr("orchestrator.dispatcher.Dispatcher.dispatch_stage", fake_dispatch)

    dispatcher = Dispatcher(repo_root=repo_root, config=load_config(config_path), run_state_path=state_path)
    run_state = dispatcher.run(ordered_tasks=[task_path])

    assert run_state.status == "handoff_required"
    assert run_state.task_states[str(task_path)].audit_failures == 3
    handoff = repo_root / ".kanban2code" / "runs" / run_state.run_id / "HANDOFF.md"
    assert handoff.exists()


def test_transport_retry_exhaustion_triggers_handoff(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    config_path = repo_root / "config.json"
    config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")
    task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
    _write_task(task_path, stage="code", agent="coder")
    state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

    def fake_dispatch(self, *, task_path: Path, run_id: str) -> StageResult:
        return StageResult(kind="transport_failure", stage="code")

    monkeypatch.setattr("orchestrator.dispatcher.Dispatcher.dispatch_stage", fake_dispatch)

    dispatcher = Dispatcher(repo_root=repo_root, config=load_config(config_path), run_state_path=state_path)
    run_state = dispatcher.run(ordered_tasks=[task_path])

    assert run_state.status == "handoff_required"
    assert run_state.task_states[str(task_path)].transport_attempts["code"] == 3


def test_continue_resumes_from_saved_state(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    config_path = repo_root / "config.json"
    config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")
    task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
    _write_task(task_path, stage="code", agent="coder")
    state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

    run_state = RunState(
        run_id="run-continue",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:00:00Z",
        status="running",
        ordered_tasks=[str(task_path)],
        task_states={str(task_path): __import__("orchestrator.models", fromlist=["TaskRunState"]).TaskRunState()},
        current_index=0,
        current_task=str(task_path),
        current_stage="code",
    )
    from orchestrator.state import save_run_state

    save_run_state(state_path, run_state)

    def fake_dispatch(self, *, task_path: Path, run_id: str) -> StageResult:
        _write_task(task_path, stage="completed", agent="auditor", body="## Review\nRating: 9\n## Audit\nsrc/file.py\n")
        return StageResult(
            kind="success",
            stage="audit",
            success=True,
            after_stage="completed",
            audit_rating=9,
            provider_model="gpt",
        )

    monkeypatch.setattr("orchestrator.dispatcher.Dispatcher.dispatch_stage", fake_dispatch)
    monkeypatch.setattr("orchestrator.dispatcher.commit_after_audit", lambda **_kwargs: None)

    dispatcher = Dispatcher(repo_root=repo_root, config=load_config(config_path), run_state_path=state_path)
    resumed = dispatcher.resume(load_run_state(state_path))

    assert resumed.status == "completed"
    assert resumed.current_task is None
