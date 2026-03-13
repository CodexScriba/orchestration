---
stage: plan
tags: [feature, p4]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 4: Concurrency and Safety

Implement concurrent task execution with file-level conflict detection and safe parallelization.

---

## Unified Goal

Enable the orchestrator to run multiple tasks concurrently while ensuring safety through conflict detection:

1. **Concurrent task scheduler** — Manage multiple parallel task runs with dynamic concurrency limits
2. **File-level conflict detection** — Prevent concurrent tasks from touching the same files

---

## Unified Task List

| # | Subtask | Description | Files |
|---|---------|-------------|-------|
| 4.1 | Concurrent task scheduler | Implement multi-threaded task dispatch with dynamic concurrency | `scheduler.py` (create), `dispatcher.py` (modify) |
| 4.2 | File-level conflict detection | Detect and prevent concurrent access to overlapping files | `scheduler.py` (modify) |

---

## Unified Definition of Done

### Concurrent Task Scheduler
- [ ] Scheduler picks multiple eligible tasks up to a dynamic concurrency limit
- [ ] Each task dispatched in its own thread with its own tmux session
- [ ] Concurrency limit decided dynamically based on available tasks and conflict analysis
- [ ] Tasks with `blocking` tag or explicit dependency are never auto-parallelized
- [ ] Thread-safe run state updates (lock or queue-based)

### File-Level Conflict Detection
- [ ] Before dispatching, check which files each task will touch (from task body/context)
- [ ] Two tasks with overlapping file sets must not run concurrently
- [ ] Conflict detected at dispatch time, not after launch
- [ ] Conflict resolution: delay the later task until the earlier one completes
- [ ] Log conflict decisions

---

## Execution Order / Dependencies

```
4.1 Concurrent scheduler ──► 4.2 File-level conflict detection
         │                            │
         └────────────────────────────┘
              (conflict detection integrates into scheduler)
```

**Dependencies:**
- **4.1** must be built first (scheduler infrastructure)
- **4.2** extends the scheduler with conflict detection logic

**Recommended build order:**
1. Build 4.1 (basic concurrent scheduler)
2. Build 4.2 (add conflict detection to scheduler)

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/orchestrator/scheduler.py` | create | Concurrent task scheduling |
| `src/orchestrator/dispatcher.py` | modify | Support concurrent dispatch |

---

## Tests

### Scheduler Tests
- [ ] Two non-conflicting tasks run concurrently
- [ ] Blocking-tagged task runs alone
- [ ] Thread-safe state updates do not corrupt run state
- [ ] Dynamic concurrency adjusts when tasks finish

### Conflict Detection Tests
- [ ] Tasks touching different files are allowed concurrently
- [ ] Tasks touching the same file are serialized
- [ ] Conflict detection reads file lists from task body
- [ ] Delayed task is dispatched after conflicting task completes

---

## Concurrency Rules

### Guardrails
- Tasks with `blocking` tag run alone (no parallelization)
- Tasks with explicit dependencies wait for their dependencies
- File-level conflicts prevent parallel execution
- Thread-safe state updates required (use locks or queue-based approach)

### Dynamic Concurrency
- Concurrency limit is not a fixed cap
- Decided dynamically based on:
  - Number of available eligible tasks
  - Conflict analysis results
  - System resources (optional)

### Conflict Resolution
- Detect conflicts at dispatch time (before launch)
- If Task A and Task B touch overlapping files:
  - Run Task A first
  - Queue Task B
  - Dispatch Task B after Task A completes

---

## Original Source Content

The sections below contain the original task definitions preserved for reference.

---

### Task 4.1: Concurrent task scheduler

#### Goal

Implement the scheduler that manages multiple concurrent task runs.

#### Definition of Done

- [ ] Scheduler picks multiple eligible tasks up to a dynamic concurrency limit
- [ ] Each task dispatched in its own thread with its own tmux session
- [ ] Concurrency limit decided dynamically based on available tasks and conflict analysis
- [ ] Tasks with `blocking` tag or explicit dependency are never auto-parallelized
- [ ] Thread-safe run state updates (lock or queue-based)

#### Files

- `src/orchestrator/scheduler.py` - create - concurrent task scheduling
- `src/orchestrator/dispatcher.py` - modify - support concurrent dispatch

#### Tests

- [ ] Two non-conflicting tasks run concurrently
- [ ] Blocking-tagged task runs alone
- [ ] Thread-safe state updates do not corrupt run state
- [ ] Dynamic concurrency adjusts when tasks finish

#### Context

Phase 4: Concurrency and Safety

---

### Task 4.2: File-level conflict detection

#### Goal

Implement conflict detection logic based on the files each task will touch.

#### Definition of Done

- [ ] Before dispatching, check which files each task will touch (from task body/context)
- [ ] Two tasks with overlapping file sets must not run concurrently
- [ ] Conflict detected at dispatch time, not after launch
- [ ] Conflict resolution: delay the later task until the earlier one completes
- [ ] Log conflict decisions

#### Files

- `src/orchestrator/scheduler.py` - modify - add file-level conflict detection

#### Tests

- [ ] Tasks touching different files are allowed concurrently
- [ ] Tasks touching the same file are serialized
- [ ] Conflict detection reads file lists from task body
- [ ] Delayed task is dispatched after conflicting task completes

#### Context

Phase 4: Concurrency and Safety