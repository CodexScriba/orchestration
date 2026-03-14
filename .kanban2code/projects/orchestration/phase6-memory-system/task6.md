---
stage: completed
tags:
  - feature
  - p6
agent: auditor
contexts: []
skills:
  - python-core-skills
---

# Task 6: Memory System

Implement the three-layer operational memory system for context retention across runs.

---

## Unified Goal

Build a three-layer memory system that retains context across orchestrator runs:

1. **Hot layer** — Current run context (active tasks, in-flight sessions, recent events)
2. **Warm layer** — Recent project context (last N completed tasks, recent decisions, recent errors)
3. **Cold layer** — Historical patterns (aggregated stats, common failure modes, model performance)

This enables Kadee to stay light by linking into orchestrator memory/state instead of re-reading all task files or carrying too much context in her own memory.

---

## Unified Task List

| # | Subtask | Description | Files |
|---|---------|-------------|-------|
| 6.1 | Memory system with hot, warm, and cold layers | Implement three-layer operational memory | `memory.py` |

---

## Unified Definition of Done

### Hot Layer (Current Run Context)
- [x] In-memory + state file
- [x] Tracks: active tasks, in-flight sessions, recent events
- [x] Updated in real-time during execution
- [x] Cleared/reset between runs

### Warm Layer (Recent Project Context)
- [x] File-based storage
- [x] Stores: last N completed tasks per project, recent decisions, recent errors
- [x] Configurable retention (default: last 10 tasks per project)
- [x] Persists across runs

### Cold Layer (Historical Patterns)
- [x] File-based storage
- [x] Stores: aggregated stats, common failure modes, model performance metrics
- [x] Updated after each run completion
- [x] Long-term retention

### Memory API
- [x] Memory read API: Kadee can query memory by layer and topic and use it as fast operational context
- [x] Memory write API: orchestrator appends to warm/cold after run completion
- [x] Memory is file-based and human-readable (JSON + markdown)

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

- [x] Hot memory reflects current run state
- [x] Warm memory stores last N completed tasks per project
- [x] Cold memory aggregates stats from completed runs
- [x] Memory read returns correct data by layer and topic
- [x] Memory files are valid JSON/markdown

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
- [ ] Memory read API: Kadee can query memory by layer and topic and use it as fast operational context
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

---

## Refined Prompt

Objective: Implement a three-layer operational memory system that retains context across orchestrator runs for Kadee integration.

Implementation approach:
1. **Create `memory.py`** with `MemoryManager` class that manages hot, warm, and cold layers through a unified API.
2. **Hot layer implementation** — In-memory `HotMemory` dataclass that mirrors `RunState` fields; persisted to `.kanban2code/runs/{run_id}/hot.json`; cleared/archived on run completion.
3. **Warm layer implementation** — File-based `WarmMemory` stored in `.kanban2code/memory/warm/{project}.json`; rotates entries when limit exceeded; persists across runs.
4. **Cold layer implementation** — File-based `ColdMemory` stored in `.kanban2code/memory/cold/stats.json`, `errors.json`, `performance.json`; aggregates from warm layer after run completion.
5. **Read API** — `read_memory(layer, topic=None) -> dict` that returns memory contents filtered by layer and optional topic.
6. **Write API** — `append_to_warm(project, entry)`, `append_to_cold(category, entry)`, `archive_hot_to_warm(run_state)` called at run completion.
7. **Integration hooks** — Dispatcher calls `archive_hot_to_warm()` after run completion; scheduler calls same for concurrent runs.

Key decisions:
- **Reuse RunState for hot layer**: Hot memory is essentially a view of `RunState` — no need for separate data model, just wrap existing state.
- **JSON for all layers**: Human-readable, easy to debug, compatible with existing patterns (`save_run_state`, `load_run_state`).
- **Configurable retention**: Add `memory.warm_retention_per_project` and `memory.cold_aggregation_interval` to config.json.
- **Project-scoped warm memory**: Each project gets its own warm file — prevents cross-project contamination and keeps files small.
- **Topic-based filtering**: Topics map to keys within each layer (e.g., `topic="errors"` returns `warm["errors"]` or `cold["errors"]`).

Edge cases:
- Empty memory files: Initialize with empty lists/dicts, not missing files.
- Corrupted JSON: Log warning, reinitialize with empty structure, continue.
- Missing project in warm: Create new file on first append.
- Large cold files: Keep only aggregated counts, not full event logs; rotate monthly if needed.
- Concurrent access: Use file locking for warm/cold writes (same pattern as `ThreadSafeStateWriter`).

---

## Context

### File Tree (scoped)

```
src/orchestrator/
├── memory.py                      # ← create
├── dispatcher.py                  # ← modify (add memory archive call)
├── scheduler.py                   # ← modify (add memory archive call)
├── models.py                      # ← modify (add MemoryConfig)
├── config.py                      # ← modify (add memory config parsing)
└── state.py                       # ← read-only reference

.kanban2code/
├── memory/                        # ← create (at runtime)
│   ├── warm/                      # ← create (at runtime)
│   │   └── {project}.json
│   └── cold/                      # ← create (at runtime)
│       ├── stats.json
│       ├── errors.json
│       └── performance.json
└── runs/
    └── {run_id}/
        └── hot.json               # ← create (at runtime)

config.json                        # ← modify (add memory config)
```

### Architecture Excerpts

From `orchestrator.md`:
- **Task frontmatter is source of truth**: Memory supplements but never replaces frontmatter.
- **Supplemental orchestration state is useful**: Memory fits this pattern — metadata that frontmatter should not hold.
- **Recommended state files**: Memory extends the state file pattern with warm/cold layers.

From task definition:
- **Hot layer**: In-memory + state file; tracks active tasks, in-flight sessions, recent events; cleared between runs.
- **Warm layer**: File-based; stores last N completed tasks per project, recent decisions, recent errors; persists across runs.
- **Cold layer**: File-based; stores aggregated stats, common failure modes, model performance; long-term retention.

### Skill Excerpts

From `skills/python-core-skills`:
- Use `snake_case` for modules, functions, variables (`read_memory`, `append_to_warm`).
- Use `PascalCase` for classes (`MemoryManager`, `HotMemory`, `WarmMemory`, `ColdMemory`).
- All public functions need type hints and Google-style docstrings.
- Use `from __future__ import annotations` in all modules.
- Use `pathlib.Path` for all file operations.

### Code Excerpts

**`state.py:44-58`** — Pattern for persisting state to JSON:
```python
def save_run_state(path: Path, run_state: RunState) -> None:
    """Persist a run state to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(run_state), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
```

**`state.py:60-82`** — Pattern for loading state from JSON:
```python
def load_run_state(path: Path) -> RunState:
    """Load a run state from JSON."""
    raw_state = json.loads(path.read_text(encoding="utf-8"))
    task_states = {
        task_path: TaskRunState(**task_state)
        for task_path, task_state in raw_state.get("task_states", {}).items()
    }
    # ...
```

**`models.py:247-258`** — `RunState` dataclass that hot memory will mirror:
```python
@dataclass(slots=True)
class RunState:
    """Persisted execution state for an orchestrator run."""
    schema_version: int = 1
    run_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    status: str = ""
    ordered_tasks: list[str] = field(default_factory=list)
    task_states: dict[str, TaskRunState] = field(default_factory=dict)
    recent_events: list[RunEvent] = field(default_factory=list)
    # ...
```

**`logger.py:22-42`** — Pattern for structured file writes:
```python
def append(self, event_type: str, message: str, **extras: object) -> RunEvent:
    """Append a structured event to the JSONL log."""
    event = RunEvent(
        timestamp=_utc_now_iso(),
        type=event_type,
        message=message,
        extras=dict(extras),
    )
    # ... write to file
```

**`scheduler.py:25-55`** — Thread-safe state writer pattern for concurrent access:
```python
class ThreadSafeStateWriter:
    """Thread-safe wrapper for run state persistence."""
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()

    def save(self, run_state: RunState) -> None:
        with self._lock:
            save_run_state(self._path, run_state)
```

### Dependency Graph

```
memory.py
    ├── pathlib.Path (stdlib)
    ├── json (stdlib)
    ├── threading (stdlib)
    ├── models.py (RunState, RunEvent, TaskRunState, MemoryConfig)
    ├── config.py (OrchestratorConfig)
    └── state.py (save_run_state, load_run_state patterns)

dispatcher.py (modify)
    └── memory.py (archive_hot_to_warm after run completion)

scheduler.py (modify)
    └── memory.py (archive_hot_to_warm after concurrent run completion)

config.py (modify)
    └── models.py (MemoryConfig)

models.py (modify)
    └── (add MemoryConfig dataclass)
```

### Patterns to Follow

1. **File-based JSON storage**: Follow `save_run_state` / `load_run_state` pattern for all memory files.
2. **Dataclass models**: Use `@dataclass(slots=True)` for `HotMemory`, `WarmMemory`, `ColdMemory`, `MemoryConfig`.
3. **Path construction**: Memory root is `.kanban2code/memory/`, not `.orchestrator/memory/` — stay within Kanban2Code structure.
4. **Error handling**: Log warnings on corrupted files, reinitialize with empty structure, never crash.
5. **Thread safety**: Use `threading.Lock` for warm/cold writes when called from scheduler.

### Test Patterns

From `tests/test_state.py`:
- Use `tmp_path` fixture for temporary memory files.
- Test round-trip through JSON save/load.
- Test retention limits (warm layer rotation).
- Test aggregation (cold layer updates).

For memory tests:
- Create temp `.kanban2code/memory/` structure.
- Test hot → warm archive flow.
- Test warm rotation when limit exceeded.
- Test cold aggregation from multiple warm entries.
- Test read API with layer and topic filters.

### Gotchas

- **Memory directory creation**: `.kanban2code/memory/` doesn't exist yet — create on first write.
- **Hot memory lifecycle**: Must be archived before clearing; don't lose data on run completion.
- **Warm rotation**: When limit reached, remove oldest entries first (FIFO).
- **Cold aggregation**: Don't duplicate counts — check if entry already exists before incrementing.
- **Project naming**: Use project name from `TaskSnapshot.project`, not task path parsing.

### Scope Boundaries

This task (Phase 6) should NOT touch:
- **Account rotation** (Phase 3 — complete): `accounts.py` is already implemented.
- **Concurrency** (Phase 4 — complete): `scheduler.py` modifications are only to add memory archive calls.
- **Notifications** (Phase 5 — complete): `notifier.py` is already implemented.
- **Provider logic**: Memory is orthogonal to provider execution.
- **Task frontmatter**: Memory supplements but never modifies frontmatter.

Phases 1-5 are complete — all infrastructure (config, state, dispatcher, scheduler, providers, sessions, evaluator, commits, accounts, notifier) is available for use.

---

## Audit

### Files Changed

- src/orchestrator/memory.py
- src/orchestrator/models.py
- src/orchestrator/dispatcher.py
- src/orchestrator/scheduler.py
- tests/test_memory.py
- tests/test_scheduler.py

### Summary

Fixed all review findings (previously rated 7/10):

1. **Concurrent runs skip stage_result memory data (blocker, prev round)** — `stage_events` pipeline through `TaskExecutionResult` — already landed.
2. **in_flight_sessions not persisted in real time (high, prev round)** — `_persist_hot_memory` refactor + add/remove call through — already landed.
3. **Sequential dispatcher never tracks in-flight sessions (high)** — `dispatch_stage()` now wraps each `provider.invoke()` call with `self.memory.add_in_flight_session(...)` before and `self.memory.remove_in_flight_session(...)` in a `finally` block. Both sequential and concurrent paths now track sessions identically.
4. **No dispatcher-level test for sequential execution (medium)** — Added `TestSequentialMemoryLifecycle.test_sequential_dispatcher_tracks_in_flight_sessions` which monkeypatches `_build_provider` and tracks calls to `add_in_flight_session` / `remove_in_flight_session` through a real `Dispatcher.dispatch_stage()` call.

All 132 tests pass including 21 memory tests, 3 concurrent scheduler lifecycle tests, and 1 sequential dispatcher memory lifecycle test.

---

## Review

**Rating: 9/10**

**Verdict: ACCEPTED**

### Summary
The remaining sequential-mode gap is fixed: both sequential and concurrent execution paths now report in-flight sessions into hot memory, and the scheduler lifecycle coverage added in this task now extends to the dispatcher path as well. The memory system meets the task definition across hot, warm, and cold layers.

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
- Missing tests: No significant coverage gaps identified for this task's scope; residual risk is limited to real CLI/tmux integration outside the mocked test harness.

### What's Good
- [x] The implementation now handles stage-result propagation, warm error archival, cold model-performance aggregation, and in-flight session persistence consistently across both dispatcher and scheduler execution modes.

### Recommendations
- [ ] Optional follow-up: add one smoke-style integration check against a real provider session path if the team wants extra confidence beyond the current mocked lifecycle tests.
