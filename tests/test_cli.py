from __future__ import annotations

import argparse

from orchestrator.cli import build_parser, main


def test_parser_registers_expected_subcommands() -> None:
    parser = build_parser()
    subparser_action = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )

    assert set(subparser_action.choices) == {"run", "continue", "status", "smoke-test"}


def test_main_dispatches_stub_commands(capsys) -> None:
    for command_name in ("run", "continue", "status", "smoke-test"):
        exit_code = main([command_name])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "not implemented yet" in captured.out
