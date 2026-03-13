from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock

from orchestrator.cli import build_parser, main
from orchestrator.models import RunState


def create_dummy_config(tmp_path: Path, *, scheduler_enabled: bool = False):
    config_path = tmp_path / "config.json"
    config_data = {
        "schema_version": 1,
        "providers": {
            "planner": {"alias": "test", "model": "test", "config_overrides": {}},
            "coder": {"alias": "test", "model": "test", "config_overrides": {}},
            "auditor": {"alias": "test", "model": "test", "config_overrides": {}},
            "auditor_escalation": {"alias": "test", "model": "test", "config_overrides": {}}
        },
        "stage_routing": {
            "plan": {"agent": "planner", "success_stage": "code", "success_agent": "coder", "required_sections": []},
            "code": {"agent": "coder", "success_stage": "audit", "success_agent": "auditor", "required_sections": []},
            "audit": {"agent": "auditor", "accepted_stage": "completed", "accepted_agent": "auditor", "rework_stage": "code", "rework_agent": "coder", "required_sections": [], "accepted_rating": 8}
        },
        "timeouts": {
            "plan": {"wall_seconds": 60, "idle_seconds": 30},
            "code": {"wall_seconds": 60, "idle_seconds": 30},
            "audit": {"wall_seconds": 60, "idle_seconds": 30}
        },
        "retry_policy": {"transport_max_attempts": 3, "audit_failure_cycles_before_handoff": 2},
        "accounts": {"codex_pool": []},
        "notifications": {"telegram": {"enabled": False, "bot_token_env_var": "T", "chat_id_env_var": "C"}},
        "logging": {"date_folder_format": "%Y-%m-%d", "retain_recent_events": 20},
        "scheduler": {"max_concurrent": 4, "enabled": scheduler_enabled}
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")


def test_parser_registers_expected_subcommands() -> None:
    parser = build_parser()
    subparser_action = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )

    assert set(subparser_action.choices) == {"run", "continue", "status", "smoke-test"}


def test_main_dispatches_run(monkeypatch, tmp_path: Path, capsys) -> None:
    create_dummy_config(tmp_path)
    class FakeDispatcher:
        def __init__(self, *, repo_root: Path, config=None, logger=None, run_state_path: Path | None = None, account_manager=None):
            self.repo_root = repo_root
            self.run_state_path = run_state_path

        def run(self) -> RunState:
            return RunState(run_id="run-1", status="completed", updated_at="2026-03-13T00:00:00Z")

    monkeypatch.setattr("orchestrator.cli.Dispatcher", FakeDispatcher)

    exit_code = main(["run", "--repo-root", str(tmp_path), "--state-path", str(tmp_path / "run.json")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run-1" in captured.out


def test_main_dispatches_continue(monkeypatch, tmp_path: Path, capsys) -> None:
    create_dummy_config(tmp_path)
    state_path = tmp_path / "run.json"
    state_path.write_text(
        (
            '{\n'
            '  "run_id": "run-2",\n'
            '  "status": "running",\n'
            '  "created_at": "",\n'
            '  "updated_at": "",\n'
            '  "ordered_tasks": [],\n'
            '  "task_states": {},\n'
            '  "recent_events": [],\n'
            '  "current_index": 0,\n'
            '  "current_task": null,\n'
            '  "current_stage": null,\n'
            '  "last_error": null\n'
            '}\n'
        ),
        encoding="utf-8",
    )

    class FakeDispatcher:
        def __init__(self, *, repo_root: Path, config=None, logger=None, run_state_path: Path | None = None, account_manager=None):
            self.repo_root = repo_root
            self.run_state_path = run_state_path

        def resume(self, run_state: RunState) -> RunState:
            assert run_state.run_id == "run-2"
            return RunState(run_id="run-2", status="completed", updated_at="2026-03-13T00:01:00Z")

    monkeypatch.setattr("orchestrator.cli.Dispatcher", FakeDispatcher)

    exit_code = main(
        ["continue", "--repo-root", str(tmp_path), "--state-path", str(state_path)]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "completed" in captured.out


def test_main_dispatches_status(tmp_path: Path, capsys) -> None:
    state_path = tmp_path / "run.json"
    state_path.write_text(
        (
            '{\n'
            '  "run_id": "run-3",\n'
            '  "status": "running",\n'
            '  "created_at": "",\n'
            '  "updated_at": "",\n'
            '  "ordered_tasks": [],\n'
            '  "task_states": {},\n'
            '  "recent_events": [],\n'
            '  "current_index": 0,\n'
            '  "current_task": null,\n'
            '  "current_stage": null,\n'
            '  "last_error": null\n'
            '}\n'
        ),
        encoding="utf-8",
    )

    exit_code = main(["status", "--state-path", str(state_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run-3" in captured.out


def test_main_dispatches_smoke_test(monkeypatch, tmp_path: Path, capsys) -> None:
    create_dummy_config(tmp_path)
    
    mock_tester = MagicMock()
    mock_tester.run_all.return_value = {"test": True}
    monkeypatch.setattr("orchestrator.cli.SmokeTester", lambda dispatcher: mock_tester)
    
    exit_code = main(["smoke-test", "--repo-root", str(tmp_path)])
    assert exit_code == 0
    assert mock_tester.run_all.called


def test_main_dispatches_run_with_scheduler_when_enabled(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    create_dummy_config(tmp_path, scheduler_enabled=True)

    class FakeScheduler:
        def __init__(self, *, repo_root: Path, config=None, logger=None, run_state_path: Path | None = None):
            self.repo_root = repo_root
            self.run_state_path = run_state_path

        def run(self, *, ordered_tasks=None, run_state=None) -> RunState:
            return RunState(run_id="run-scheduler", status="completed", updated_at="2026-03-13T00:00:00Z")

    class FailingDispatcher:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Dispatcher should not be used when scheduler is enabled.")

    monkeypatch.setattr("orchestrator.cli.ConcurrentScheduler", FakeScheduler)
    monkeypatch.setattr("orchestrator.cli.Dispatcher", FailingDispatcher)

    exit_code = main(["run", "--repo-root", str(tmp_path), "--state-path", str(tmp_path / "run.json")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run-scheduler" in captured.out


def test_main_dispatches_run_with_sequential_flag(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    create_dummy_config(tmp_path, scheduler_enabled=True)

    class FakeDispatcher:
        def __init__(self, *, repo_root: Path, config=None, logger=None, run_state_path: Path | None = None, account_manager=None):
            self.repo_root = repo_root
            self.run_state_path = run_state_path

        def run(self) -> RunState:
            return RunState(run_id="run-sequential", status="completed", updated_at="2026-03-13T00:00:00Z")

    class FailingScheduler:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Scheduler should not be used when --sequential is set.")

    monkeypatch.setattr("orchestrator.cli.Dispatcher", FakeDispatcher)
    monkeypatch.setattr("orchestrator.cli.ConcurrentScheduler", FailingScheduler)

    exit_code = main(
        ["run", "--repo-root", str(tmp_path), "--state-path", str(tmp_path / "run.json"), "--sequential"]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run-sequential" in captured.out
