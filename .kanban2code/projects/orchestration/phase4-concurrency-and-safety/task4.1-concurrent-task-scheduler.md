---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 4.1: Concurrent task scheduler

## Goal

Implement the scheduler that manages multiple concurrent task runs.

## Definition of Done

- [ ] Scheduler picks multiple eligible tasks up to a dynamic concurrency limit
- [ ] Each task dispatched in its own thread with its own tmux session
- [ ] Concurrency limit decided dynamically based on available tasks and conflict analysis
- [ ] Tasks with `blocking` tag or explicit dependency are never auto-parallelized
- [ ] Thread-safe run state updates (lock or queue-based)

## Files

- `src/orchestrator/scheduler.py` - create - concurrent task scheduling
- `src/orchestrator/dispatcher.py` - modify - support concurrent dispatch

## Tests

- [ ] Two non-conflicting tasks run concurrently
- [ ] Blocking-tagged task runs alone
- [ ] Thread-safe state updates do not corrupt run state
- [ ] Dynamic concurrency adjusts when tasks finish

## Context

Phase 4: Concurrency and Safety
