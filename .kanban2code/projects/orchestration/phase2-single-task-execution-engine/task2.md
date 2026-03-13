---
stage: plan
tags: [feature, p2]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 2: Single-Task Execution Engine

Build the core execution loop: provider abstraction, prompt assembly, tmux sessions, stage dispatch, result evaluation, bounce tracking, and auto-commit. End result: one task can go through plan → code → audit → completed using configured providers.

---

## Unified Goal

Implement a complete single-task execution engine that can take a Kanban2Code task from plan through code to audit and completion. This includes:

1. **Provider abstraction** — A pluggable interface for different AI CLI providers (Codex, Claude, Gemini, Qwen)
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
- [ ] `BaseProvider` abstract class defines: `invoke(prompt, task_path, output_dir, timeouts) → InvocationResult`
- [ ] `CodexProvider` implements `BaseProvider` using subprocess + tmux
- [ ] Provider loads CLI config from `.kanban2code/_providers/*.md` frontmatter
- [ ] InvocationResult captures: ok, exit_code, timeout_type, final_message, output_paths, error_message, command
- [ ] Provider validates that the CLI binary exists on PATH before invocation

### Prompt Assembly
- [ ] Assembles full prompt from: role file, ai-guide.md, task file, context files
- [ ] Injects actual file contents — never placeholders or summaries
- [ ] Includes run metadata: run ID, repo root, task path, current stage, expected transition
- [ ] Context files resolved from task frontmatter `contexts:` field
- [ ] Handles missing context files with a clear error rather than silent omission

### Session Management
- [ ] Creates named tmux sessions for each stage invocation (e.g., `orch-run123-task1.1-plan`)
- [ ] Runs provider CLI command inside the tmux session
- [ ] Monitors session: polls for process exit and task file mutation
- [ ] Enforces wall timeout and idle timeout (configurable per stage)
- [ ] Kills session cleanly on timeout (SIGTERM then SIGKILL)
- [ ] Returns session output path for debugging

### Stage Dispatch and Evaluation
- [ ] Dispatcher takes a task path, selects provider, assembles prompt, spawns session, waits, evaluates
- [ ] Evaluator compares before/after TaskSnapshots to determine result kind
- [ ] Plan result: success if stage moved to code + required sections present; blocked if questions added
- [ ] Code result: success if stage moved to audit + Audit section present + file changed
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating < 8 + back to code
- [ ] Transport failure if expected transition did not happen
- [ ] All results include provider key, alias, model, exit code, output paths

### Run Loop and Bounce Tracking
- [ ] Run loop processes ordered queue: for each task, execute stages until completed or blocked
- [ ] Bounce tracker counts audit failures per task (stored in task state)
- [ ] Max 2 audit bounces: third cycle triggers handoff stop
- [ ] Transport retry: up to 3 attempts per stage before escalation
- [ ] Handoff writes human-readable readme with context for Dan
- [ ] Run state updated after every stage with current index, task, stage
- [ ] `continue` command resumes from persisted run state

### Auto-Commit
- [ ] On audit acceptance, commit immediately
- [ ] Only stage files listed in the task's Audit section + task file + architecture.md if changed
- [ ] Never use `git add .` or `git add -A`
- [ ] Commit message format: `feat(task-id): description\n\nAudited: rating/10 by MODEL\nFiles: N files changed\nBounces: N`
- [ ] Skip commit if no files to stage (log warning)
- [ ] Branch creation after phase/milestone completion (configurable)

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
- [ ] CodexProvider builds correct command line from provider config
- [ ] CodexProvider detects missing binary gracefully
- [ ] InvocationResult correctly reports success/failure/timeout
- [ ] Provider loads config from a sample .md frontmatter file

### Prompt Tests
- [ ] Prompt includes role file content verbatim
- [ ] Prompt includes ai-guide.md content
- [ ] Prompt includes task file content
- [ ] Prompt includes context file contents from task frontmatter
- [ ] Missing context file raises a clear error
- [ ] Prompt includes expected transition text for each stage

### Session Tests
- [ ] Session creates with correct name format
- [ ] Session detects process exit
- [ ] Wall timeout triggers session kill
- [ ] Idle timeout triggers session kill
- [ ] Session cleanup removes finished sessions

### Dispatcher/Evaluator Tests
- [ ] Plan success detected when frontmatter changes to stage: code, agent: coder
- [ ] Plan blocked detected when Questions section added
- [ ] Code success detected when frontmatter changes to stage: audit, agent: auditor
- [ ] Audit acceptance detected when rating ≥ 8 and stage: completed
- [ ] Audit rework detected when rating < 8 and stage: code
- [ ] Transport failure detected when no expected transition occurs

### Run Loop Tests
- [ ] Run loop processes a single task through plan → code → audit → completed
- [ ] Bounce counter increments on audit failure
- [ ] Third audit cycle triggers handoff stop
- [ ] Transport retry exhaustion triggers handoff stop
- [ ] Continue resumes from the correct task and stage
- [ ] Handoff readme contains task context and failure reason

### Commit Tests
- [ ] Commit stages only the specified files
- [ ] Commit message follows the defined format
- [ ] No commit when file list is empty (warning logged)
- [ ] `git add .` and `git add -A` never appear in the code
- [ ] Branch created when configured for milestone

---

## Original Source Content

The sections below contain the original task definitions preserved for reference.

---

### Task 2.1: Provider abstraction and Codex CLI provider

#### Goal

Create a BaseProvider abstract class and implement a Codex CLI provider.

#### Definition of Done

- [ ] `BaseProvider` abstract class defines: `invoke(prompt, task_path, output_dir, timeouts) → InvocationResult`
- [ ] `CodexProvider` implements `BaseProvider` using subprocess + tmux
- [ ] Provider loads CLI config from `.kanban2code/_providers/*.md` frontmatter
- [ ] InvocationResult captures: ok, exit_code, timeout_type, final_message, output_paths, error_message, command
- [ ] Provider validates that the CLI binary exists on PATH before invocation

#### Files

- `src/orchestrator/providers/__init__.py` - create - provider package init
- `src/orchestrator/providers/base.py` - create - abstract provider interface
- `src/orchestrator/providers/codex.py` - create - Codex CLI implementation

#### Tests

- [ ] CodexProvider builds correct command line from provider config
- [ ] CodexProvider detects missing binary gracefully
- [ ] InvocationResult correctly reports success/failure/timeout
- [ ] Provider loads config from a sample .md frontmatter file

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.2: Prompt assembler

#### Goal

Build a system that assembles full prompts by injecting actual file contents.

#### Definition of Done

- [ ] Assembles full prompt from: role file, ai-guide.md, task file, context files
- [ ] Injects actual file contents — never placeholders or summaries
- [ ] Includes run metadata: run ID, repo root, task path, current stage, expected transition
- [ ] Context files resolved from task frontmatter `contexts:` field
- [ ] Handles missing context files with a clear error rather than silent omission

#### Files

- `src/orchestrator/prompts.py` - create - prompt assembly logic

#### Tests

- [ ] Prompt includes role file content verbatim
- [ ] Prompt includes ai-guide.md content
- [ ] Prompt includes task file content
- [ ] Prompt includes context file contents from task frontmatter
- [ ] Missing context file raises a clear error
- [ ] Prompt includes expected transition text for each stage

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.3: tmux session manager

#### Goal

Implement programmatic tmux session management for running agent CLIs.

#### Definition of Done

- [ ] Creates named tmux sessions for each stage invocation (e.g., `orch-run123-task1.1-plan`)
- [ ] Runs provider CLI command inside the tmux session
- [ ] Monitors session: polls for process exit and task file mutation
- [ ] Enforces wall timeout and idle timeout (configurable per stage)
- [ ] Kills session cleanly on timeout (SIGTERM then SIGKILL)
- [ ] Returns session output path for debugging

#### Files

- `src/orchestrator/sessions.py` - create - tmux session lifecycle management

#### Tests

- [ ] Session creates with correct name format
- [ ] Session detects process exit
- [ ] Wall timeout triggers session kill
- [ ] Idle timeout triggers session kill
- [ ] Session cleanup removes finished sessions

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.4: Stage dispatcher and result evaluator

#### Goal

Build the stage execution logic that runs providers and evaluates frontmatter transitions.

#### Definition of Done

- [ ] Dispatcher takes a task path, selects provider, assembles prompt, spawns session, waits, evaluates
- [ ] Evaluator compares before/after TaskSnapshots to determine result kind
- [ ] Plan result: success if stage moved to code + required sections present; blocked if questions added
- [ ] Code result: success if stage moved to audit + Audit section present + file changed
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating < 8 + back to code
- [ ] Transport failure if expected transition did not happen
- [ ] All results include provider key, alias, model, exit code, output paths

#### Files

- `src/orchestrator/dispatcher.py` - create - stage execution orchestration
- `src/orchestrator/evaluator.py` - create - before/after snapshot comparison

#### Tests

- [ ] Plan success detected when frontmatter changes to stage: code, agent: coder
- [ ] Plan blocked detected when Questions section added
- [ ] Code success detected when frontmatter changes to stage: audit, agent: auditor
- [ ] Audit acceptance detected when rating ≥ 8 and stage: completed
- [ ] Audit rework detected when rating < 8 and stage: code
- [ ] Transport failure detected when no expected transition occurs

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.5: Bounce tracker and run loop

#### Goal

Implement the core run loop that processes tasks and tracks audit bounces.

#### Definition of Done

- [ ] Run loop processes ordered queue: for each task, execute stages until completed or blocked
- [ ] Bounce tracker counts audit failures per task (stored in task state)
- [ ] Max 2 audit bounces: third cycle triggers handoff stop
- [ ] Transport retry: up to 3 attempts per stage before escalation
- [ ] Handoff writes human-readable readme with context for Dan
- [ ] Run state updated after every stage with current index, task, stage
- [ ] `continue` command resumes from persisted run state

#### Files

- `src/orchestrator/dispatcher.py` - modify - add run loop and bounce tracking
- `src/orchestrator/state.py` - modify - add handoff readme generation

#### Tests

- [ ] Run loop processes a single task through plan → code → audit → completed
- [ ] Bounce counter increments on audit failure
- [ ] Third audit cycle triggers handoff stop
- [ ] Transport retry exhaustion triggers handoff stop
- [ ] Continue resumes from the correct task and stage
- [ ] Handoff readme contains task context and failure reason

#### Context

Phase 2: Single-Task Execution Engine

---

### Task 2.6: Auto-commit after audit pass

#### Goal

Implement surgical git commits after successful audit passes.

#### Definition of Done

- [ ] On audit acceptance, commit immediately
- [ ] Only stage files listed in the task's Audit section + task file + architecture.md if changed
- [ ] Never use `git add .` or `git add -A`
- [ ] Commit message format: `feat(task-id): description\n\nAudited: rating/10 by MODEL\nFiles: N files changed\nBounces: N`
- [ ] Skip commit if no files to stage (log warning)
- [ ] Branch creation after phase/milestone completion (configurable)

#### Files

- `src/orchestrator/commits.py` - create - git commit logic

#### Tests

- [ ] Commit stages only the specified files
- [ ] Commit message follows the defined format
- [ ] No commit when file list is empty (warning logged)
- [ ] `git add .` and `git add -A` never appear in the code
- [ ] Branch created when configured for milestone

#### Context

Phase 2: Single-Task Execution Engine