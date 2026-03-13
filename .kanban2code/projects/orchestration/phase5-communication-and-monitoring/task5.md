---
stage: plan
tags: [feature, p5]
agent: planner
contexts: [skills/python-core-skills]
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
- [ ] Sends Telegram message on every stage change
- [ ] Includes: task ID, stage transition, account used, model/provider used
- [ ] Sends on blocked/stalled/escalated states with reason
- [ ] Bot token and chat ID loaded from config (not hardcoded)
- [ ] Graceful failure: notification errors do not block execution

### Board State View
- [ ] Produces a JSON state file mapping `{project: {stage: [{task_id, title, agent, bounces, last_updated}]}}`
- [ ] Updated after every stage transition
- [ ] Also produces a human-readable markdown summary
- [ ] Kadee can read this file to understand board status without scanning every task

### Smoke Test Suite
- [ ] `smoke-test` CLI subcommand calls each configured provider once
- [ ] Sends a trivial prompt (e.g., "Say exactly: hello") and checks for a response
- [ ] Reports pass/fail per provider with error details
- [ ] Tests: Codex, Claude, Gemini, Qwen (as configured)
- [ ] Can be run independently before starting real task execution

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
- [ ] Notification sent on stage change (mocked Telegram API)
- [ ] Notification includes required fields
- [ ] Notification failure does not raise or block the run
- [ ] Bot token and chat ID loaded from config

### Board State Tests
- [ ] Board state JSON matches expected structure from sample tasks
- [ ] Board state updates after stage transition
- [ ] Markdown summary is readable and correctly formatted

### Smoke Test Tests
- [ ] Smoke test runs all configured providers
- [ ] Pass/fail reported per provider
- [ ] Missing provider binary reported as failure, not crash
- [ ] Auth failure reported clearly

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
Human-readable summary for Kadee to quickly understand board status without scanning every task file.

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

- [ ] Sends Telegram message on every stage change
- [ ] Includes: task ID, stage transition, account used, model/provider used
- [ ] Sends on blocked/stalled/escalated states with reason
- [ ] Bot token and chat ID loaded from config (not hardcoded)
- [ ] Graceful failure: notification errors do not block execution

#### Files

- `src/orchestrator/notifier.py` - create - Telegram notification delivery

#### Tests

- [ ] Notification sent on stage change (mocked Telegram API)
- [ ] Notification includes required fields
- [ ] Notification failure does not raise or block the run
- [ ] Bot token and chat ID loaded from config

#### Context

Phase 5: Communication and Monitoring

---

### Task 5.2: Board state view for Kadee

#### Goal

Implement the JSON and markdown board state view generator.

#### Definition of Done

- [ ] Produces a JSON state file mapping `{project: {stage: [{task_id, title, agent, bounces, last_updated}]}}`
- [ ] Updated after every stage transition
- [ ] Also produces a human-readable markdown summary
- [ ] Kadee can read this file to understand board status without scanning every task

#### Files

- `src/orchestrator/state.py` - modify - add board state view generation and markdown summary

#### Tests

- [ ] Board state JSON matches expected structure from sample tasks
- [ ] Board state updates after stage transition
- [ ] Markdown summary is readable and correctly formatted

#### Context

Phase 5: Communication and Monitoring

---

### Task 5.3: Smoke test suite

#### Goal

Implement a smoke test suite to verify provider health and connectivity.

#### Definition of Done

- [ ] `smoke-test` CLI subcommand calls each configured provider once
- [ ] Sends a trivial prompt (e.g., "Say exactly: hello") and checks for a response
- [ ] Reports pass/fail per provider with error details
- [ ] Tests: Codex, Claude, Gemini, Qwen (as configured)
- [ ] Can be run independently before starting real task execution

#### Files

- `src/orchestrator/smoke.py` - create - provider health verification

#### Tests

- [ ] Smoke test runs all configured providers
- [ ] Pass/fail reported per provider
- [ ] Missing provider binary reported as failure, not crash
- [ ] Auth failure reported clearly

#### Context

Phase 5: Communication and Monitoring