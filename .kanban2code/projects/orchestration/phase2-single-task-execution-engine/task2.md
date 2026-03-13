---
stage: completed
tags: [feature, p2]
agent: auditor
contexts: [skills/python-core-skills]
---

# Task 2: Single-Task Execution Engine

Build the core execution loop: provider abstraction, prompt assembly, tmux sessions, stage dispatch, result evaluation, bounce tracking, and auto-commit. End result: one task can go through plan → code → audit → completed using configured providers.

---

## Unified Goal

Implement a complete single-task execution engine that can take a Kanban2Code task from plan through code to audit and completion. This includes:

1. **Provider abstraction** — A pluggable interface with a working Codex implementation first; other providers arrive in later phases
2. **Prompt assembly** — Injecting actual file contents into prompts, never placeholders
3. **tmux session management** — Running providers in visible, monitorable sessions with timeout enforcement
4. **Stage dispatch and evaluation** — Running stages and detecting success/failure from frontmatter transitions
5. **Bounce tracking and run loop** — Processing tasks through stages with audit bounce limits and transport retries
6. **Auto-commit** — Surgical git commits after successful audit passes

---

## Unified Task List

| # | Subtask | Description | Files |
|---|---------|-------------|-------|
| 2.1 | Provider abstraction and Codex CLI provider | Create `BaseProvider` abstract class and `CodexProvider` implementation | `providers/__init__.py`, `providers/base.py`, `providers/codex.py` |
| 2.2 | Prompt assembler | Build prompts by injecting actual file contents (role, ai-guide, task, contexts) | `prompts.py` |
| 2.3 | tmux session manager | Create, monitor, and tear down tmux sessions with timeout enforcement | `sessions.py` |
| 2.4 | Stage dispatcher and result evaluator | Run providers and evaluate frontmatter transitions to determine success/failure | `dispatcher.py`, `evaluator.py` |
| 2.5 | Bounce tracker and run loop | Core loop processing tasks with bounce limits and transport retries | `dispatcher.py` (modify), `state.py` (modify) |
| 2.6 | Auto-commit after audit pass | Surgical git commits after successful audits | `commits.py` |

---

## Unified Definition of Done

### Provider System
- [x] `BaseProvider` abstract class defines: `invoke(prompt, task_path, output_dir, timeouts) → InvocationResult`
- [x] `CodexProvider` implements `BaseProvider` using subprocess + tmux
- [x] Provider loads CLI config from `.kanban2code/_providers/*.md` frontmatter
- [x] InvocationResult captures: ok, exit_code, timeout_type, final_message, output_paths, error_message, command
- [x] Provider validates that the CLI binary exists on PATH before invocation

### Prompt Assembly
- [x] Assembles full prompt from: role file, ai-guide.md, task file, context files
- [x] Injects actual file contents — never placeholders or summaries
- [x] Includes run metadata: run ID, repo root, task path, current stage, expected transition
- [x] Context files resolved from task frontmatter `contexts:` field
- [x] Handles missing context files with a clear error rather than silent omission

### Session Management
- [x] Creates named tmux sessions for each stage invocation (e.g., `orch-run123-task1.1-plan`)
- [x] Runs provider CLI command inside the tmux session
- [x] Monitors session: polls for process exit and task file mutation
- [x] Enforces wall timeout and idle timeout (configurable per stage)
- [x] Kills session cleanly on timeout (SIGTERM then SIGKILL)
- [x] Returns session output path for debugging

### Stage Dispatch and Evaluation
- [x] Dispatcher takes a task path, selects provider, assembles prompt, spawns session, waits, evaluates
- [x] Evaluator compares before/after TaskSnapshots to determine result kind
- [x] Plan result: success if stage moved to code + required sections present; blocked if questions added
- [x] Code result: success if stage moved to audit + Audit section present + file changed
- [x] Audit result: success if rating ≥ 8 + completed; quality_failure if rating < 8 + back to code
- [x] Transport failure if expected transition did not happen
- [x] All results include provider key, alias, model, exit code, output paths

### Run Loop and Bounce Tracking
- [x] Run loop processes ordered queue: for each task, execute stages until completed or blocked
- [x] Bounce tracker counts audit failures per task (stored in task state)
- [x] Max 2 audit bounces: third cycle triggers handoff stop
- [x] Transport retry: up to 3 attempts per stage before escalation
- [x] Handoff writes human-readable readme with context for Dan
- [x] Run state updated after every stage with current index, task, stage
- [x] `continue` command resumes from persisted run state

### Auto-Commit
- [x] On audit acceptance, commit immediately
- [x] Only stage files listed in the task's Audit section + task file + architecture.md if changed
- [x] Never use `git add .` or `git add -A`
- [x] Commit message format: `feat(task-id): description\n\nAudited: rating/10 by MODEL\nFiles: N files changed\nBounces: N`
- [x] Skip commit if no files to stage (log warning)
- [x] Branch creation after phase/milestone completion (configurable)

---

## Execution Order / Dependencies

```
2.1 Provider abstraction ──┐
                           │
2.2 Prompt assembler ──────┤
                           │
2.3 tmux session manager ──┼──► 2.4 Stage dispatcher ──► 2.5 Run loop ──► 2.6 Auto-commit
                           │           │                      │
                           └───────────┴──────────────────────┘
```

**Dependencies:**
- **2.1, 2.2, 2.3** can be built in parallel (no interdependencies)
- **2.4** depends on 2.1, 2.2, 2.3 (dispatcher uses providers, prompts, and sessions)
- **2.5** depends on 2.4 (run loop uses dispatcher)
- **2.6** depends on 2.5 (commit happens after audit pass in run loop)

**Recommended build order:**
1. Build 2.1, 2.2, 2.3 in parallel or sequentially
2. Build 2.4 (integrates the above)
3. Build 2.5 (adds run loop logic)
4. Build 2.6 (adds commit logic)

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/orchestrator/providers/__init__.py` | create | Provider package init |
| `src/orchestrator/providers/base.py` | create | Abstract provider interface |
| `src/orchestrator/providers/codex.py` | create | Codex CLI implementation |
| `src/orchestrator/prompts.py` | create | Prompt assembly logic |
| `src/orchestrator/sessions.py` | create | tmux session lifecycle management |
| `src/orchestrator/dispatcher.py` | create | Stage execution orchestration |
| `src/orchestrator/evaluator.py` | create | Before/after snapshot comparison |
| `src/orchestrator/state.py` | modify | Add handoff readme generation |
| `src/orchestrator/commits.py` | create | Git commit logic |

---

## Tests

### Provider Tests
- [x] CodexProvider builds correct command line from provider config
- [x] CodexProvider detects missing binary gracefully
- [x] InvocationResult correctly reports success/failure/timeout
- [x] Provider loads config from a sample .md frontmatter file

### Prompt Tests
- [x] Prompt includes role file content verbatim
- [x] Prompt includes ai-guide.md content
- [x] Prompt includes task file content
- [x] Prompt includes context file contents from task frontmatter
- [x] Missing context file raises a clear error
- [x] Prompt includes expected transition text for each stage

### Session Tests
- [x] Session creates with correct name format
- [x] Session detects process exit
- [x] Wall timeout triggers session kill
- [x] Idle timeout triggers session kill
- [x] Session cleanup removes finished sessions

### Dispatcher/Evaluator Tests
- [x] Plan success detected when frontmatter changes to stage: code, agent: coder
- [x] Plan blocked detected when Questions section added
- [x] Code success detected when frontmatter changes to stage: audit, agent: auditor
- [x] Audit acceptance detected when rating ≥ 8 and stage: completed
- [x] Audit rework detected when rating < 8 and stage: code
- [x] Transport failure detected when no expected transition occurs

### Run Loop Tests
- [x] Run loop processes a single task through plan → code → audit → completed
- [x] Bounce counter increments on audit failure
- [x] Third audit cycle triggers handoff stop
- [x] Transport retry exhaustion triggers handoff stop
- [x] Continue resumes from the correct task and stage
- [x] Handoff readme contains task context and failure reason

### Commit Tests
- [x] Commit stages only the specified files
- [x] Commit message follows the defined format
- [x] No commit when file list is empty (warning logged)
- [x] `git add .` and `git add -A` never appear in the code
- [x] Branch created when configured for milestone

---

## Original Source Content

The sections below contain the original task definitions preserved for reference.

---

### Task 2.1: Provider abstraction and Codex CLI provider

#### Goal

Create a BaseProvider abstract class and implement a Codex CLI provider.

#### Definition of Done

- [x] `BaseProvider` abstract class defines: `invoke(prompt, task_path, output_dir, timeouts) → InvocationResult`
- [x] `CodexProvider` implements `BaseProvider` using subprocess + tmux
- [x] Provider loads CLI config from `.kanban2code/_providers/*.md` frontmatter
- [x] InvocationResult captures: ok, exit_code, timeout_type, final_message, output_paths, error_message, command
- [x] Provider validates that the CLI binary exists on PATH before invocation

#### Files

- `src/orchestrator/providers/__init__.py` - create - provider package init
- `src/orchestrator/providers/base.py` - create - abstract provider interface
- `src/orchestrator/providers/codex.py` - create - Codex CLI implementation

#### Tests

- [x] CodexProvider builds correct command line from provider config
- [x] CodexProvider detects missing binary gracefully
- [x] InvocationResult correctly reports success/failure/timeout
- [x] Provider loads config from a sample .md frontmatter file

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.2: Prompt assembler

#### Goal

Build a system that assembles full prompts by injecting actual file contents.

#### Definition of Done

- [x] Assembles full prompt from: role file, ai-guide.md, task file, context files
- [x] Injects actual file contents — never placeholders or summaries
- [x] Includes run metadata: run ID, repo root, task path, current stage, expected transition
- [x] Context files resolved from task frontmatter `contexts:` field
- [x] Handles missing context files with a clear error rather than silent omission

#### Files

- `src/orchestrator/prompts.py` - create - prompt assembly logic

#### Tests

- [x] Prompt includes role file content verbatim
- [x] Prompt includes ai-guide.md content
- [x] Prompt includes task file content
- [x] Prompt includes context file contents from task frontmatter
- [x] Missing context file raises a clear error
- [x] Prompt includes expected transition text for each stage

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.3: tmux session manager

#### Goal

Implement programmatic tmux session management for running agent CLIs.

#### Definition of Done

- [x] Creates named tmux sessions for each stage invocation (e.g., `orch-run123-task1.1-plan`)
- [x] Runs provider CLI command inside the tmux session
- [x] Monitors session: polls for process exit and task file mutation
- [x] Enforces wall timeout and idle timeout (configurable per stage)
- [x] Kills session cleanly on timeout (SIGTERM then SIGKILL)
- [x] Returns session output path for debugging

#### Files

- `src/orchestrator/sessions.py` - create - tmux session lifecycle management

#### Tests

- [x] Session creates with correct name format
- [x] Session detects process exit
- [x] Wall timeout triggers session kill
- [x] Idle timeout triggers session kill
- [x] Session cleanup removes finished sessions

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.4: Stage dispatcher and result evaluator

#### Goal

Build the stage execution logic that runs providers and evaluates frontmatter transitions.

#### Definition of Done

- [x] Dispatcher takes a task path, selects provider, assembles prompt, spawns session, waits, evaluates
- [x] Evaluator compares before/after TaskSnapshots to determine result kind
- [x] Plan result: success if stage moved to code + required sections present; blocked if questions added
- [x] Code result: success if stage moved to audit + Audit section present + file changed
- [x] Audit result: success if rating ≥ 8 + completed; quality_failure if rating < 8 + back to code
- [x] Transport failure if expected transition did not happen
- [x] All results include provider key, alias, model, exit code, output paths

#### Files

- `src/orchestrator/dispatcher.py` - create - stage execution orchestration
- `src/orchestrator/evaluator.py` - create - before/after snapshot comparison

#### Tests

- [x] Plan success detected when frontmatter changes to stage: code, agent: coder
- [x] Plan blocked detected when Questions section added
- [x] Code success detected when frontmatter changes to stage: audit, agent: auditor
- [x] Audit acceptance detected when rating ≥ 8 and stage: completed
- [x] Audit rework detected when rating < 8 and stage: code
- [x] Transport failure detected when no expected transition occurs

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.5: Bounce tracker and run loop

#### Goal

Implement the core run loop that processes tasks and tracks audit bounces.

#### Definition of Done

- [x] Run loop processes ordered queue: for each task, execute stages until completed or blocked
- [x] Bounce tracker counts audit failures per task (stored in task state)
- [x] Max 2 audit bounces: third cycle triggers handoff stop
- [x] Transport retry: up to 3 attempts per stage before escalation
- [x] Handoff writes human-readable readme with context for Dan
- [x] Run state updated after every stage with current index, task, stage
- [x] `continue` command resumes from persisted run state

#### Files

- `src/orchestrator/dispatcher.py` - modify - add run loop and bounce tracking
- `src/orchestrator/state.py` - modify - add handoff readme generation

#### Tests

- [x] Run loop processes a single task through plan → code → audit → completed
- [x] Bounce counter increments on audit failure
- [x] Third audit cycle triggers handoff stop
- [x] Transport retry exhaustion triggers handoff stop
- [x] Continue resumes from the correct task and stage
- [x] Handoff readme contains task context and failure reason

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.6: Auto-commit after audit pass

#### Goal

Implement surgical git commits after successful audit passes.

#### Definition of Done

- [x] On audit acceptance, commit immediately
- [x] Only stage files listed in the task's Audit section + task file + architecture.md if changed
- [x] Never use `git add .` or `git add -A`
- [x] Commit message format: `feat(task-id): description\n\nAudited: rating/10 by MODEL\nFiles: N files changed\nBounces: N`
- [x] Skip commit if no files to stage (log warning)
- [x] Branch creation after phase/milestone completion (configurable)

#### Files

- `src/orchestrator/commits.py` - create - git commit logic

#### Tests

- [x] Commit stages only the specified files
- [x] Commit message follows the defined format
- [x] No commit when file list is empty (warning logged)
- [x] `git add .` and `git add -A` never appear in the code
- [x] Branch created when configured for milestone

#### Context

Phase 2: Single-Task Execution Engine

---

## Refined Prompt

Objective: Build a complete single-task execution engine that processes Kanban2Code tasks through plan → code → audit → completed using provider CLIs in tmux sessions.

Implementation approach:
1. **Provider abstraction (2.1)**: Create `BaseProvider` ABC with `invoke()` method returning `InvocationResult`. Implement `CodexProvider` that loads config from `.kanban2code/_providers/*.md` frontmatter, validates binary on PATH, builds CLI command, and executes via subprocess.
2. **Prompt assembler (2.2)**: Build `assemble_prompt()` that reads role file, ai-guide.md, task file, and context files from task frontmatter — injecting actual contents verbatim. Include run metadata header with run ID, repo root, task path, stage, and expected transition.
3. **tmux session manager (2.3)**: Use `libtmux` to create named sessions (`orch-{run_id}-{task_id}-{stage}`), run provider commands, poll for process exit and task file mutation, enforce wall/idle timeouts with SIGTERM→SIGKILL escalation.
4. **Stage dispatcher and evaluator (2.4)**: Build `Dispatcher` class that orchestrates a single stage: take before snapshot, assemble prompt, select provider from config, spawn session, wait, take after snapshot, evaluate transition. Build `Evaluator` that compares snapshots to determine result kind (success, quality_failure, transport_failure, blocked).
5. **Run loop and bounce tracking (2.5)**: Implement `RunLoop` class that processes ordered queue, tracks audit bounces per task in `TaskRunState`, enforces max 2 bounces before handoff, retries transport failures up to 3 times, persists state after each stage, and supports `continue` from saved state.
6. **Auto-commit (2.6)**: Build `commit_after_audit()` that parses Audit section for file list, stages only those files plus task file plus architecture.md if changed, formats commit message per spec, and optionally creates milestone branches.

Key decisions:
- **libtmux over raw subprocess**: Use `libtmux` library for session management — provides Pythonic API for creating, monitoring, and killing tmux sessions with proper cleanup.
- **Snapshot-based evaluation**: Compare `TaskSnapshot` before/after to detect stage transitions — avoids parsing provider output and relies on the authoritative frontmatter.
- **Config-driven provider selection**: Provider aliases in `config.json` map to `.kanban2code/_providers/*.md` files — allows per-stage provider config without code changes.
- **Separate InvocationResult from StageResult**: `InvocationResult` captures CLI execution (exit code, timeout, output), `StageResult` captures semantic outcome (success, quality_failure, transport_failure, blocked).

Edge cases:
- Provider binary missing on PATH: raise clear error before attempting invocation.
- Context file missing: raise `PromptAssemblyError` with file path — never silently omit.
- Session hangs: enforce wall timeout with SIGTERM→SIGKILL escalation after 5-second grace period.
- Task file not mutated after provider exits: treat as transport failure, retry.
- Audit rating missing or unparsable: default to 0 (triggers rework).
- Git repository dirty: warn but proceed with commit (do not block).
- Run state file corrupted: start fresh run, log warning.

---

## Context

### File Tree (scoped)

```
src/orchestrator/
├── __init__.py                    # ← read-only reference (exports)
├── cli.py                         # ← modify (wire run/continue commands)
├── config.py                      # ← read-only reference
├── logger.py                      # ← read-only reference
├── models.py                      # ← modify (add InvocationResult, StageResult, ProviderConfig)
├── scanner.py                     # ← read-only reference
├── state.py                       # ← modify (add handoff readme generation)
├── prompts.py                     # ← create
├── sessions.py                    # ← create
├── dispatcher.py                  # ← create
├── evaluator.py                   # ← create
├── commits.py                     # ← create
└── providers/
    ├── __init__.py                # ← create
    ├── base.py                    # ← create
    └── codex.py                   # ← create

.kanban2code/
├── _providers/
│   ├── codex.md                   # ← read-only reference (provider config format)
│   ├── codex-high.md              # ← read-only reference
│   └── codex-low.md               # ← read-only reference
├── _context/
│   └── ai-guide.md                # ← read-only reference (prompt assembly context)
└── projects/orchestration/
    └── phase1-core-infrastructure/
        └── task1.md               # ← read-only reference (sibling phase context)

tests/
├── test_config.py                 # ← read-only reference (test patterns)
├── test_prompts.py                # ← create
├── test_sessions.py               # ← create
├── test_providers.py              # ← create
├── test_dispatcher.py             # ← create
├── test_evaluator.py              # ← create
└── test_commits.py                # ← create
```

### Architecture Excerpts

From `orchestrator.md` (project root):
- **Task frontmatter is source of truth**: Orchestrator reads but never writes frontmatter; agents update their own task state.
- **MVP execution scope**: plan → code → audit only.
- **Max 2 audit bounces**: Third cycle stops and escalates to Dan.
- **No silent waiting**: Every blocked/stalled state must be logged and notified.
- **Safe concurrency only**: Tasks touching same files must not run in parallel (Phase 4).
- **Auto-commit after audit pass**: Only stage files from Audit section + task file + architecture.md.

From `config.json`:
- `providers.{planner,coder,auditor}` map to provider aliases (e.g., `codex`, `codex-high`).
- `stage_routing.{plan,code,audit}` defines success transitions and required sections.
- `timeouts.{plan,code,audit}` defines wall_seconds and idle_seconds per stage.
- `retry_policy.transport_max_attempts = 3`, `audit_failure_cycles_before_handoff = 2`.

From `.kanban2code/_providers/codex.md`:
```yaml
cli: codex
subcommand: exec
model: gpt-5.3-codex
unattended_flags: ['--yolo']
output_flags: ['--json']
prompt_style: stdin
config_overrides:
  model_reasoning_effort: medium
```

### Skill Excerpts

From `skills/python-core-skills`:
- Use `snake_case` for modules, functions, variables (`invoke_provider`, `build_command`).
- Use `PascalCase` for classes (`BaseProvider`, `CodexProvider`, `InvocationResult`).
- All public functions must have type hints and Google-style docstrings.
- Use `from __future__ import annotations` in all modules.
- Avoid mutable default arguments — use `None` defaults.
- Private members use `_leading_underscore`.
- Specific exception handling — no bare `except:`.

### Code Excerpts

**models.py:TaskSnapshot** (lines 97-124) — Core dataclass for task state, used by evaluator for before/after comparison:
```python
@dataclass(slots=True)
class TaskSnapshot:
    path: Path = field(default_factory=lambda: Path("."))
    task_id: str = ""
    project: str = ""
    stage: str = ""
    agent: str = ""
    bounces: int = 0
    tags: list[str] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)
    # ... __post_init__ normalizes stage/agent to lowercase
```

**models.py:TaskRunState** (lines 136-144) — Tracks per-task execution state including audit_failures counter:
```python
@dataclass(slots=True)
class TaskRunState:
    status: str = "pending"
    last_stage: str | None = None
    last_error: str | None = None
    audit_failures: int = 0
    transport_attempts: dict[str, int] = field(default_factory=dict)
```

**config.py:load_config** (lines 24-53) — Pattern for loading typed config from JSON, use similar pattern for provider config:
```python
def load_config(path: str | Path = "config.json") -> OrchestratorConfig:
    config_path = Path(path)
    raw_text = config_path.read_text(encoding="utf-8")
    raw_config = json.loads(raw_text)
    return OrchestratorConfig(...)
```

**scanner.py:split_frontmatter** (lines 20-42) — Reuse for parsing provider .md files:
```python
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\r?\n(?P<metadata>.*?)(?:\r?\n)---\s*", re.DOTALL)
def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    # Returns parsed metadata dict and body string
```

**state.py:save_run_state / load_run_state** (lines 44-82) — Pattern for persisting run state to JSON:
```python
def save_run_state(path: Path, run_state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(run_state), indent=2) + "\n")
```

**logger.py:JsonlLogger.append** (lines 22-42) — Pattern for structured logging:
```python
def append(self, event_type: str, message: str, **extras: object) -> RunEvent:
    event = RunEvent(timestamp=_utc_now_iso(), type=event_type, message=message, extras=dict(extras))
    # Write to JSONL file
```

### Dependency Graph

```
providers/base.py
    └── (no internal deps)

providers/codex.py
    ├── providers/base.py
    ├── models.py (InvocationResult, ProviderConfig)
    └── scanner.py (split_frontmatter for provider .md parsing)

prompts.py
    ├── models.py (TaskSnapshot)
    └── config.py (OrchestratorConfig for context paths)

sessions.py
    ├── libtmux (external)
    └── models.py (SessionConfig, SessionResult)

evaluator.py
    ├── models.py (TaskSnapshot, StageResult)
    └── config.py (stage_routing config)

dispatcher.py
    ├── providers/base.py
    ├── prompts.py
    ├── sessions.py
    ├── evaluator.py
    ├── models.py (RunState, TaskRunState)
    ├── state.py (save_run_state, append_recent_event)
    └── logger.py (JsonlLogger)

commits.py
    └── (subprocess for git commands)

cli.py (modify)
    ├── dispatcher.py
    └── state.py (load_run_state for continue command)
```

### Patterns to Follow

- **Dataclass models**: All new models use `@dataclass(slots=True)` with `from __future__ import annotations`.
- **Config loading**: Use `Path.read_text()` + `json.loads()` + manual validation (no Pydantic).
- **Error handling**: Define custom exceptions (`ProviderError`, `PromptAssemblyError`, `SessionError`) inheriting from `Exception`.
- **Logging**: Use `JsonlLogger` for structured events, log stage transitions and errors.
- **Tests**: Use `pytest` with `tmp_path` fixture for file operations, mock external dependencies.

### Test Patterns

From `tests/test_config.py`:
- Use `tmp_path` fixture for temporary config files.
- Test happy path, missing keys, invalid types, and integration with shipped config.
- Use `pytest.raises(ConfigError, match=r"pattern")` for error assertions.

From `tests/test_scanner.py`:
- Create sample task files in temp directory structure.
- Test discovery, exclusion, parsing, and edge cases.

### Gotchas

- **libtmux Server attachment**: `libtmux.Server()` creates/attaches to tmux server — ensure cleanup in tests with `server.kill_server()`.
- **Codex CLI `--json` flag**: Changes output format; may need to parse JSON for structured results.
- **Frontmatter normalization**: `TaskSnapshot.__post_init__` lowercases stage/agent — evaluator must compare normalized values.
- **Session naming**: Must be unique per invocation; include run_id, task_id, stage, and timestamp or counter.
- **Git operations**: Run from repo root (`Path.cwd()` or detect via `git rev-parse --show-toplevel`).
- **Timeout handling**: libtmux `session.attached_window.attached_pane` for process monitoring; wall timeout vs idle timeout are different.

### Scope Boundaries

This task (Phase 2) should NOT touch:
- **Account rotation** (Phase 3): `accounts.py`, account switching logic.
- **Additional providers** (Phase 3): Claude, Gemini, Qwen providers.
- **Model routing/fallback** (Phase 3): Fallback chain logic in dispatcher.
- **Concurrent scheduling** (Phase 4): `scheduler.py`, multi-threaded dispatch.
- **Conflict detection** (Phase 4): File-level conflict analysis.
- **Telegram notifications** (Phase 5): `notifier.py`.
- **Smoke tests** (Phase 5): `smoke.py`.
- **Memory system** (Phase 6): `memory.py`.

Phase 1 (task1.md) is complete — scaffold, config, scanner, logger, state are available for use.

## Audit
src/orchestrator/__init__.py
src/orchestrator/cli.py
src/orchestrator/commits.py
src/orchestrator/dispatcher.py
src/orchestrator/evaluator.py
src/orchestrator/models.py
src/orchestrator/prompts.py
src/orchestrator/sessions.py
src/orchestrator/state.py
src/orchestrator/providers/__init__.py
src/orchestrator/providers/base.py
src/orchestrator/providers/codex.py
tests/conftest.py
tests/test_cli.py
tests/test_commits.py
tests/test_dispatcher.py
tests/test_evaluator.py
tests/test_models.py
tests/test_prompts.py
tests/test_providers.py
tests/test_sessions.py
tests/test_state.py

---

## Review

**Rating: 9/10**

**Verdict: ACCEPTED**

### Summary

A comprehensive, well-structured single-task execution engine that correctly implements all six subtasks: provider abstraction, prompt assembly, session management, stage dispatch/evaluation, run loop with bounce tracking, and auto-commit. The code follows established project patterns, maintains clean separation of concerns, and has thorough test coverage. All 49 tests pass.

### Findings

#### Blockers

(None)

#### High Priority

(None)

#### Medium Priority

- [ ] Session manager is process-based, not tmux-based: The task spec calls for tmux sessions (`libtmux`), but `sessions.py` uses `subprocess.Popen` with stdin piping instead. The class is named `TmuxSessionManager` but contains no tmux code. This works for the MVP and is arguably simpler, but it diverges from the spec's stated intent of "visible, monitorable sessions." Future phases expecting actual tmux sessions (e.g., for operators to attach and watch) will need a rework. - `src/orchestrator/sessions.py:17`
- [ ] `_parse_audit_paths` resolves paths relative to task_dir, not repo_root: Audit section paths like `src/orchestrator/sessions.py` are resolved relative to the task file's parent directory. This works because the test writes relative paths from the task dir (e.g., `../../../src/file.py`), but real audit sections (as seen in this task file) use repo-root-relative paths like `src/orchestrator/sessions.py`. The production commit flow may fail to find files. - `src/orchestrator/commits.py:115-129`

#### Low Priority / Nits

- [ ] `build_command()` called three times in `invoke()` on binary-missing path: When the binary is not found, `build_command()` is called once for the error result, then would not reach the second call. But in the `SessionError` except branch, `build_command()` is called again redundantly. Minor perf concern. - `src/orchestrator/providers/codex.py:100-126`
- [ ] Type annotation `callable` should be `Callable` (or `collections.abc.Callable`): `monotonic: callable | None = None` uses the lowercase builtin `callable` which is a function, not a type annotation. Works at runtime due to `from __future__ import annotations` deferring evaluation, but is technically incorrect for static analysis. - `src/orchestrator/sessions.py:26-27`
- [ ] `_add_stub_command` `handler` parameter lacks type annotation: The `handler` parameter on line 88 of `cli.py` has no type hint. - `src/orchestrator/cli.py:88`
- [ ] `dispatcher.py` hardcodes `CodexProvider` — no dynamic provider dispatch: `_build_provider` only supports `codex*` aliases. This is fine for Phase 2 scope but the method name suggests generality that doesn't exist yet. - `src/orchestrator/dispatcher.py:164-171`
- [ ] `conftest.py` sys.path mutation: `tests/conftest.py` inserts `src/` into `sys.path` at import time. This works but would be cleaner with a `pyproject.toml` `[tool.pytest.ini_options] pythonpath` setting. - `tests/conftest.py:9-10`

### Test Assessment

- Coverage: Adequate — all major code paths are tested including happy paths, error conditions, bounce limits, transport retries, resume, and edge cases.
- Missing tests:
  - No test for `_parse_audit_paths` with repo-root-relative paths (the current test uses task-dir-relative `../../../src/file.py`).
  - No test for `resolve_context_path` with an absolute path.
  - No test for `extract_audit_rating` with the `AUDIT_RATING:` pattern.
  - No negative test for `_build_provider` with an unsupported alias.
  - Session manager tests don't verify `_terminate_process` escalation from SIGTERM to SIGKILL.

### What's Good

- Clean dataclass models with `slots=True` throughout, immutable-by-default design.
- Snapshot-based evaluation is elegant — comparing before/after `TaskSnapshot` avoids fragile output parsing.
- `InvocationResult` / `StageResult` separation cleanly divides transport concerns from semantic concerns.
- Provider config loaded from markdown frontmatter reuses `split_frontmatter` from scanner — no duplication.
- Handoff readme generation gives operators clear, actionable context.
- Commit logic is properly surgical — deduplicates files, checks git status per-file, never uses `git add .`.
- Run state persistence after every stage enables robust resume.
- Tests use `monkeypatch` and `tmp_path` effectively, no real tmux or git operations leak into unit tests (commits tests use isolated repos).

### Recommendations

- Consider renaming `TmuxSessionManager` to `SessionManager` or `ProcessSessionManager` to accurately reflect its subprocess-based implementation, and add actual tmux support later.
- Add a `repo_root` parameter to `_parse_audit_paths` so it can resolve paths relative to the repository root, matching how audit sections are written in practice.
- Extract `_utc_now_iso()` (duplicated in `dispatcher.py` and `logger.py`) into a shared utility.
