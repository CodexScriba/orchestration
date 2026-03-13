---
stage: completed
agent: 05-⚙️coder
bounces: 0
tags:
  - orchestration
  - roadmap
  - supervisor
contexts:
  - .kanban2code/how-it-works.md
  - .kanban2code/architecture.md
updated: 2026-03-13T00:00:00.000Z
skills: []
---

# Roadmap — Orchestration project

## Goal
Design a brand new orchestrator for Kanban2Code-first workflows.

## Working decisions
- Kanban2Code-first, not generic-first.
- Kanban2Code task frontmatter remains the source of truth.
- Kanban2Code should mutate its own task state.
- The orchestrator acts as a supervisor, not the owner of task truth.
- Supplemental orchestrator state (DB/JSON) is allowed for queue/run metadata only.
- The new project lives separately at `/home/cynicus/code/orchestration`.

## Open questions
- Should the supervisor run one task at a time serially or support parallel runs from day one?
- What should be the first runnable MVP loop?
- What exact metadata belongs in orchestrator-only state?
- How should notifications/reporting be emitted?

## Notes
Use this file to capture decisions as we make them so conversation context loss does not reset the design.

## New decisions
- Add an orchestrator memory system with hot, warm, and cold layers.
- Orchestrator memory should hold operational/project context so Kadee can stay lighter and link into it when needed.
- The orchestrator should be a smart but bounded supervisor.
- It may detect blockers, choose among eligible tasks, and keep unrelated work moving concurrently.
- It must not skip stages, rewrite task truth loosely, or bypass guardrails.
- Communication is a first-class requirement: Dan wants to stay on top of development in real time.
- Python should communicate through state files and/or OpenClaw session messages, with Kadee acting as the human-facing supervisor.
- Tunnel-based oversight enables a kill switch if something starts going south.

## Additional decisions
- The orchestrator should maintain a programmatic state view of Kanban2Code tasks by project and stage (inbox, plan, code, audit, completed).
- This state view should be easy for Kadee to read so she can understand board status quickly without re-reading every task file.
- The orchestrator should own queueing/eligibility/concurrency decisions within guardrails.
- The orchestrator should log what is being run, including provider/model/account used per run.
- Account switching should be part of the MVP.
- Account usage/status lookup should be part of the MVP if it is easy to query.
- Logs/state should be readable enough that Kadee can translate them into real-time updates for Dan.

- Agent runs should use tmux-managed visible sessions rather than hidden subprocess-only execution.
- The orchestrator should support multiple concurrent tasks from day one, with guardrails.
- Tasks marked as blocking or governed by rules that require waiting (for example UI-dependent tasks) should not be auto-run concurrently.
- Concurrency should be decided dynamically rather than by a fixed low cap.
- Dynamic concurrency decisions should still respect explicit guardrails and task eligibility rules.
- The orchestrator may pause or deprioritize a task when it detects the task is waiting on Dan.
- When this happens, it should notify Dan on Telegram and continue with other eligible work.
- MVP notification policy: notify Dan on every stage change.
- Notification verbosity can be reduced later if it becomes noisy.
- Stage-change notifications should include the account and model/provider used for that run.
- Max audit bounces = 2, then stop and notify Dan.
- No silent waiting: blocked/waiting/stalled states must be logged and notified.
- No hidden stage jumps unless an explicit rule allows it.
- Safe concurrency only: do not run tasks together if they touch the same files or area.
- Commit rules are explicit: after each audit pass, auto-commit.
- After each phase or major project milestone, create a new branch for safety.
- Everything should be logged: stage, account, model, start, finish, error, and reason.
- Auto-commit is enabled after audit pass.
- The orchestrator DB/state must not override Kanban2Code task truth, especially in MVP.
- Blocked states include: waiting on human, expected outcome did not happen, or auth/provider issues after fallback attempts.
- If a stage runs and the expected outcome does not happen (example: planner runs but does not update the task), mark it clearly rather than pretending progress.
- On auth/provider issues, try fallback or a different account first, then notify Dan if still blocked.
- MVP execution scope is only: plan -> code -> audit.
- Architecture remains human-led; the orchestrator itself should not own architecture decisions.
- Kadee may be involved in architecture or splitter work directly, but that is separate from the orchestrator runtime.
- Projects are entered explicitly by Kadee from Dan-provided name and location; the orchestrator should not auto-scan arbitrary projects by default.
- Conflict detection/concurrency safety will be decided by the orchestrator within guardrails.
- Planning model preference: Google Flash 3.0/3.1; avoid 2.5. Fallbacks may include Qwen Kimi 2.5, MiniMax, other Qwen models, or Haiku.
- Coding model preference: Codex 5.4 with medium reasoning; fallbacks include Sonnet 4.6 or GLM via Qwen CLI.
- Stage success should be validated by task metadata/frontmatter changes; agents must update task state clearly when done.
- Notification format can be decided by Kadee/orchestrator design during implementation.
- Add a smoke test as part of the orchestrator.
- The smoke test should call Qwen, Gemini, Claude, and Codex once each during development.
- Minimal expected response can be something simple like saying hi back, just to verify wiring/auth/runtime health.

## Kadee role in the system
- Kadee is the smart supervisory layer, not the primary executor.
- Kadee reads orchestrator state, logs, and Kanban2Code task truth to understand what is happening.
- Kadee helps decide queueing, blocker handling, escalation, and communication within guardrails.
- Kadee does not own task truth and should not casually override Kanban2Code state.
- Kadee communicates progress, blockers, stage changes, account/model usage, and critical events to Dan.
- Kadee can inspect live runs through tunnel access and tmux-managed sessions, and act as a kill switch if a run is going south.
- Kadee may participate directly in architecture/splitter discussions, but that is separate from the orchestrator runtime itself.

---

## Technical Architecture

### Overview

The orchestrator is a Python process that acts as a deterministic supervisor for Kanban2Code task execution. It reads task files as the source of truth, resolves an ordered queue, spawns CLI-based agent runtimes inside tmux sessions, monitors results by inspecting task file mutations, and drives the plan → code → audit loop to completion.

The architecture separates the **execution engine** (queue processing, dispatch, retries, commits, state) from the **policy layer** (model routing, account rules, prompt assembly, notification format). This split ensures deterministic execution with flexible, editable configuration.

Key design principles:
- Task frontmatter is the single source of truth for stage, agent, and bounces.
- The orchestrator never writes task frontmatter directly; agents do that.
- Orchestrator-only state covers queue order, run metadata, session status, account used, and timestamps.
- Concurrency is supported from day one with file-level conflict detection.
- All execution happens in tmux-managed visible sessions for human oversight.
- Every state change is logged structurally and notified to Dan via Telegram.

### Components

- **CLI (`cli.py`)**: Entry point with `run`, `continue`, `status`, `smoke-test` subcommands.
- **Config (`config.py`)**: Loads and validates `config.json` — provider mappings, stage routing, timeouts, retry policy, account pool, notification settings.
- **Models (`models.py`)**: Dataclasses for `TaskSnapshot`, `RunState`, `TaskState`, `StageResult`, `ProviderSpec`, `AccountInfo`.
- **Scanner (`scanner.py`)**: Reads `.kanban2code/` folders, parses YAML frontmatter, builds a typed task list per project and stage.
- **Queue (`queue.py`)**: Resolves eligible tasks from targets, orders by phase/task number, filters by selected stages.
- **Scheduler (`scheduler.py`)**: Makes concurrency decisions — picks eligible tasks, detects file-level conflicts, respects blocking tags, enforces guardrails.
- **Dispatcher (`dispatcher.py`)**: Orchestrates a single stage execution — selects provider, rotates account, assembles prompt, spawns session, waits for completion, evaluates result.
- **Providers (`providers/`)**: Abstract base + concrete implementations for Codex, Claude, Gemini, and Qwen CLIs. Each knows its CLI binary, flags, prompt style, and output parsing.
- **Accounts (`accounts.py`)**: Manages account rotation per task (Codex symlink pattern), health checks via login status, round-robin fallback.
- **Sessions (`sessions.py`)**: Creates/monitors/tears down tmux sessions. Detects completion by polling process exit + task file mutation. Enforces wall/idle timeouts.
- **Prompts (`prompts.py`)**: Assembles full prompts by injecting real file contents — role file, ai-guide.md, task file, context files. Never uses placeholders.
- **Evaluator (`evaluator.py`)**: Validates stage outcomes by comparing before/after task snapshots — checks frontmatter transitions, required sections, review ratings.
- **Commits (`commits.py`)**: Auto-commits after audit pass. Stages only files listed in the Audit section + task file + architecture.md if changed. Uses structured commit messages.
- **Notifier (`notifier.py`)**: Sends Telegram messages on every stage change, blocked/stalled states, and escalations. Includes account and model/provider in each notification.
- **State (`state.py`)**: Persists run state as JSON, appends structured events to JSONL, generates board state view (project × stage matrix) for Kadee.
- **Logger (`logger.py`)**: Structured JSONL logging — stage, account, model, start, finish, error, reason. One-line structured event format for real-time readability.
- **Memory (`memory.py`)**: Three-layer operational memory — hot (current run context), warm (recent project/task context), cold (historical patterns). File-based, readable by Kadee.
- **Smoke (`smoke.py`)**: Calls each configured provider once with a simple prompt to verify wiring, auth, and runtime health.

### Data Flow

```
CLI invocation (run/continue/status)
  │
  ▼
Config loader ──► Validate config.json + provider files
  │
  ▼
Scanner ──► Read .kanban2code/ folders ──► Parse frontmatter ──► TaskSnapshot[]
  │
  ▼
Queue resolver ──► Filter eligible tasks ──► Order by phase/task ──► ordered queue
  │
  ▼
Scheduler ──► Pick next eligible task(s) ──► Check conflicts ──► Dispatch slots
  │
  ▼
For each dispatched task:
  │
  ├── Account manager ──► Rotate to next account ──► Verify login
  ├── Provider router ──► Select provider for stage ──► Load CLI config
  ├── Prompt assembler ──► Inject role + ai-guide + task + contexts
  │
  ▼
Session manager ──► Create tmux session ──► Run CLI command
  │
  ▼
Monitor ──► Poll exit + task file ──► Enforce wall/idle timeouts
  │
  ▼
Evaluator ──► Compare before/after snapshots ──► Determine result kind
  │
  ├── success ──► Log + Notify + (if audit pass: Commit) + Continue loop
  ├── quality_failure ──► Increment bounce ──► Back to code (or escalate at max)
  ├── transport_failure ──► Retry (or escalate at max attempts)
  ├── planner_blocked ──► Stop + Notify Dan
  └── handoff_stop ──► Stop + Notify Dan + Write human readme
```

### Dependencies

- **Python 3.12+**: Runtime (project has 3.14 installed).
- **PyYAML**: Robust YAML frontmatter parsing (replaces fragile custom parser from reference runner).
- **libtmux**: Programmatic tmux session management (create, monitor, kill).
- **python-telegram-bot**: Telegram notification delivery.
- **pathlib / subprocess / threading**: Standard library for file ops, process spawning, concurrency.
- **tmux**: System dependency — must be installed on the host.
- **CLI tools on PATH**: `codex`, `claude`, `gemini` (Google CLI), `qwen` — as configured per provider.

### Constraints

- **No frontmatter writes**: The orchestrator must never directly mutate task frontmatter. Agents update their own task state; the orchestrator reads and validates.
- **No `git add .`**: Commits must be surgical — only files from the Audit section, the task file, and architecture.md if changed.
- **Max 2 audit bounces**: Third audit cycle stops the run and escalates to Dan. No exceptions.
- **No silent waiting**: Every blocked, stalled, or waiting state must be logged and notified.
- **No hidden stage jumps**: Stage transitions must follow the defined routing unless an explicit rule allows it.
- **Safe concurrency only**: Tasks touching the same files or area must not run in parallel.
- **Prompt integrity**: Prompts must contain actual file contents. Weak/summarized prompts cause pipeline breaks.
- **Account rotation per task**: Same account through all bounces of a single task. Rotate on the next task.
- **MVP scope**: plan → code → audit only. Architecture and splitter remain human-led.

---

## Phases

### Phase 1: Core Infrastructure

Set up the project scaffold, configuration system, task scanning, structured logging, and state management. This phase produces no executable pipeline — it builds the foundation every other phase depends on.

#### Task 1.1: Project scaffold and config system

**Definition of Done:**

- [ ] `src/orchestrator/` package exists with `__init__.py`, `cli.py`, `config.py`, `models.py`
- [ ] `config.json` schema defined and loadable with validation errors on bad input
- [ ] Config covers: provider mappings, stage routing, timeouts, retry policy, account pool, notification settings
- [ ] `pyproject.toml` with dependencies (pyyaml, libtmux, python-telegram-bot) and dev dependencies (pytest, ruff)
- [ ] CLI entry point registers `run`, `continue`, `status`, `smoke-test` subcommands (stubs)

**Files:**

- `src/orchestrator/__init__.py` - create - package init
- `src/orchestrator/cli.py` - create - argparse entry point
- `src/orchestrator/config.py` - create - config loading and validation
- `src/orchestrator/models.py` - create - dataclasses for all core types
- `config.json` - create - default orchestrator configuration
- `pyproject.toml` - create - project metadata and dependencies

**Tests:**

- [ ] Config loads valid JSON and returns typed config object
- [ ] Config rejects missing required fields with clear error
- [ ] CLI registers all subcommands without error
- [ ] Models are constructible with expected defaults

**Skills:**

- `skills/python-core-skills` - All code must follow PEP 8, type hints, docstring conventions

#### Task 1.2: Task scanner and frontmatter parser

**Definition of Done:**

- [ ] Scanner reads `.kanban2code/` folders recursively and finds all task `.md` files
- [ ] YAML frontmatter is parsed into `TaskSnapshot` with typed fields (stage, agent, bounces, tags, contexts)
- [ ] Scanner builds a per-project, per-stage index of tasks
- [ ] Tasks in `_archive/`, `_agents/`, `_providers/`, `_context/` are excluded
- [ ] Board state view: JSON object mapping `{project: {stage: [task_id, ...]}}` for Kadee

**Files:**

- `src/orchestrator/scanner.py` - create - task file discovery and frontmatter parsing
- `src/orchestrator/state.py` - create - board state view builder

**Tests:**

- [ ] Scanner finds task files in inbox/, projects/*, and nested phase folders
- [ ] Scanner excludes _archive, _agents, _providers, _context
- [ ] Frontmatter parser extracts stage, agent, bounces, tags, contexts correctly
- [ ] Frontmatter parser handles missing optional fields with defaults
- [ ] Board state view produces correct project × stage matrix from sample tasks

**Skills:**

- `skills/python-core-skills` - Python conventions and type safety

#### Task 1.3: Structured logging and run state persistence

**Definition of Done:**

- [ ] JSONL logger writes one event per line with timestamp, type, message, and arbitrary extras
- [ ] Run state persists as JSON with schema version, run ID, ordered tasks, task states, recent events
- [ ] Events include: run_started, run_resumed, stage_success, stage_transport_failure, audit_rework, run_handoff, run_completed
- [ ] Summary markdown is auto-generated from run state
- [ ] Recent events are capped (configurable, default 20)

**Files:**

- `src/orchestrator/logger.py` - create - structured JSONL logging
- `src/orchestrator/state.py` - modify - add run state persistence and summary generation

**Tests:**

- [ ] Logger appends events as valid JSONL lines
- [ ] Run state round-trips through save/load without data loss
- [ ] Summary markdown is generated from run state with correct formatting
- [ ] Recent events list respects the configured cap

**Skills:**

- `skills/python-core-skills` - Python conventions

### Phase 2: Single-Task Execution Engine

Build the core execution loop: provider abstraction, prompt assembly, tmux sessions, stage dispatch, result evaluation, bounce tracking, auto-commit. End result: one task can go through plan → code → audit → completed using a single Codex provider.

#### Task 2.1: Provider abstraction and Codex CLI provider

**Definition of Done:**

- [ ] `BaseProvider` abstract class defines: `invoke(prompt, task_path, output_dir, timeouts) → InvocationResult`
- [ ] `CodexProvider` implements `BaseProvider` using subprocess + tmux
- [ ] Provider loads CLI config from `.kanban2code/_providers/*.md` frontmatter
- [ ] InvocationResult captures: ok, exit_code, timeout_type, final_message, output_paths, error_message, command
- [ ] Provider validates that the CLI binary exists on PATH before invocation

**Files:**

- `src/orchestrator/providers/__init__.py` - create - provider package init
- `src/orchestrator/providers/base.py` - create - abstract provider interface
- `src/orchestrator/providers/codex.py` - create - Codex CLI implementation

**Tests:**

- [ ] CodexProvider builds correct command line from provider config
- [ ] CodexProvider detects missing binary gracefully
- [ ] InvocationResult correctly reports success/failure/timeout
- [ ] Provider loads config from a sample .md frontmatter file

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 2.2: Prompt assembler

**Definition of Done:**

- [ ] Assembles full prompt from: role file, ai-guide.md, task file, context files
- [ ] Injects actual file contents — never placeholders or summaries
- [ ] Includes run metadata: run ID, repo root, task path, current stage, expected transition
- [ ] Context files resolved from task frontmatter `contexts:` field
- [ ] Handles missing context files with a clear error rather than silent omission

**Files:**

- `src/orchestrator/prompts.py` - create - prompt assembly logic

**Tests:**

- [ ] Prompt includes role file content verbatim
- [ ] Prompt includes ai-guide.md content
- [ ] Prompt includes task file content
- [ ] Prompt includes context file contents from task frontmatter
- [ ] Missing context file raises a clear error
- [ ] Prompt includes expected transition text for each stage

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 2.3: tmux session manager

**Definition of Done:**

- [ ] Creates named tmux sessions for each stage invocation (e.g., `orch-run123-task1.1-plan`)
- [ ] Runs provider CLI command inside the tmux session
- [ ] Monitors session: polls for process exit and task file mutation
- [ ] Enforces wall timeout and idle timeout (configurable per stage)
- [ ] Kills session cleanly on timeout (SIGTERM then SIGKILL)
- [ ] Returns session output path for debugging

**Files:**

- `src/orchestrator/sessions.py` - create - tmux session lifecycle management

**Tests:**

- [ ] Session creates with correct name format
- [ ] Session detects process exit
- [ ] Wall timeout triggers session kill
- [ ] Idle timeout triggers session kill
- [ ] Session cleanup removes finished sessions

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 2.4: Stage dispatcher and result evaluator

**Definition of Done:**

- [ ] Dispatcher takes a task path, selects provider, assembles prompt, spawns session, waits, evaluates
- [ ] Evaluator compares before/after TaskSnapshots to determine result kind
- [ ] Plan result: success if stage moved to code + required sections present; blocked if questions added
- [ ] Code result: success if stage moved to audit + Audit section present + file changed
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating < 8 + back to code
- [ ] Transport failure if expected transition did not happen
- [ ] All results include provider key, alias, model, exit code, output paths

**Files:**

- `src/orchestrator/dispatcher.py` - create - stage execution orchestration
- `src/orchestrator/evaluator.py` - create - before/after snapshot comparison

**Tests:**

- [ ] Plan success detected when frontmatter changes to stage: code, agent: coder
- [ ] Plan blocked detected when Questions section added
- [ ] Code success detected when frontmatter changes to stage: audit, agent: auditor
- [ ] Audit acceptance detected when rating ≥ 8 and stage: completed
- [ ] Audit rework detected when rating < 8 and stage: code
- [ ] Transport failure detected when no expected transition occurs

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 2.5: Bounce tracker and run loop

**Definition of Done:**

- [ ] Run loop processes ordered queue: for each task, execute stages until completed or blocked
- [ ] Bounce tracker counts audit failures per task (stored in task state)
- [ ] Max 2 audit bounces: third cycle triggers handoff stop
- [ ] Transport retry: up to 3 attempts per stage before escalation
- [ ] Handoff writes human-readable readme with context for Dan
- [ ] Run state updated after every stage with current index, task, stage
- [ ] `continue` command resumes from persisted run state

**Files:**

- `src/orchestrator/dispatcher.py` - modify - add run loop and bounce tracking
- `src/orchestrator/state.py` - modify - add handoff readme generation

**Tests:**

- [ ] Run loop processes a single task through plan → code → audit → completed
- [ ] Bounce counter increments on audit failure
- [ ] Third audit cycle triggers handoff stop
- [ ] Transport retry exhaustion triggers handoff stop
- [ ] Continue resumes from the correct task and stage
- [ ] Handoff readme contains task context and failure reason

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 2.6: Auto-commit after audit pass

**Definition of Done:**

- [ ] On audit acceptance, commit immediately
- [ ] Only stage files listed in the task's Audit section + task file + architecture.md if changed
- [ ] Never use `git add .` or `git add -A`
- [ ] Commit message format: `feat(task-id): description\n\nAudited: rating/10 by MODEL\nFiles: N files changed\nBounces: N`
- [ ] Skip commit if no files to stage (log warning)
- [ ] Branch creation after phase/milestone completion (configurable)

**Files:**

- `src/orchestrator/commits.py` - create - git commit logic

**Tests:**

- [ ] Commit stages only the specified files
- [ ] Commit message follows the defined format
- [ ] No commit when file list is empty (warning logged)
- [ ] `git add .` and `git add -A` never appear in the code
- [ ] Branch created when configured for milestone

**Skills:**

- `skills/python-core-skills` - Python conventions

### Phase 3: Account Rotation and Multi-Provider

Add account management for Codex and additional CLI providers for Claude, Gemini, and Qwen. Add model routing configuration with fallback chains.

#### Task 3.1: Account manager with Codex rotation

**Definition of Done:**

- [ ] Account pool loaded from config (list of account names)
- [ ] Rotation: pick next account per task, keep same through bounces
- [ ] Switch mechanism: symlink `~/.codex/auth.json` to `~/.codex/accounts/TARGET.json`
- [ ] Health check: run `codex login status` after switch, parse result
- [ ] Round-robin fallback: if account fails, try next; if all fail, escalate
- [ ] Log which account is active for each task

**Files:**

- `src/orchestrator/accounts.py` - create - account rotation and health checking

**Tests:**

- [ ] Account rotation picks the next account in pool order
- [ ] Same account persists through bounces of a task
- [ ] Failed account triggers fallback to next
- [ ] All accounts failing triggers escalation
- [ ] Health check parses codex login status output

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 3.2: Claude CLI provider

**Definition of Done:**

- [ ] `ClaudeProvider` implements `BaseProvider`
- [ ] Loads config from `.kanban2code/_providers/opus.md`, `sonnet.md`, `haiku.md`
- [ ] Builds correct `claude` CLI command with model, flags, and prompt
- [ ] Supports stdin prompt delivery
- [ ] Captures output for evaluation

**Files:**

- `src/orchestrator/providers/claude.py` - create - Claude CLI implementation

**Tests:**

- [ ] ClaudeProvider builds correct command for opus/sonnet/haiku
- [ ] ClaudeProvider handles stdin prompt delivery
- [ ] Missing claude binary detected gracefully

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 3.3: Gemini and Qwen CLI providers

**Definition of Done:**

- [ ] `GeminiProvider` implements `BaseProvider` for Google Gemini CLI
- [ ] `QwenProvider` implements `BaseProvider` for Qwen CLI
- [ ] Each loads config from its respective `_providers/*.md` file
- [ ] Qwen supports model aliases (kimi-k2.5, minimax, etc.)
- [ ] Gemini supports model name format (`gemini-3-flash-preview`)

**Files:**

- `src/orchestrator/providers/gemini.py` - create - Gemini CLI implementation
- `src/orchestrator/providers/qwen.py` - create - Qwen CLI implementation

**Tests:**

- [ ] GeminiProvider builds correct command with model name
- [ ] QwenProvider builds correct command with model alias
- [ ] Both detect missing binary gracefully

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 3.4: Model routing with fallback chains

**Definition of Done:**

- [ ] Config defines provider preference per stage with ordered fallback list
- [ ] Planning: Gemini Flash 3.x → Qwen Kimi 2.5 → Haiku
- [ ] Coding: Codex 5.4 medium → Sonnet 4.6 → GLM via Qwen
- [ ] Auditing: Opus → Codex 5.4 high reasoning
- [ ] On provider failure, automatically try next in fallback chain
- [ ] Log which provider/model was actually used

**Files:**

- `src/orchestrator/dispatcher.py` - modify - add fallback chain logic
- `config.json` - modify - add fallback chain configuration

**Tests:**

- [ ] Primary provider selected for each stage
- [ ] Fallback triggered on provider failure
- [ ] All fallbacks exhausted triggers escalation
- [ ] Correct provider/model logged for each invocation

**Skills:**

- `skills/python-core-skills` - Python conventions

### Phase 4: Concurrency and Safety

Enable multiple concurrent task execution with file-level conflict detection and dynamic concurrency decisions.

#### Task 4.1: Concurrent task scheduler

**Definition of Done:**

- [ ] Scheduler picks multiple eligible tasks up to a dynamic concurrency limit
- [ ] Each task dispatched in its own thread with its own tmux session
- [ ] Concurrency limit decided dynamically based on available tasks and conflict analysis
- [ ] Tasks with `blocking` tag or explicit dependency are never auto-parallelized
- [ ] Thread-safe run state updates (lock or queue-based)

**Files:**

- `src/orchestrator/scheduler.py` - create - concurrent task scheduling
- `src/orchestrator/dispatcher.py` - modify - support concurrent dispatch

**Tests:**

- [ ] Two non-conflicting tasks run concurrently
- [ ] Blocking-tagged task runs alone
- [ ] Thread-safe state updates do not corrupt run state
- [ ] Dynamic concurrency adjusts when tasks finish

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 4.2: File-level conflict detection

**Definition of Done:**

- [ ] Before dispatching, check which files each task will touch (from task body/context)
- [ ] Two tasks with overlapping file sets must not run concurrently
- [ ] Conflict detected at dispatch time, not after launch
- [ ] Conflict resolution: delay the later task until the earlier one completes
- [ ] Log conflict decisions

**Files:**

- `src/orchestrator/scheduler.py` - modify - add file-level conflict detection

**Tests:**

- [ ] Tasks touching different files are allowed concurrently
- [ ] Tasks touching the same file are serialized
- [ ] Conflict detection reads file lists from task body
- [ ] Delayed task is dispatched after conflicting task completes

**Skills:**

- `skills/python-core-skills` - Python conventions

### Phase 5: Communication and Monitoring

Add Telegram notifications, board state view for Kadee, and provider health smoke tests.

#### Task 5.1: Telegram notifier

**Definition of Done:**

- [ ] Sends Telegram message on every stage change
- [ ] Includes: task ID, stage transition, account used, model/provider used
- [ ] Sends on blocked/stalled/escalated states with reason
- [ ] Bot token and chat ID loaded from config (not hardcoded)
- [ ] Graceful failure: notification errors do not block execution

**Files:**

- `src/orchestrator/notifier.py` - create - Telegram notification delivery

**Tests:**

- [ ] Notification sent on stage change (mocked Telegram API)
- [ ] Notification includes required fields
- [ ] Notification failure does not raise or block the run
- [ ] Bot token and chat ID loaded from config

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 5.2: Board state view for Kadee

**Definition of Done:**

- [ ] Produces a JSON state file mapping `{project: {stage: [{task_id, title, agent, bounces, last_updated}]}}`
- [ ] Updated after every stage transition
- [ ] Also produces a human-readable markdown summary
- [ ] Kadee can read this file to understand board status without scanning every task

**Files:**

- `src/orchestrator/state.py` - modify - add board state view generation and markdown summary

**Tests:**

- [ ] Board state JSON matches expected structure from sample tasks
- [ ] Board state updates after stage transition
- [ ] Markdown summary is readable and correctly formatted

**Skills:**

- `skills/python-core-skills` - Python conventions

#### Task 5.3: Smoke test suite

**Definition of Done:**

- [ ] `smoke-test` CLI subcommand calls each configured provider once
- [ ] Sends a trivial prompt (e.g., "Say exactly: hello") and checks for a response
- [ ] Reports pass/fail per provider with error details
- [ ] Tests: Codex, Claude, Gemini, Qwen (as configured)
- [ ] Can be run independently before starting real task execution

**Files:**

- `src/orchestrator/smoke.py` - create - provider health verification

**Tests:**

- [ ] Smoke test runs all configured providers
- [ ] Pass/fail reported per provider
- [ ] Missing provider binary reported as failure, not crash
- [ ] Auth failure reported clearly

**Skills:**

- `skills/python-core-skills` - Python conventions

### Phase 6: Memory System

Add the three-layer operational memory system for retaining context across runs.

#### Task 6.1: Memory system with hot, warm, and cold layers

**Definition of Done:**

- [ ] Hot layer: current run context (active tasks, in-flight sessions, recent events) — in-memory + state file
- [ ] Warm layer: recent project context (last N completed tasks per project, recent decisions, recent errors) — file-based
- [ ] Cold layer: historical patterns (aggregated stats, common failure modes, model performance) — file-based
- [ ] Memory read API: Kadee can query memory by layer and topic
- [ ] Memory write API: orchestrator appends to warm/cold after run completion
- [ ] Memory is file-based and human-readable (JSON + markdown)

**Files:**

- `src/orchestrator/memory.py` - create - three-layer memory system

**Tests:**

- [ ] Hot memory reflects current run state
- [ ] Warm memory stores last N completed tasks per project
- [ ] Cold memory aggregates stats from completed runs
- [ ] Memory read returns correct data by layer and topic
- [ ] Memory files are valid JSON/markdown

**Skills:**

- `skills/python-core-skills` - Python conventions

---

## Context

### Relevant Patterns

- **Reference runner**: `/home/cynicus/Downloads/orchestrator/orchestrator/runner.py` (~1200 lines) contains a working serial execution engine. Key patterns to preserve: `TaskSnapshot` dataclass, `StageResult` with `kind` discriminator, frontmatter before/after comparison for result evaluation, structured event logging. Key patterns to improve: replace custom YAML parser with PyYAML, replace raw subprocess with tmux sessions, add concurrency.
- **Provider config format**: `.kanban2code/_providers/*.md` files use YAML frontmatter with `cli`, `model`, `subcommand`, `prompt_style`, `output_flags`, `config_overrides`. The orchestrator should load these directly rather than duplicating config.
- **Agent file loading**: Reference runner finds agent files by scanning `_agents/*.md` frontmatter for a `name` field match. Preserve this pattern.
- **Stage routing config**: Reference runner uses `config.json` with `stage_routing` mapping each stage to its agent, success transition, and required sections. This is a clean pattern to keep.
- **Structured markers**: The ai-guide defines HTML comment markers (`<!-- STAGE_TRANSITION: ... -->`, `<!-- AUDIT_RATING: ... -->`) for automated mode. The orchestrator should support both direct frontmatter edits (manual mode) and marker-based detection.
- **Codex account switching**: Symlink pattern `ln -sf ~/.codex/accounts/TARGET.json ~/.codex/auth.json` with verification via `codex login status`.

### Related Files

- `orchestrator.md` - Complete architectural notes and operational lessons; primary design reference
- `.kanban2code/_context/ai-guide.md` - Defines stage progression, dual-mode behavior, structured markers
- `.kanban2code/_agents/04-📋planner.md` - Planner behavioral constraints
- `.kanban2code/_agents/05-⚙️coder.md` - Coder behavioral constraints
- `.kanban2code/_agents/06-✅auditor.md` - Auditor behavioral constraints with rating system
- `.kanban2code/_providers/*.md` - All provider CLI configurations
- `/home/cynicus/Downloads/orchestrator/orchestrator/runner.py` - Reference implementation
- `/home/cynicus/Downloads/orchestrator/orchestrator/config.json` - Reference config schema

### Gotchas

- **Custom YAML parser fragility**: The reference runner has a hand-rolled YAML parser (~100 lines) that breaks on edge cases like multiline values and nested objects. Use PyYAML instead but keep the same `split_frontmatter` interface.
- **Codex auth path**: Active auth must be at `~/.codex/auth.json`, NOT `~/.codex/accounts/auth.json`. This was a documented prior mistake.
- **Gemini model naming**: `gemini-3-flash-preview` works; incorrect forms like `gemini-3.0-*` do not. Model name strings must be exact.
- **Prompt weakness causes pipeline breaks**: If the role file is summarized or truncated in the prompt, models skip stages, omit required sections, or break handoff. Always inject full file contents.
- **tmux session naming**: tmux session names cannot contain dots or colons. Sanitize task IDs when building session names.
- **Concurrent git operations**: If two tasks try to commit at the same time, git will conflict. Commits must be serialized even if task execution is parallel. Use a commit lock.
- **Planner returns text vs edits file**: The reference runner observed that planners sometimes return updated task markdown in their output rather than editing the file directly. The evaluator must handle both modes (check frontmatter mutations, and if missing, check for structured markers in output).
- **Stale task file reads**: After a tmux session completes, wait briefly before reading the task file to ensure filesystem writes have flushed. This is especially relevant on networked/synced filesystems.
- **Provider CLI version drift**: CLI tools (codex, claude, gemini, qwen) update their flags and behavior. The provider abstraction should read flags from config, not hardcode them.
