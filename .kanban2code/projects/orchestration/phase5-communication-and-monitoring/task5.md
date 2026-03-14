---
stage: completed
tags:
  - feature
  - p5
agent: auditor
contexts: []
skills:
  - python-core-skills
---

# Task 5: Communication and Monitoring

Implement notification, board state visualization, and health verification systems.

---

## Unified Goal

Build the communication and monitoring layer for the orchestrator:

1. **Telegram notifier** — Send notifications on stage changes, escalations, and blocked states
2. **Board state view** — Generate JSON and markdown summaries of board status for Kadee
3. **Smoke test suite** — Verify provider health and connectivity before real execution

---

## Unified Task List

| # | Subtask | Description | Files |
|---|---------|-------------|-------|
| 5.1 | Telegram notifier | Implement notification system for stage changes and escalations | `notifier.py` |
| 5.2 | Board state view for Kadee | Generate JSON and markdown board state summaries | `state.py` (modify) |
| 5.3 | Smoke test suite | Provider health verification CLI command | `smoke.py` |

---

## Unified Definition of Done

### Telegram Notifier
- [x] Sends Telegram message on every stage change
- [x] Includes: task ID, stage transition, account used, model/provider used
- [x] Sends on blocked/stalled/escalated states with reason
- [x] Bot token and chat ID loaded from config (not hardcoded)
- [x] Graceful failure: notification errors do not block execution

### Board State View
- [x] Produces a JSON state file mapping `{project: {stage: [{task_id, title, agent, bounces, last_updated}]}}`
- [x] Updated after every stage transition
- [x] Also produces a human-readable markdown summary
- [x] Kadee can read this file to understand board status without scanning every task

### Smoke Test Suite
- [x] `smoke-test` CLI subcommand calls Codex, Claude, Gemini, and Qwen once each during development
- [x] Sends a trivial prompt (e.g., "Say exactly: hi" or "Say exactly: hello") and checks for a response
- [x] Reports pass/fail per provider with error details
- [x] Tests: Codex, Claude, Gemini, and Qwen explicitly
- [x] Can be run independently before starting real task execution

---

## Execution Order / Dependencies

```
5.1 Telegram notifier ──┐
                        │
5.2 Board state view ───┼──► Independent modules, can build in any order
                        │
5.3 Smoke test suite ───┘
```

**Dependencies:**
- All three subtasks are independent modules
- Can be built in any order or in parallel

**Recommended build order:**
- Build in any order — all are independent

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/orchestrator/notifier.py` | create | Telegram notification delivery |
| `src/orchestrator/state.py` | modify | Add board state view generation and markdown summary |
| `src/orchestrator/smoke.py` | create | Provider health verification |

---

## Tests

### Notifier Tests
- [x] Notification sent on stage change (mocked Telegram API)
- [x] Notification includes required fields
- [x] Notification failure does not raise or block the run
- [x] Bot token and chat ID loaded from config

### Board State Tests
- [x] Board state JSON matches expected structure from sample tasks
- [x] Board state updates after stage transition
- [x] Markdown summary is readable and correctly formatted

### Smoke Test Tests
- [x] Smoke test runs all configured providers
- [x] Pass/fail reported per provider
- [x] Missing provider binary reported as failure, not crash
- [x] Auth failure reported clearly

---

## Notification Policy

### Stage Change Notifications
Every stage change triggers a notification including:
- Task ID
- Stage transition (e.g., `plan → code`)
- Account used
- Model/provider used

### Escalation Notifications
Blocked, stalled, or escalated states trigger notifications with:
- Task ID
- Current state
- Reason for block/escalation
- Recommended action (if applicable)

### Graceful Failure
- Notification errors are logged but do not block execution
- If Telegram API is unavailable, continue without notification
- Retry logic optional (not required for MVP)

---

## Board State Format

### JSON Structure
```json
{
  "project_name": {
    "inbox": [
      {"task_id": "task1", "title": "...", "agent": "...", "bounces": 0, "last_updated": "..."}
    ],
    "plan": [...],
    "code": [...],
    "audit": [...],
    "completed": [...]
  }
}
```

### Markdown Summary
Human-readable summary for Kadee to quickly understand board status without scanning every task file; this is one of the main ways Kadee links into orchestrator memory/state.

---

## Smoke Test Behavior

### Command
```bash
orchestrator smoke-test
```

### Behavior
1. Load configured providers from config
2. For each provider:
   - Send trivial prompt: "Say exactly: hello"
   - Check for response
   - Report pass/fail with error details if failed
3. Summary report at end

### Failure Handling
- Missing binary: report as failure (not crash)
- Auth failure: report clearly with remediation hint
- Network failure: report with error details

---

## Original Source Content

The sections below contain the original task definitions preserved for reference.

---

### Task 5.1: Telegram notifier

#### Goal

Implement the Telegram notification system for stage changes and escalations.

#### Definition of Done

- [x] Sends Telegram message on every stage change
- [x] Includes: task ID, stage transition, account used, model/provider used
- [x] Sends on blocked/stalled/escalated states with reason
- [x] Bot token and chat ID loaded from config (not hardcoded)
- [x] Graceful failure: notification errors do not block execution

#### Files

- `src/orchestrator/notifier.py` - create - Telegram notification delivery

#### Tests

- [x] Notification sent on stage change (mocked Telegram API)
- [x] Notification includes required fields
- [x] Notification failure does not raise or block the run
- [x] Bot token and chat ID loaded from config

#### Context

Phase 5: Communication and Monitoring

---

### Task 5.2: Board state view for Kadee

#### Goal

Implement the JSON and markdown board state view generator.

#### Definition of Done

- [x] Produces a JSON state file mapping `{project: {stage: [{task_id, title, agent, bounces, last_updated}]}}`
- [x] Updated after every stage transition
- [x] Also produces a human-readable markdown summary
- [x] Kadee can read this file to understand board status without scanning every task

#### Files

- `src/orchestrator/state.py` - modify - add board state view generation and markdown summary

#### Tests

- [x] Board state JSON matches expected structure from sample tasks
- [x] Board state updates after stage transition
- [x] Markdown summary is readable and correctly formatted

#### Context

Phase 5: Communication and Monitoring

---

### Task 5.3: Smoke test suite

#### Goal

Implement a smoke test suite to verify provider health and connectivity.

#### Definition of Done

- [x] `smoke-test` CLI subcommand calls Codex, Claude, Gemini, and Qwen once each during development
- [x] Sends a trivial prompt (e.g., "Say exactly: hi" or "Say exactly: hello") and checks for a response
- [x] Reports pass/fail per provider with error details
- [x] Tests: Codex, Claude, Gemini, and Qwen explicitly
- [x] Can be run independently before starting real task execution

#### Files

- `src/orchestrator/smoke.py` - create - provider health verification

#### Tests

- [x] Smoke test runs all configured providers
- [x] Pass/fail reported per provider
- [x] Missing provider binary reported as failure, not crash
- [x] Auth failure reported clearly

#### Context

Phase 5: Communication and Monitoring

## Refined Prompt
Objective: Implement the communication and monitoring layer, including a Telegram notifier, board state visualization (JSON/MD), and a provider smoke test suite.

Implementation approach:
1. **Telegram Notifier**: Create `src/orchestrator/notifier.py` using `python-telegram-bot`. Implement `notify_stage_change` and `notify_escalation`. Load credentials from `OrchestratorConfig` (env vars: `ORCHESTRATOR_TELEGRAM_BOT_TOKEN`, `ORCHESTRATOR_TELEGRAM_CHAT_ID`). Ensure failures are logged but non-blocking.
2. **Board State View**: Modify `src/orchestrator/state.py` to add `build_detailed_board_state` (returning the specified JSON structure) and `render_board_summary` (returning Markdown). Derive `title` from the first H1 in the task body and `last_updated` from file modification time.
3. **Smoke Test Suite**: Create `src/orchestrator/smoke.py` with a `SmokeTester` class. It should iterate through configured providers, send a trivial prompt ("Say exactly: hello"), and verify the response.
4. **Integration**: Update `src/orchestrator/dispatcher.py` to initialize the `Notifier` and trigger notifications/board state updates after each stage transition. Update `src/orchestrator/cli.py` to wire up the `smoke-test` command.

Key decisions:
- **Telegram Client**: Use `python-telegram-bot` as it's already a dependency and provides a clean async/sync interface.
- **Board State Storage**: Save `board_state.json` and `BOARD.md` to `.kanban2code/` root for Kadee's accessibility.
- **Smoke Test Scope**: Explicitly test Codex, Claude, Gemini, and Qwen as they are the primary providers in the architecture.

Edge cases:
- Telegram bot token/chat ID missing: Log a warning and skip notification.
- Provider binary missing during smoke test: Report as a clear failure with a remediation hint.
- Task file without H1: Use `task_id` (filename) as the fallback title.

## Context

### File Tree (scoped)
- src/orchestrator/
    - notifier.py             <- create
    - smoke.py                <- create
    - state.py                <- modify
    - dispatcher.py           <- modify
    - cli.py                  <- modify
    - config.py               <- read-only reference
    - models.py               <- read-only reference
    - scanner.py              <- read-only reference
    - providers/
        - base.py             <- read-only reference

### Architecture Excerpts
- "Phase 5: Communication and Monitoring" focus on observability and health.
- `Dispatcher` is the central hub for orchestration; notifications and state updates should hook in here.
- `state.py` is the source of truth for translating raw snapshots into structured status.

### Skill Excerpts
Python Core Skills (PEP 8 + Modern Best Practices):
- Use snake_case for functions and variables.
- Always include type hints.
- Use Google-style docstrings for public methods.
- Handle specific exceptions (e.g., `TelegramError`).

### Code Excerpts
- `src/orchestrator/state.py:11-33`: Current board index and compact state logic. Use as a base for the detailed version.
- `src/orchestrator/config.py:183-199`: `NotificationConfig` and `TelegramNotificationConfig` parsing.
- `src/orchestrator/dispatcher.py:207-227`: Main run loop. Hook notifier and state updates after `self._record_stage_result`.
- `src/orchestrator/models.py:110-116`: `TelegramNotificationConfig` definition.

### Dependency Graph
- `notifier.py` -> `config.py`, `models.py`, `python-telegram-bot`
- `smoke.py` -> `config.py`, `dispatcher.py` (for provider building)
- `dispatcher.py` -> `notifier.py`, `state.py`
- `cli.py` -> `smoke.py`

### Test Patterns
- Use `pytest` with `unittest.mock` to mock Telegram API calls.
- Verify JSON structure of board state matches the requirement.
- Smoke test should be testable by mocking the provider's `invoke` method.

### Gotchas
- `python-telegram-bot` v20+ is primarily async. Since the orchestrator is currently sync, use `asyncio.run` or the library's sync-compatible wrappers if available, or simply use `httpx`/`requests` if only sending simple messages is needed. (Self-correction: `python-telegram-bot` provides `Bot.send_message` which is async; wrapping it in a helper is fine).

### Scope Boundaries
- Do not modify provider implementation details (e.g., `claude.py`).
- Do not change the core run logic in `dispatcher.py` beyond adding the hooks.

---

## Audit

### Files Touched
- src/orchestrator/notifier.py
- src/orchestrator/smoke.py
- src/orchestrator/state.py
- src/orchestrator/dispatcher.py
- src/orchestrator/cli.py
- tests/test_phase5.py

---

## Review

**Rating: 9/10**

**Verdict: ACCEPTED**

### Summary
Re-audit of the current code shows the previous smoke-family and stalled-notification findings are resolved. The communication and monitoring layer now meets the Phase 5 definition of done, and the supporting test coverage is strong.

### Findings

#### Blockers
- None.

#### High Priority
- None.

#### Medium Priority
- None.

#### Low Priority / Nits
- None.

### Test Assessment
- Coverage: Adequate
- Missing tests: Optional live end-to-end smoke verification against real provider CLIs and credentials would add runtime confidence, but the current unit/integration coverage is sufficient for acceptance

### What&apos;s Good
- `SmokeTester` now resolves provider families from provider metadata, preserves configured model/override settings, and covers the required provider families without relying on alias substrings.
- The shared `post_stage_hook` keeps sequential and concurrent observability behavior aligned, and dependency-stalled tasks now emit escalation notifications with a reason.
- The board-state JSON includes the canonical stage buckets and the Phase 5 test suite now covers the previously missed behaviors directly.

### Recommendations
- Consider adding an opt-in live smoke run to docs or CI if you want validation against real installed CLIs and credentials in addition to the mocked suite.
