---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 4: Concurrency and Safety

This task consolidates all Phase 4 tasks into a single comprehensive task for testing AI capabilities with long tasks.

---

## Task 4.1: Concurrent task scheduler

### Goal

Implement the scheduler that manages multiple concurrent task runs.

### Definition of Done

- [ ] Scheduler picks multiple eligible tasks up to a dynamic concurrency limit
- [ ] Each task dispatched in its own thread with its own tmux session
- [ ] Concurrency limit decided dynamically based on available tasks and conflict analysis
- [ ] Tasks with `blocking` tag or explicit dependency are never auto-parallelized
- [ ] Thread-safe run state updates (lock or queue-based)

### Files

- `src/orchestrator/scheduler.py` - create - concurrent task scheduling
- `src/orchestrator/dispatcher.py` - modify - support concurrent dispatch

### Tests

- [ ] Two non-conflicting tasks run concurrently
- [ ] Blocking-tagged task runs alone
- [ ] Thread-safe state updates do not corrupt run state
- [ ] Dynamic concurrency adjusts when tasks finish

### Context

Phase 4: Concurrency and Safety

---

## Task 4.2: File-level conflict detection

### Goal

Implement conflict detection logic based on the files each task will touch.

### Definition of Done

- [ ] Before dispatching, check which files each task will touch (from task body/context)
- [ ] Two tasks with overlapping file sets must not run concurrently
- [ ] Conflict detected at dispatch time, not after launch
- [ ] Conflict resolution: delay the later task until the earlier one completes
- [ ] Log conflict decisions

### Files

- `src/orchestrator/scheduler.py` - modify - add file-level conflict detection

### Tests

- [ ] Tasks touching different files are allowed concurrently
- [ ] Tasks touching the same file are serialized
- [ ] Conflict detection reads file lists from task body
- [ ] Delayed task is dispatched after conflicting task completes

### Context

Phase 4: Concurrency and Safety