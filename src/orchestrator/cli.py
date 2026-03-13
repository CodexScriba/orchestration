"""Command-line entry point for the orchestrator scaffold."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from orchestrator.config import load_config
from orchestrator.dispatcher import Dispatcher
from orchestrator.scheduler import ConcurrentScheduler
from orchestrator.smoke import SmokeTester
from orchestrator.state import load_run_state, render_run_summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the orchestrator."""

    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Kanban2Code orchestration CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    _add_run_command(subparsers)
    _add_continue_command(subparsers)
    _add_status_command(subparsers)
    _add_smoke_test_command(subparsers)

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


def cmd_run(args: argparse.Namespace) -> int:
    """Handle the run subcommand."""

    repo_root = Path(args.repo_root).resolve()
    state_path = Path(args.state_path).resolve()
    config = load_config(repo_root / "config.json")

    if args.sequential or not config.scheduler.enabled:
        dispatcher = Dispatcher(
            repo_root=repo_root,
            config=config,
            run_state_path=state_path,
        )
        run_state = dispatcher.run()
    else:
        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=config,
            run_state_path=state_path,
        )
        run_state = scheduler.run()

    print(render_run_summary(run_state))
    return 0


def cmd_continue(args: argparse.Namespace) -> int:
    """Handle the continue subcommand."""

    repo_root = Path(args.repo_root).resolve()
    state_path = Path(args.state_path).resolve()
    config = load_config(repo_root / "config.json")
    saved_state = load_run_state(state_path)

    if args.sequential or not config.scheduler.enabled:
        dispatcher = Dispatcher(
            repo_root=repo_root,
            config=config,
            run_state_path=state_path,
        )
        run_state = dispatcher.resume(saved_state)
    else:
        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=config,
            run_state_path=state_path,
        )
        run_state = scheduler.run(run_state=saved_state)

    print(render_run_summary(run_state))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Handle the status subcommand."""

    state_path = Path(args.state_path).resolve()
    print(render_run_summary(load_run_state(state_path)))
    return 0


def cmd_smoke_test(args: argparse.Namespace) -> int:
    """Handle the smoke-test subcommand."""

    repo_root = Path(args.repo_root).resolve()
    dispatcher = Dispatcher(
        repo_root=repo_root,
        run_state_path=Path(args.state_path).resolve(),
    )
    tester = SmokeTester(dispatcher)
    results = tester.run_all()
    return 0 if all(results.values()) else 1


def _add_smoke_test_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    subparser = subparsers.add_parser("smoke-test", help="Run provider smoke tests.")
    _add_common_paths(subparser)
    subparser.set_defaults(handler=cmd_smoke_test)


def _add_stub_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    handler,
    help_text: str,
) -> None:
    subparser = subparsers.add_parser(name, help=help_text)
    subparser.set_defaults(handler=handler)


def _add_run_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    subparser = subparsers.add_parser("run", help="Run the orchestrator pipeline.")
    _add_common_paths(subparser)
    subparser.set_defaults(handler=cmd_run)


def _add_continue_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    subparser = subparsers.add_parser("continue", help="Resume a saved orchestrator run.")
    _add_common_paths(subparser)
    subparser.set_defaults(handler=cmd_continue)


def _add_status_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    subparser = subparsers.add_parser("status", help="Show orchestrator status.")
    subparser.add_argument(
        "--state-path",
        default=".kanban2code/runs/latest.json",
        help="Path to the persisted run state.",
    )
    subparser.set_defaults(handler=cmd_status)


def _add_common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing config.json and .kanban2code.",
    )
    parser.add_argument(
        "--state-path",
        default=".kanban2code/runs/latest.json",
        help="Path to the persisted run state.",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run tasks sequentially instead of concurrently.",
    )
