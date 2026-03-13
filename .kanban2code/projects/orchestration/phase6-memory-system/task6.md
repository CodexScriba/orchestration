---
stage: plan
tags: [feature, p6]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 6: Memory System

Implement the three-layer operational memory system for context retention across runs.

---

## Unified Goal

Build a three-layer memory system that retains context across orchestrator runs:

1. **Hot layer** — Current run context (active tasks, in-flight sessions, recent events)
2. **Warm layer** — Recent project context (last N completed tasks, recent decisions, recent errors)
3. **Cold layer** — Historical patterns (aggregated stats, common failure modes, model performance)

This enables Kadee to query memory for context without re-reading all task files.

---

## Unified Task List

| # | Subtask | Description | Files |
|---|---------|-------------|-------|
| 6.1 | Memory system with hot, warm, and cold layers | Implement three-layer operational memory | `memory.py` |

---

## Unified Definition of Done

### Hot Layer (Current Run Context)
- [ ] In-memory + state file
- [ ] Tracks: active tasks, in-flight sessions, recent events
- [ ] Updated in real-time during execution
- [ ] Cleared/reset between runs

### Warm Layer (Recent Project Context)
- [ ] File-based storage
- [ ] Stores: last N completed tasks per project, recent decisions, recent errors
- [ ] Configurable retention (default: last 10 tasks per project)
- [ ] Persists across runs

### Cold Layer (Historical Patterns)
- [ ] File-based storage
- [ ] Stores: aggregated stats, common failure modes, model performance metrics
- [ ] Updated after each run completion
- [ ] Long-term retention

### Memory API
- [ ] Memory read API: Kadee can query memory by layer and topic
- [ ] Memory write API: orchestrator appends to warm/cold after run completion
- [ ] Memory is file-based and human-readable (JSON + markdown)

---

## Execution Order / Dependencies

```
6.1 Memory system (single task — no dependencies within phase)
```

**Dependencies:**
- Single task in this phase
- Depends on Phase 1 (state.py) and Phase 2 (run loop) being complete

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/orchestrator/memory.py` | create | Three-layer memory system |

---

## Tests

- [ ] Hot memory reflects current run state
- [ ] Warm memory stores last N completed tasks per project
- [ ] Cold memory aggregates stats from completed runs
- [ ] Memory read returns correct data by layer and topic
- [ ] Memory files are valid JSON/markdown

---

## Memory Architecture

### Hot Layer
```
Location: In-memory + state file
Contents:
  - Active tasks (currently being processed)
  - In-flight sessions (tmux session IDs, PIDs)
  - Recent events (last 20 events)
  - Current run ID, start time, status

Lifecycle:
  - Created at run start
  - Updated during execution
  - Persisted to state file on changes
  - Cleared on run completion (archived to warm)
```

### Warm Layer
```
Location: .orchestrator/memory/warm/
Contents:
  - Last N completed tasks per project (default: 10)
  - Recent decisions (architecture choices, config changes)
  - Recent errors (last 20 errors with context)

Lifecycle:
  - Updated after each task completion
  - Rotates old entries out when limit reached
  - Persists across runs
```

### Cold Layer
```
Location: .orchestrator/memory/cold/
Contents:
  - Aggregated stats (tasks completed, by stage, by project)
  - Common failure modes (patterns detected across runs)
  - Model performance (success rates, latency by provider/model)

Lifecycle:
  - Updated after each run completion
  - Aggregates from warm layer
  - Long-term retention (manual cleanup if needed)
```

---

## Memory API

### Read API
```python
def read_memory(layer: str, topic: str | None = None) -> dict:
    """
    Query memory by layer and optional topic.
    
    Args:
        layer: "hot", "warm", or "cold"
        topic: Optional filter (e.g., "errors", "decisions", "stats")
    
    Returns:
        dict with memory contents
    """
```

### Write API
```python
def append_to_warm(project: str, entry: dict) -> None:
    """Append an entry to warm memory for a project."""

def append_to_cold(category: str, entry: dict) -> None:
    """Append an entry to cold memory."""
```

---

## Original Source Content

The sections below contain the original task definitions preserved for reference.

---

### Task 6.1: Memory system with hot, warm, and cold layers

#### Goal

Implement the three-layer operational memory system for context retention.

#### Definition of Done

- [ ] Hot layer: current run context (active tasks, in-flight sessions, recent events) — in-memory + state file
- [ ] Warm layer: recent project context (last N completed tasks per project, recent decisions, recent errors) — file-based
- [ ] Cold layer: historical patterns (aggregated stats, common failure modes, model performance) — file-based
- [ ] Memory read API: Kadee can query memory by layer and topic
- [ ] Memory write API: orchestrator appends to warm/cold after run completion
- [ ] Memory is file-based and human-readable (JSON + markdown)

#### Files

- `src/orchestrator/memory.py` - create - three-layer memory system

#### Tests

- [ ] Hot memory reflects current run state
- [ ] Warm memory stores last N completed tasks per project
- [ ] Cold memory aggregates stats from completed runs
- [ ] Memory read returns correct data by layer and topic
- [ ] Memory files are valid JSON/markdown

#### Context

Phase 6: Memory System