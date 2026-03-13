---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 5: Communication and Monitoring

This task consolidates all Phase 5 tasks into a single comprehensive task for testing AI capabilities with long tasks.

---

## Task 5.1: Telegram notifier

### Goal

Implement the Telegram notification system for stage changes and escalations.

### Definition of Done

- [ ] Sends Telegram message on every stage change
- [ ] Includes: task ID, stage transition, account used, model/provider used
- [ ] Sends on blocked/stalled/escalated states with reason
- [ ] Bot token and chat ID loaded from config (not hardcoded)
- [ ] Graceful failure: notification errors do not block execution

### Files

- `src/orchestrator/notifier.py` - create - Telegram notification delivery

### Tests

- [ ] Notification sent on stage change (mocked Telegram API)
- [ ] Notification includes required fields
- [ ] Notification failure does not raise or block the run
- [ ] Bot token and chat ID loaded from config

### Context

Phase 5: Communication and Monitoring

---

## Task 5.2: Board state view for Kadee

### Goal

Implement the JSON and markdown board state view generator.

### Definition of Done

- [ ] Produces a JSON state file mapping `{project: {stage: [{task_id, title, agent, bounces, last_updated}]}}`
- [ ] Updated after every stage transition
- [ ] Also produces a human-readable markdown summary
- [ ] Kadee can read this file to understand board status without scanning every task

### Files

- `src/orchestrator/state.py` - modify - add board state view generation and markdown summary

### Tests

- [ ] Board state JSON matches expected structure from sample tasks
- [ ] Board state updates after stage transition
- [ ] Markdown summary is readable and correctly formatted

### Context

Phase 5: Communication and Monitoring

---

## Task 5.3: Smoke test suite

### Goal

Implement a smoke test suite to verify provider health and connectivity.

### Definition of Done

- [ ] `smoke-test` CLI subcommand calls each configured provider once
- [ ] Sends a trivial prompt (e.g., "Say exactly: hello") and checks for a response
- [ ] Reports pass/fail per provider with error details
- [ ] Tests: Codex, Claude, Gemini, Qwen (as configured)
- [ ] Can be run independently before starting real task execution

### Files

- `src/orchestrator/smoke.py` - create - provider health verification

### Tests

- [ ] Smoke test runs all configured providers
- [ ] Pass/fail reported per provider
- [ ] Missing provider binary reported as failure, not crash
- [ ] Auth failure reported clearly

### Context

Phase 5: Communication and Monitoring