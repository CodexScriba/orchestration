from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator.cli import build_parser, main
from orchestrator.models import RunState


def test_parser_registers_expected_subcommands() -> None:
    parser = build_parser()
    subparser_action = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )

    assert set(subparser_action.choices) == {"run", "continue", "status", "smoke-test"}


def test_main_dispatches_run(monkeypatch, tmp_path: Path, capsys) -> None:
    class FakeDispatcher:
        def __init__(self, *, repo_root: Path, config=None, logger=None, run_state_path: Path | None = None):
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
        def __init__(self, *, repo_root: Path, config=None, logger=None, run_state_path: Path | None = None):
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


def test_main_dispatches_smoke_test(capsys) -> None:
    exit_code = main(["smoke-test"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "not implemented yet" in captured.out
