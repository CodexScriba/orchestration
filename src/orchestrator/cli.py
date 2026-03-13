"""Command-line entry point for the orchestrator scaffold."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the orchestrator."""

    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Kanban2Code orchestration CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    _add_stub_command(subparsers, "run", cmd_run, "Run the orchestrator pipeline.")
    _add_stub_command(subparsers, "continue", cmd_continue, "Resume a saved orchestrator run.")
    _add_stub_command(subparsers, "status", cmd_status, "Show orchestrator status.")
    _add_stub_command(subparsers, "smoke-test", cmd_smoke_test, "Run provider smoke tests.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator CLI."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    return int(handler(args))


def cmd_run(_args: argparse.Namespace) -> int:
    """Handle the run subcommand."""

    print("Run command is not implemented yet.")
    return 0


def cmd_continue(_args: argparse.Namespace) -> int:
    """Handle the continue subcommand."""

    print("Continue command is not implemented yet.")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    """Handle the status subcommand."""

    print("Status command is not implemented yet.")
    return 0


def cmd_smoke_test(_args: argparse.Namespace) -> int:
    """Handle the smoke-test subcommand."""

    print("Smoke-test command is not implemented yet.")
    return 0


def _add_stub_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    handler: callable,
    help_text: str,
) -> None:
    subparser = subparsers.add_parser(name, help=help_text)
    subparser.set_defaults(handler=handler)
