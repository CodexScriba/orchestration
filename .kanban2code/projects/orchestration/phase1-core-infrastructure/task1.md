---
stage: completed
tags: [feature, p1]
agent: auditor
contexts: [skills/python-core-skills]
---

# Task 1: Core Infrastructure

This task consolidates all Phase 1 tasks into a single comprehensive task for testing AI capabilities with long tasks.

---

## Task 1.1: Project scaffold and config system

### Goal

Set up the project scaffold, configuration system, task scanning, structured logging, and state management. This phase produces no executable pipeline — it builds the foundation every other phase depends on.

### Definition of Done

- [x] `src/orchestrator/` package exists with `__init__.py`, `cli.py`, `config.py`, `models.py`
- [x] `config.json` schema defined and loadable with validation errors on bad input
- [x] Config covers: provider mappings, stage routing, timeouts, retry policy, account pool, notification settings
- [x] `pyproject.toml` with dependencies (pyyaml, libtmux, python-telegram-bot) and dev dependencies (pytest, ruff)
- [x] CLI entry point registers `run`, `continue`, `status`, `smoke-test` subcommands (stubs)

### Files

- `src/orchestrator/__init__.py` - create - package init
- `src/orchestrator/cli.py` - create - argparse entry point
- `src/orchestrator/config.py` - create - config loading and validation
- `src/orchestrator/models.py` - create - dataclasses for all core types
- `config.json` - create - default orchestrator configuration
- `pyproject.toml` - create - project metadata and dependencies

### Tests

- [x] Config loads valid JSON and returns typed config object
- [x] Config rejects missing required fields with clear error
- [x] CLI registers all subcommands without error
- [x] Models are constructible with expected defaults

### Context

Phase 1: Core Infrastructure

### Refined Prompt
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

### Context

#### File Tree (scoped)
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

#### Architecture Excerpts
- Project Goal: Foundational infrastructure for orchestration.
- Config Requirements: Provider mappings, stage routing, timeouts, retry policy, account pool, notification settings.
- CLI Commands: run, continue, status, smoke-test.

#### Skill Excerpts
python-core-skills:
- Use `snake_case` for modules, functions, and variables.
- Use `PascalCase` for classes (e.g., `OrchestratorConfig`).
- All public functions and methods must have type hints and Google-style docstrings.
- Modules must include `from __future__ import annotations`.
- Avoid mutable default arguments in dataclasses or functions.

#### Code Excerpts
No existing code; this is a greenfield initialization task.

#### Dependency Graph
- `cli.py` -> imports `config.py` and `models.py`.
- `config.py` -> imports `models.py`.
- `models.py` -> standalone (standard library).

#### Patterns to Follow
- PEP 8 naming conventions.
- Structured logging (to be implemented as a stub/init in this phase).
- Fail-fast configuration validation.

#### Test Patterns
- Use `pytest`.
- Config tests should verify both successful loads and descriptive error messages for invalid files.
- CLI tests should use `capsys` or mock `sys.argv` to verify subcommand registration.

#### Gotchas
- Ensure `src/` is recognized as a package root by setting `packages = ["orchestrator"]` in `pyproject.toml` or using `package_dir`.

#### Scope Boundaries
This task is limited to the scaffold and static configuration. It should NOT touch actual pipeline logic, `libtmux` session management implementation, or Telegram bot polling logic beyond defining their configuration models.

### Audit

pyproject.toml
config.json
src/orchestrator/__init__.py
src/orchestrator/models.py
src/orchestrator/config.py
src/orchestrator/cli.py
tests/test_config.py
tests/test_cli.py
tests/test_models.py
.kanban2code/projects/orchestration/phase1-core-infrastructure/task1.1-project-scaffold-and-config-system.md

---

### Review

**Rating: 9/10**

**Verdict: ACCEPTED**

#### Summary
Clean, well-structured project scaffold with thorough configuration validation and good test coverage. The implementation faithfully meets every item in the Definition of Done.

#### Findings

##### Blockers
(none)

##### High Priority
(none)

##### Medium Priority
- [ ] `cli.py:72` — `handler` parameter typed as `callable` (lowercase) instead of `Callable` or `collections.abc.Callable`. This is a runtime string, not the proper type. Minor since it works at runtime but incorrect for static analysis.

##### Low Priority / Nits
- [ ] `PlanStageRoutingConfig` and `CodeStageRoutingConfig` are structurally identical — could be a single `LinearStageRoutingConfig`. Acceptable at scaffold stage; revisit if they diverge.
- [ ] `_parse_providers` hardcodes the four provider keys rather than iterating `raw_providers.keys()`. This is fine for fail-fast validation but means adding a new provider requires a code change in addition to a config change.
- [ ] No `tests/__init__.py` — not required by pytest but some tooling expects it.

#### Test Assessment
- Coverage: Adequate — happy path, missing key, invalid JSON, shipped config integration test, model defaults, and mutable-default isolation are all covered.
- Missing tests: A test for `ConfigError` on a missing config file (`FileNotFoundError` path) would round things out, but not blocking.

#### What's Good
- Robust validation with clear dotted-path error messages (e.g., `stage_routing.plan.success_stage`) — excellent DX.
- `bool` guard in `_require_int` prevents `True`/`False` from passing as ints — shows attention to Python's `bool` subclass gotcha.
- `slots=True` on all dataclasses — good memory discipline from the start.
- `from __future__ import annotations` consistently applied across all modules.
- Tests verify mutable default isolation — a common dataclass pitfall caught proactively.
- `pyproject.toml` correctly sets `package-dir` and `packages.find.where` for the `src/` layout.

#### Recommendations
- Add `pythonpath = ["src"]` under `[tool.pytest.ini_options]` in `pyproject.toml` so tests run without needing `PYTHONPATH=src` on the command line.

---

## Task 1.2: Task scanner and frontmatter parser

### Goal

Build a system that reads .kanban2code/ folders and parses YAML frontmatter into typed TaskSnapshots.

### Definition of Done

- [x] Scanner reads `.kanban2code/` folders recursively and finds all task `.md` files
- [x] YAML frontmatter is parsed into `TaskSnapshot` with typed fields (stage, agent, bounces, tags, contexts)
- [x] Scanner builds a per-project, per-stage index of tasks
- [x] Tasks in `_archive/`, `_agents/`, `_providers/`, `_context/` are excluded
- [x] Board state view: JSON object mapping `{project: {stage: [task_id, ...]}}` for Kadee

### Files

- `src/orchestrator/scanner.py` - create - task file discovery and frontmatter parsing
- `src/orchestrator/state.py` - create - board state view builder

### Tests

- [x] Scanner finds task files in inbox/, projects/*, and nested phase folders
- [x] Scanner excludes _archive, _agents, _providers, _context
- [x] Frontmatter parser extracts stage, agent, bounces, tags, contexts correctly
- [x] Frontmatter parser handles missing optional fields with defaults
- [x] Board state view produces correct project × stage matrix from sample tasks

### Context

Phase 1: Core Infrastructure

### Audit

src/orchestrator/models.py
src/orchestrator/scanner.py
src/orchestrator/state.py
tests/test_models.py
tests/test_scanner.py
.kanban2code/projects/orchestration/phase1-core-infrastructure/task1.md

---

### Review

**Rating: 9/10**

**Verdict: ACCEPTED**

#### Summary
Scanner and frontmatter parser are well-built with proper exclusion logic, deterministic ordering, and a clean board-state view. All five DoD items are met. No evidence of merge damage — models integrate cleanly with Task 1.1's dataclasses.

#### Findings

##### Blockers
(none)

##### High Priority
(none)

##### Medium Priority
- [ ] `state.py:11` — `build_board_index` is a thin pass-through to `scanner.index_tasks_by_project_and_stage`. Creates a `state -> scanner` coupling; if `scanner` ever needs `state`, you'll hit a circular import. Consider moving `index_tasks_by_project_and_stage` into `state.py` directly or inlining it.

##### Low Priority / Nits
- [ ] `scanner.py:14-16` — The frontmatter regex uses `\A` anchor + `re.DOTALL` which is correct, but a document with `---` on line 1 and no closing `---` raises `ValueError("Unterminated YAML frontmatter block.")`. This is the right behavior but worth noting for task files that are still being edited.
- [ ] `scanner.py:71` — `_optional_str` strips/lowercases stage and agent in `parse_task_file` (lines 71-72) *before* storing in `TaskSnapshot`, but `TaskSnapshot.__post_init__` also does `self.stage.strip().lower()` — double normalization. Harmless but redundant.
- [ ] `__init__.py` only exports Task 1.1 items (`ConfigError`, `load_config`, `OrchestratorConfig`). Scanner, state, and logger are not in the public API surface. Fine for now; revisit when building the pipeline.

#### Test Assessment
- Coverage: Adequate — discovery with exclusion, frontmatter extraction with normalization, missing optional fields, non-mapping frontmatter error, and deterministic board state ordering are all covered.
- Missing tests: No test for `_derive_project_name` with a path outside `.kanban2code/` (the `ValueError` path). Not blocking.

#### What's Good
- `EXCLUDED_DIR_NAMES` as a frozenset-like constant with clear membership check — easy to extend.
- `_is_excluded` checks all path parts, not just immediate parent — correctly catches nested `_context/` dirs like `projects/orchestration/_context/`.
- `split_frontmatter` validates that parsed YAML is a mapping — catches `--- \n- list \n---` edge case.
- `_optional_int` has the same `bool` guard as config's `_require_int` — consistent defensive pattern.
- Board state test verifies multi-project, multi-stage matrix in a single assertion — good integration coverage.

#### Recommendations
- Collapse the double normalization: either remove `.strip().lower()` from `parse_task_file` lines 71-72 and let `__post_init__` handle it, or vice versa.

---

## Task 1.3: Structured logging and run state persistence

### Goal

Implement JSONL logging and run state persistence to track execution progress.

### Definition of Done

- [x] JSONL logger writes one event per line with timestamp, type, message, and arbitrary extras
- [x] Run state persists as JSON with schema version, run ID, ordered tasks, task states, recent events
- [x] Events include: run_started, run_resumed, stage_success, stage_transport_failure, audit_rework, run_handoff, run_completed
- [x] Summary markdown is auto-generated from run state
- [x] Recent events are capped (configurable, default 20)

### Files

- `src/orchestrator/logger.py` - create - structured JSONL logging
- `src/orchestrator/state.py` - modify - add run state persistence and summary generation

### Tests

- [x] Logger appends events as valid JSONL lines
- [x] Run state round-trips through save/load without data loss
- [x] Summary markdown is generated from run state with correct formatting
- [x] Recent events list respects the configured cap

### Context

Phase 1: Core Infrastructure

### Audit

src/orchestrator/models.py
src/orchestrator/logger.py
src/orchestrator/state.py
tests/test_models.py
tests/test_logger.py
tests/test_state.py
.kanban2code/projects/orchestration/phase1-core-infrastructure/task1.md

---

### Review

**Rating: 8/10**

**Verdict: ACCEPTED**

#### Summary
Logger and run-state persistence are clean and functional. JSONL append, JSON round-trip, event capping, and markdown summary all work correctly. All five DoD items are met. The mid-development merge did not cause any data model conflicts — `RunEvent`, `TaskRunState`, and `RunState` coexist cleanly with Task 1.1/1.2 models in a single `models.py`.

#### Findings

##### Blockers
(none)

##### High Priority
(none)

##### Medium Priority
- [ ] `state.py:103-104` — `append_recent_event` uses `run_state.recent_events[-max_events:]` with guard `if max_events >= 0`. When `max_events=0`, Python evaluates `list[-0:]` as `list[0:]` (full list), so `max_events=0` silently means "keep all" instead of "keep none." This is a semantic bug — the config default of 20 masks it, but any consumer passing 0 expecting an empty cap would be surprised. Fix: add `if max_events == 0: run_state.recent_events.clear(); return` or use `max_events > 0`.
- [ ] `state.py:70-90` — `load_run_state` uses `.get()` with fallback defaults for every field, meaning a corrupted or truncated JSON file silently loads with empty strings instead of raising. Consider validating at least `schema_version` and `run_id` are present.

##### Low Priority / Nits
- [ ] Event types (`run_started`, `run_resumed`, `stage_success`, etc.) are string conventions with no enum or constant — easy to typo. A `class EventType(str, Enum)` would add safety. Not blocking for scaffold phase.
- [ ] `logger.py:57` — `_utc_now_iso` replaces `+00:00` with `Z` via string replacement. Correct per ISO-8601 but brittle if the datetime library ever changes its format. `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")` would be more explicit.
- [ ] `render_run_summary` line 136: marker logic — a task at `index < current_index` with `status != "completed"` shows `>` (active), which could imply it's currently running when it may have been skipped or failed. Minor UX ambiguity in the summary output.

#### Test Assessment
- Coverage: Adequate — JSONL append (single and multi-event), run-state JSON round-trip with nested models, event cap enforcement, and summary markdown content assertions are all covered.
- Missing tests: No test for `render_run_summary` with an empty queue (the `"- none"` branch). No test for `load_run_state` with missing or extra fields (resilience). Not blocking.

#### What's Good
- `JsonlLogger.append` returns the `RunEvent` model — callers can immediately pass it to `append_recent_event` without reconstructing.
- `save_run_state` auto-creates parent directories — no need for callers to manage paths.
- `load_run_state` correctly reconstructs nested `TaskRunState` and `RunEvent` objects from raw dicts — proper deserialization without a framework.
- `render_run_summary` produces clean, human-readable markdown with queue checklist markers (`[x]`, `[>]`, `[ ]`) — useful for both humans and downstream reporting.
- `_utc_now_iso` is extracted as a testable/mockable function — good for deterministic testing.

#### Recommendations
- Fix the `max_events=0` edge case in `append_recent_event` — guard with `if max_events > 0` instead of `>= 0`.
- Consider adding a `validate_run_state` helper that checks required fields after loading, rather than silently defaulting everything.
