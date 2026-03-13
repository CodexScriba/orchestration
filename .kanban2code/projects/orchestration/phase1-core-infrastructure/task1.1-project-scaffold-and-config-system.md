---
stage: code
tags: [feature, p1]
agent: coder
contexts: [skills/python-core-skills]
---

# Task 1.1: Project scaffold and config system

## Goal

Set up the project scaffold, configuration system, task scanning, structured logging, and state management. This phase produces no executable pipeline — it builds the foundation every other phase depends on.

## Definition of Done

- [ ] `src/orchestrator/` package exists with `__init__.py`, `cli.py`, `config.py`, `models.py`
- [ ] `config.json` schema defined and loadable with validation errors on bad input
- [ ] Config covers: provider mappings, stage routing, timeouts, retry policy, account pool, notification settings
- [ ] `pyproject.toml` with dependencies (pyyaml, libtmux, python-telegram-bot) and dev dependencies (pytest, ruff)
- [ ] CLI entry point registers `run`, `continue`, `status`, `smoke-test` subcommands (stubs)

## Files

- `src/orchestrator/__init__.py` - create - package init
- `src/orchestrator/cli.py` - create - argparse entry point
- `src/orchestrator/config.py` - create - config loading and validation
- `src/orchestrator/models.py` - create - dataclasses for all core types
- `config.json` - create - default orchestrator configuration
- `pyproject.toml` - create - project metadata and dependencies

## Tests

- [ ] Config loads valid JSON and returns typed config object
- [ ] Config rejects missing required fields with clear error
- [ ] CLI registers all subcommands without error
- [ ] Models are constructible with expected defaults

## Context

Phase 1: Core Infrastructure

## Refined Prompt
Objective: Establish the foundational Python project structure, CLI entry point, and type-safe configuration system for the orchestrator.

Implementation approach:
1. Initialize `pyproject.toml` using `setuptools` or `poetry` style with specified dependencies (`pyyaml`, `libtmux`, `python-telegram-bot`) and development tools (`pytest`, `ruff`).
2. Define core configuration schemas using `dataclasses` in `models.py`, ensuring all fields mentioned in the Goal are present.
3. Implement a robust JSON loader in `config.py` that maps `config.json` to the `OrchestratorConfig` model, including manual validation for required fields.
4. Set up the `cli.py` entry point using `argparse` to handle the `run`, `continue`, `status`, and `smoke-test` subcommands as stubs.
5. Create a default `config.json` reflecting the required structure for provider mappings and policies.

Key decisions:
- Dataclasses over Pydantic: Use standard library `dataclasses` for models to keep the core infrastructure lightweight unless complex validation is requested.
- Argparse for CLI: Standard library `argparse` is sufficient for the initial subcommand stubs.

Edge cases:
- `config.json` missing or containing invalid JSON syntax.
- Missing mandatory configuration keys (e.g., empty provider mappings).
- CLI invoked with an unsupported subcommand.

## Context

### File Tree (scoped)
```
.
├── pyproject.toml                # <- create
├── config.json                   # <- create
└── src/
    └── orchestrator/
        ├── __init__.py           # <- create
        ├── cli.py                # <- create
        ├── config.py             # <- create
        └── models.py             # <- create
```

### Architecture Excerpts
- Project Goal: Foundational infrastructure for orchestration.
- Config Requirements: Provider mappings, stage routing, timeouts, retry policy, account pool, notification settings.
- CLI Commands: run, continue, status, smoke-test.

### Skill Excerpts
python-core-skills:
- Use `snake_case` for modules, functions, and variables.
- Use `PascalCase` for classes (e.g., `OrchestratorConfig`).
- All public functions and methods must have type hints and Google-style docstrings.
- Modules must include `from __future__ import annotations`.
- Avoid mutable default arguments in dataclasses or functions.

### Code Excerpts
No existing code; this is a greenfield initialization task.

### Dependency Graph
- `cli.py` -> imports `config.py` and `models.py`.
- `config.py` -> imports `models.py`.
- `models.py` -> standalone (standard library).

### Patterns to Follow
- PEP 8 naming conventions.
- Structured logging (to be implemented as a stub/init in this phase).
- Fail-fast configuration validation.

### Test Patterns
- Use `pytest`.
- Config tests should verify both successful loads and descriptive error messages for invalid files.
- CLI tests should use `capsys` or mock `sys.argv` to verify subcommand registration.

### Gotchas
- Ensure `src/` is recognized as a package root by setting `packages = ["orchestrator"]` in `pyproject.toml` or using `package_dir`.

### Scope Boundaries
This task is limited to the scaffold and static configuration. It should NOT touch actual pipeline logic, `libtmux` session management implementation, or Telegram bot polling logic beyond defining their configuration models.
