# Architecture

The orchestration project is a Python-based task runner for Kanban2Code boards. It scans task markdown files under `.kanban2code/`, chooses the right execution path for each stage, and persists run state plus event logs so runs can be resumed safely.

## Runtime Flow

1. `src/orchestrator/cli.py` loads `config.json` and chooses either sequential execution (`Dispatcher`) or safe concurrent execution (`ConcurrentScheduler`).
2. `src/orchestrator/scheduler.py` evaluates queued tasks for safe parallelism.
   - Tasks tagged `blocking` run alone.
   - Tasks with `depends_on` wait for their dependencies.
   - Tasks that touch overlapping files are serialized.
3. `src/orchestrator/dispatcher.py` executes one task stage at a time through the configured provider fallback chain and tmux-backed sessions.
4. `src/orchestrator/state.py` persists `RunState` JSON and recent events so runs can continue after interruption.
5. Successful audit completions can trigger commits, while repeated failures escalate to handoff.

## Key Components

- `src/orchestrator/scanner.py`: discovers task files and parses task frontmatter/body into typed snapshots.
- `src/orchestrator/scheduler.py`: implements `ConcurrentScheduler`, `ConflictDetector`, and thread-safe run-state writes.
- `src/orchestrator/dispatcher.py`: owns single-task stage execution, fallback-provider dispatch, audit commit flow, and handoff generation.
- `src/orchestrator/providers/`: contains provider implementations for Codex, Claude, Gemini, and Qwen-family CLIs.
- `tests/test_scheduler.py`: validates concurrency, serialization, dependency handling, state persistence, and handoff behavior.
