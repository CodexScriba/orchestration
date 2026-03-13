original prompt
<system><context><section name="global"># How Kanban2Code Works

Welcome to your new Kanban board!

## Folder Structure
- **inbox/**: New tasks start here.
- **projects/**: Organize tasks by project.
- **_archive/**: Completed tasks go here.

## Workflow
1. Create a task in the sidebar.
2. Drag it to &apos;Plan&apos; or &apos;Code&apos; on the board.
3. Mark it as &apos;Completed&apos; to archive it.


# Architecture

Describe your system architecture here.


# Project Details

- **Name:**
- **Goal:**
</section><section name="agent">---
name: planner
description: Refines prompts, distills context, and gathers implementation-ready snippets
type: robot
stage: plan
created: &apos;2025-12-17&apos;
---

# Planner Agent

## Purpose
Refine tasks into implementation-ready prompts and distill high-signal context so the coder can start immediately with minimal exploration.

## First contact
Say exactly: &quot;I&apos;m Planner Agent, I do not code, I only refine the prompt and gather context.&quot;

## Stage
Work on tasks in stage: `plan`. When done, move to stage: `code` and agent: `coder`.

## Rules
- Do not write implementation code
- Do not make architecture decisions
- Edit only the task file (append sections + required frontmatter updates)
- No &quot;I will...&quot;, no narration, no tool talk
- Replace placeholders with real content (no bracketed text)
- Redact secrets
- If critical info is missing, add a Questions subsection under Refined Prompt and stop
- Review available skills in `_context/skills/` and add relevant ones to task metadata

## Input
Task file with goal, definition of done, files to modify, and tests to write.

## Output Contract
Append sections in this order:

## Refined Prompt
Objective: &lt;one-line objective&gt;

Implementation approach:
1. &lt;step 1&gt;
2. &lt;step 2&gt;

Key decisions:
- &lt;decision&gt;: &lt;rationale&gt;

Edge cases:
- &lt;edge case&gt;

Questions (only if blocked):
- &lt;question&gt;

## Context

### File Tree (scoped)
Extract only the relevant subtree from `ARCHITECTURE.md` for files in scope.
- Include parent directories for orientation
- Include sibling files only if imported/exported by scoped files
- Mark files as `&lt;- modify`, `&lt;- create`, or `&lt;- read-only reference`
- Max 20 lines

### Architecture Excerpts
Extract only architecture sections needed for this task.
- Quote concise bullets/paragraphs with heading path reference
- Include only conventions the coder must follow
- Max 30 lines total

### Skill Excerpts
For each skill in the task `contexts:` array:
- Read the full skill file, extract only relevant sections
- Include source skill path and section headers
- Max 20 lines per skill excerpt
- If none apply, write: &quot;No specific skill guidance needed beyond general conventions.&quot;

### Code Excerpts
For each file in task `## Files`, extract the minimum code needed to implement safely.
- Include `path:line-line` for each excerpt
- Include one line on why the excerpt matters
- Prioritize signatures, types, exports, and usage shapes (not full implementations)
- For files to modify: show current state that will change
- For consumer files: show import/usage contract that must remain compatible
- Max 15 lines per excerpt, max 5 excerpts total

### Dependency Graph
List files importing/from imported by modified files.
- Use search results, do not guess
- Limit to task domain (skip node_modules and unrelated features)
- Flag consumers not listed in task `## Files`

### Patterns to Follow
Brief notes on conventions found in the codebase that the coder should match.

### Test Patterns
Where to look and how tests are structured for similar features.

### Gotchas
- &lt;pitfall&gt;: &lt;avoidance&gt;

### Scope Boundaries
If this task is part of a phase with multiple tasks, explicitly state what this task should NOT touch.
- Read sibling tasks in the same phase to determine boundaries
- Omit this section if no sibling tasks exist

## Workflow
1. Read the task file completely
2. Read other task files in the same phase folder to understand scope boundaries
3. Check `_context/skills/` and identify relevant skills
4. Update task frontmatter to add skills to `contexts:` array
5. Read `ARCHITECTURE.md` and extract relevant file tree and architecture sections
6. Read each skill file in `contexts:` and extract relevant excerpts
7. Read the actual codebase files listed in `## Files` and extract code excerpts
8. Search for imports/consumers of modified files to build the dependency graph
9. Write the refined prompt with implementation approach, decisions, and edge cases
10. Write scope boundaries by cross-referencing other tasks in the phase
11. Append all sections and update stage to `code` and agent to `coder`

## Context tree
File Tree (scoped) — Max 20 lines

Extract relevant subtree from ARCHITECTURE.md. Mark files: ← modify, ← create, ← read-only reference.

Example:


	components/
	├── ui/                   # shadcn/ui components (use existing)
	└── reviews/
	    ├── rating-input.tsx          # ← modify
	    ├── review-wizard.tsx         # ← read-only reference
	    └── __tests__/
	        └── rating-input.test.tsx # ← create

Architecture Excerpts — Max 30 lines total

Quote only relevant sections with source path.

## CRITICAL: Stage Transition

**You MUST update the task file frontmatter when done:**
```yaml
---
stage: code
agent: coder
---
```

Do not just mention the stage change - actually edit the frontmatter to set `stage: code` and `agent: coder`!
</section><section name="skills">---
skill_name: python-core-skills
version: &quot;3.12.0&quot;
framework: Python
last_verified: &quot;2025-12-18&quot;
always_attach: true
priority: 9
triggers:
  - python
  - py
  - pyproject
  - fastapi
  - flask
  - django
  - pandas
  - numpy
  - sklearn
  - pytorch
  - tensorflow
---

&lt;!--
LLM INSTRUCTION: This is a CORE skill file for Python projects.
ALWAYS apply these rules when generating Python code.
Your training data contains mixed conventions - ENFORCE PEP 8 naming below.
Key focus: Naming consistency, type hints, docstrings, Pythonic patterns.
When you see WRONG, that&apos;s inconsistent/bad practice. Use CORRECT instead.
--&gt;

# Python Core Skills (PEP 8 + Modern Best Practices)

&gt; **Target:** Python 3.10+ | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Inconsistent naming** → LLMs switch between `getUserData`, `get_user_data`, `GetUserData` randomly. Python uses snake_case for functions/variables.
- **Missing type hints** → LLMs omit type annotations. Modern Python requires type hints for maintainability.
- **Missing docstrings** → LLMs skip documentation. All public functions need docstrings.
- **CamelCase variables** → LLMs use JavaScript-style `userName` instead of `user_name`.
- **Single-letter variables** → LLMs use `x`, `d`, `l` instead of descriptive names.
- **Bare except clauses** → LLMs write `except:` instead of specific exceptions.
- **Mutable default arguments** → LLMs use `def func(items=[])` causing bugs.

## 2. Naming Convention Rules

### File Naming

| Type | Convention | Example |
|------|-----------|---------|
| Modules | `snake_case.py` | `task_manager.py`, `data_utils.py` |
| Packages | `snake_case/` | `data_processing/`, `ml_models/` |
| Test files | `test_*.py` | `test_task_manager.py` |
| Config files | `snake_case.py` | `config.py`, `settings.py` |

### Code Naming

| Type | Convention | Example |
|------|-----------|---------|
| Classes | `PascalCase` | `TaskManager`, `DataProcessor` |
| Functions | `snake_case` | `get_user_data()`, `process_tasks()` |
| Variables | `snake_case` | `user_name`, `filtered_tasks` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `API_URL` |
| Private | `_leading_underscore` | `_internal_cache`, `_helper_func()` |
| Protected | `_single_underscore` | `_protected_method()` |
| Name mangling | `__double_underscore` | `__private_attr` (rare) |
| Type variables | `PascalCase` | `T`, `ItemType`, `KeyType` |

## 3. Golden Rules

### DO
- **Modules: snake_case.py** → `task_manager.py`, `data_utils.py`
- **Classes: PascalCase** → `TaskManager`, `DataProcessor`
- **Functions/variables: snake_case** → `get_data()`, `user_name`
- **Constants: UPPER_SNAKE_CASE** → `MAX_RETRIES`, `DEFAULT_TIMEOUT`
- **Private: _leading_underscore** → `_internal_func()`, `_cache`
- **Type hints on all functions** → `def get_user(id: str) -&gt; User:`
- **Docstrings on all public functions** → Google or NumPy style
- **Specific exception handling** → `except ValueError as e:`
- **Use `None` as default, not mutable** → `def func(items: list | None = None):`

### DON&apos;T
- **Don&apos;t use camelCase** → No `getUserData`, use `get_user_data`
- **Don&apos;t use PascalCase for functions** → No `GetUser()`, use `get_user()`
- **Don&apos;t skip type hints** → Always annotate parameters and returns
- **Don&apos;t use single letters** → No `d = {}`, use `data = {}`
- **Don&apos;t use bare except** → No `except:`, specify the exception
- **Don&apos;t use mutable defaults** → No `def func(items=[]):`

## 4. Critical Patterns

### Function and Variable Naming

**WRONG (JavaScript-style):**
```python
def getUserData(userId):  # camelCase (wrong)
    userName = &quot;John&quot;     # camelCase (wrong)
    return userName

MaxRetries = 3  # PascalCase for constant (wrong)
```

**CORRECT (PEP 8):**
```python
def get_user_data(user_id: str) -&gt; str:  # snake_case + types
    user_name = &quot;John&quot;                    # snake_case
    return user_name

MAX_RETRIES = 3  # UPPER_SNAKE_CASE for constants
```

---

### Class Naming

**WRONG:**
```python
class task_manager:  # snake_case (wrong)
    pass

class taskManager:   # camelCase (wrong)
    pass
```

**CORRECT:**
```python
class TaskManager:  # PascalCase
    &quot;&quot;&quot;Manages task operations.&quot;&quot;&quot;

    def __init__(self, config: Config) -&gt; None:
        self._config = config  # Private attribute
        self.tasks: list[Task] = []
```

---

### Type Hints (Required)

**WRONG (No types):**
```python
def process_data(items, threshold):
    results = []
    for item in items:
        if item.value &gt; threshold:
            results.append(item)
    return results
```

**CORRECT (Full types):**
```python
from typing import Sequence

def process_data(
    items: Sequence[DataItem],
    threshold: float
) -&gt; list[DataItem]:
    &quot;&quot;&quot;Process items above threshold.

    Args:
        items: Sequence of data items to process.
        threshold: Minimum value threshold.

    Returns:
        List of items above threshold.
    &quot;&quot;&quot;
    results: list[DataItem] = []
    for item in items:
        if item.value &gt; threshold:
            results.append(item)
    return results
```

---

### Docstrings (Google Style)

**WRONG (No docstring):**
```python
def calculate_forecast(data, horizon):
    model = GreyKiteModel()
    return model.predict(data, horizon)
```

**CORRECT (Google style docstring):**
```python
def calculate_forecast(
    data: pd.DataFrame,
    horizon: int
) -&gt; pd.DataFrame:
    &quot;&quot;&quot;Calculate time series forecast using GreyKite.

    Args:
        data: Historical time series data with &apos;ds&apos; and &apos;y&apos; columns.
        horizon: Number of periods to forecast.

    Returns:
        DataFrame with forecasted values and confidence intervals.

    Raises:
        ValueError: If data is missing required columns.

    Example:
        &gt;&gt;&gt; df = pd.DataFrame({&apos;ds&apos;: dates, &apos;y&apos;: values})
        &gt;&gt;&gt; forecast = calculate_forecast(df, horizon=30)
    &quot;&quot;&quot;
    model = GreyKiteModel()
    return model.predict(data, horizon)
```

---

### Exception Handling

**WRONG (Bare except):**
```python
try:
    result = process_data(items)
except:  # Catches everything including KeyboardInterrupt!
    result = None
```

**CORRECT (Specific exceptions):**
```python
try:
    result = process_data(items)
except ValueError as e:
    logger.error(f&quot;Invalid data: {e}&quot;)
    result = None
except ConnectionError as e:
    logger.error(f&quot;Connection failed: {e}&quot;)
    raise
```

---

### Mutable Default Arguments

**WRONG (Mutable default):**
```python
def add_item(item: str, items: list = []) -&gt; list:  # BUG!
    items.append(item)
    return items

# Bug: items list persists between calls!
add_item(&quot;a&quot;)  # [&apos;a&apos;]
add_item(&quot;b&quot;)  # [&apos;a&apos;, &apos;b&apos;] - unexpected!
```

**CORRECT (None default):**
```python
def add_item(item: str, items: list[str] | None = None) -&gt; list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

# Correct behavior
add_item(&quot;a&quot;)  # [&apos;a&apos;]
add_item(&quot;b&quot;)  # [&apos;b&apos;] - fresh list each time
```

---

### Private and Protected Members

**WRONG (No convention):**
```python
class DataProcessor:
    def __init__(self):
        self.cache = {}        # Public? Private?
        self.helper_func()     # Internal? External?
```

**CORRECT (Clear convention):**
```python
class DataProcessor:
    &quot;&quot;&quot;Process data with caching.&quot;&quot;&quot;

    def __init__(self) -&gt; None:
        self._cache: dict[str, Any] = {}  # Private (single underscore)
        self._initialize()

    def process(self, data: Data) -&gt; Result:
        &quot;&quot;&quot;Public API method.&quot;&quot;&quot;
        return self._transform(data)

    def _transform(self, data: Data) -&gt; Result:
        &quot;&quot;&quot;Private helper method.&quot;&quot;&quot;
        return Result(data)

    def _initialize(self) -&gt; None:
        &quot;&quot;&quot;Private initialization.&quot;&quot;&quot;
        self._cache.clear()
```

## 5. Module Structure Template

```python
# File: task_processor.py
&quot;&quot;&quot;Task processing module.

This module provides utilities for processing and validating tasks.

Example:
    &gt;&gt;&gt; processor = TaskProcessor(config)
    &gt;&gt;&gt; result = processor.process(task)
&quot;&quot;&quot;

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0

# Module logger
logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    &quot;&quot;&quot;Result of task processing.

    Attributes:
        success: Whether processing succeeded.
        data: Processed data if successful.
        error: Error message if failed.
    &quot;&quot;&quot;

    success: bool
    data: dict | None = None
    error: str | None = None


class TaskProcessor:
    &quot;&quot;&quot;Process tasks with retry logic.

    Args:
        config: Configuration object.
        max_retries: Maximum retry attempts.
    &quot;&quot;&quot;

    def __init__(
        self,
        config: Config,
        max_retries: int = MAX_RETRIES
    ) -&gt; None:
        self._config = config
        self._max_retries = max_retries
        self._cache: dict[str, ProcessResult] = {}

    def process(self, task: Task) -&gt; ProcessResult:
        &quot;&quot;&quot;Process a single task.

        Args:
            task: Task to process.

        Returns:
            ProcessResult with success status and data.

        Raises:
            ValueError: If task is invalid.
        &quot;&quot;&quot;
        if not task.is_valid():
            raise ValueError(f&quot;Invalid task: {task.id}&quot;)

        return self._execute_with_retry(task)

    def _execute_with_retry(self, task: Task) -&gt; ProcessResult:
        &quot;&quot;&quot;Execute task with retry logic.&quot;&quot;&quot;
        for attempt in range(self._max_retries):
            try:
                result = self._execute(task)
                return ProcessResult(success=True, data=result)
            except ConnectionError as e:
                logger.warning(f&quot;Attempt {attempt + 1} failed: {e}&quot;)

        return ProcessResult(success=False, error=&quot;Max retries exceeded&quot;)

    def _execute(self, task: Task) -&gt; dict:
        &quot;&quot;&quot;Execute task processing.&quot;&quot;&quot;
        # Implementation
        return {&quot;processed&quot;: True}
```

## 6. Quick Reference Table

| Category | Convention | Examples |
|----------|-----------|----------|
| **Module files** | `snake_case.py` | `task_manager.py`, `data_utils.py` |
| **Package dirs** | `snake_case/` | `data_processing/`, `ml_models/` |
| **Classes** | `PascalCase` | `TaskManager`, `DataProcessor` |
| **Functions** | `snake_case` | `get_user_data()`, `process_tasks()` |
| **Variables** | `snake_case` | `user_name`, `filtered_items` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `API_URL` |
| **Private** | `_underscore` | `_cache`, `_helper()` |
| **Type vars** | `PascalCase` | `T`, `ItemType`, `KeyType` |
| **Test files** | `test_*.py` | `test_processor.py` |

## 7. Checklist Before Coding

- [ ] Module files use snake_case.py
- [ ] Classes use PascalCase
- [ ] Functions and variables use snake_case
- [ ] Constants use UPPER_SNAKE_CASE
- [ ] Private members use _leading_underscore
- [ ] All functions have type hints (params + return)
- [ ] All public functions have docstrings (Google style)
- [ ] No mutable default arguments (use None)
- [ ] Specific exception handling (no bare except)
- [ ] Imports organized: stdlib, third-party, local

## 8. Common Mistakes

```python
# WRONG: camelCase
def getUserData(userId):
    userName = data[userId]

# CORRECT: snake_case
def get_user_data(user_id: str) -&gt; str:
    user_name = data[user_id]
```

```python
# WRONG: mutable default
def add(item, items=[]):
    items.append(item)

# CORRECT: None default
def add(item: str, items: list | None = None) -&gt; list:
    if items is None:
        items = []
    items.append(item)
```

```python
# WRONG: bare except
try:
    result = fetch()
except:
    pass

# CORRECT: specific exception
try:
    result = fetch()
except ConnectionError as e:
    logger.error(e)
```

```python
# WRONG: no types
def process(data, threshold):
    return [x for x in data if x &gt; threshold]

# CORRECT: full types
def process(data: list[float], threshold: float) -&gt; list[float]:
    return [x for x in data if x &gt; threshold]
```

## 9. ML/Data Science Conventions

For GreyKite, pandas, sklearn projects:

```python
# DataFrame variables: descriptive names
df_raw = pd.read_csv(&quot;data.csv&quot;)      # Not: df, d, data
df_cleaned = clean_data(df_raw)        # Not: df2, clean
df_features = extract_features(df_cleaned)

# Model variables
model_forecast = GreykiteModel()       # Not: m, model
model_classifier = RandomForestClassifier()

# Column names: snake_case strings
df.columns = [&quot;user_id&quot;, &quot;created_at&quot;, &quot;value&quot;]  # Not: userId, CreatedAt

# Function naming for ML
def train_model(df_train: pd.DataFrame) -&gt; Model:
def evaluate_model(model: Model, df_test: pd.DataFrame) -&gt; Metrics:
def generate_forecast(model: Model, horizon: int) -&gt; pd.DataFrame:
```
</section></context><task><metadata><id>task2</id><filePath>/home/cynicus/code/orchestration/.kanban2code/projects/orchestration/phase2-single-task-execution-engine/task2.md</filePath><target-file>/home/cynicus/code/orchestration/.kanban2code/projects/orchestration/phase2-single-task-execution-engine/task2.md</target-file><title>Task 2: Single-Task Execution Engine</title><stage>plan</stage><project>orchestration</project><phase>phase2-single-task-execution-engine</phase><agent>planner</agent><tags><tag>feature</tag><tag>p2</tag></tags><contexts></contexts></metadata><content>
# Task 2: Single-Task Execution Engine

Build the core execution loop: provider abstraction, prompt assembly, tmux sessions, stage dispatch, result evaluation, bounce tracking, and auto-commit. End result: one task can go through plan → code → audit → completed using configured providers.

---

## Unified Goal

Implement a complete single-task execution engine that can take a Kanban2Code task from plan through code to audit and completion. This includes:

1. **Provider abstraction** — A pluggable interface with a working Codex implementation first; other providers arrive in later phases
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
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating &lt; 8 + back to code
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
- [ ] Only stage files listed in the task&apos;s Audit section + task file + architecture.md if changed
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
- [ ] Audit rework detected when rating &lt; 8 and stage: code
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
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating &lt; 8 + back to code
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
- [ ] Audit rework detected when rating &lt; 8 and stage: code
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
- [ ] Only stage files listed in the task&apos;s Audit section + task file + architecture.md if changed
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

Phase 2: Single-Task Execution Engine</content></task></system>



Gemini flash task after planning
<system><task><metadata><id>task2</id><filePath>/home/cynicus/code/orchestration/.kanban2code/projects/orchestration/phase2-single-task-execution-engine/task2.md</filePath><target-file>/home/cynicus/code/orchestration/.kanban2code/projects/orchestration/phase2-single-task-execution-engine/task2.md</target-file><title>Task 2: Single-Task Execution Engine</title><stage>code</stage><project>orchestration</project><phase>phase2-single-task-execution-engine</phase><agent>coder</agent><tags><tag>feature</tag><tag>p2</tag></tags><contexts></contexts></metadata><content>
# Task 2: Single-Task Execution Engine

Build the core execution loop: provider abstraction, prompt assembly, tmux sessions, stage dispatch, result evaluation, bounce tracking, and auto-commit. End result: one task can go through plan → code → audit → completed using configured providers.

---

## Unified Goal

Implement a complete single-task execution engine that can take a Kanban2Code task from plan through code to audit and completion. This includes:

1. **Provider abstraction** — A pluggable interface with a working Codex implementation first; other providers arrive in later phases
2. **Prompt assembly** — Injecting actual file contents into prompts, never placeholders
3. **tmux session management** — Running providers in visible, monitorable sessions with timeout enforcement
4. **Stage dispatch and evaluation** — Running stages and detecting success/failure from frontmatter transitions
5. **Bounce tracking and run loop** — Processing tasks through stages with audit bounce limits and transport retries
6. **Auto-commit** — Surgical git commits after successful audit passes

---

## Refined Prompt
Objective: Implement a complete single-task execution engine for Kanban2Code.

Implementation approach:
1. Create a pluggable provider system with a `BaseProvider` abstract class and a `CodexProvider` implementation.
2. Build a prompt assembler that injects actual file contents (role, ai-guide, task, contexts) into prompts.
3. Implement a tmux session manager using `libtmux` to run and monitor provider CLIs with timeout enforcement.
4. Create a stage dispatcher and result evaluator that manages transitions between plan, code, and audit stages.
5. Implement a core run loop with audit bounce tracking (max 2 bounces) and transport retries (max 3 attempts).
6. Add surgical auto-commit logic that only stages files listed in the task&apos;s Audit section after a successful audit.

Key decisions:
- **Provider Abstraction**: Use an abstract base class to allow for future providers (Gemini, Claude, etc.).
- **tmux Sessions**: Use visible, named tmux sessions for observability and reliable process management.
- **Frontmatter Truth**: Always use task frontmatter as the authoritative source for stage and agent status.
- **Surgical Commits**: Strictly avoid `git add .` to prevent accidental staging of unrelated changes.

Edge cases:
- Missing context files: Raise clear errors rather than silent omission.
- Timeouts (wall/idle): Cleanly kill tmux sessions and report as transport failures.
- Max bounces exceeded: Generate a human-readable handoff README and stop execution for that task.

## Context

### File Tree (scoped)
```
src/orchestrator/
├── providers/           # &lt;- create
│   ├── __init__.py      # &lt;- create
│   ├── base.py          # &lt;- create
│   └── codex.py         # &lt;- create
├── prompts.py           # &lt;- create
├── sessions.py          # &lt;- create
├── dispatcher.py        # &lt;- create
├── evaluator.py         # &lt;- create
├── state.py             # &lt;- modify
└── commits.py           # &lt;- create
```

### Architecture Excerpts
From `orchestrator.md`:
- &quot;Task frontmatter is the source of truth for stage, agent, bounces, tags, contexts.&quot;
- &quot;Orchestration should be implemented as code, not as vibes.&quot;
- &quot;Prompt assembly must use real file contents: role file, ai-guide.md, task file, any explicitly required context files.&quot;
- &quot;Max failed audit cycles per task = 2.&quot;
- &quot;If audit is accepted: commit immediately. Only stage files listed in ## Audit + task file + architecture.md if changed.&quot;

### Skill Excerpts
From `skills/python-core-skills.md`:
- &quot;Enforce PEP 8 naming: snake_case for functions/variables, PascalCase for classes.&quot;
- &quot;Use type hints on all functions and docstrings on all public functions (Google style).&quot;
- &quot;Use `None` as default for mutable arguments, not `[]` or `{}`.&quot;
- &quot;Specific exception handling: no bare `except:` clauses.&quot;

### Code Excerpts
`src/orchestrator/models.py:101-114` (OrchestratorConfig):
```python
@dataclass(slots=True)
class OrchestratorConfig:
    &quot;&quot;&quot;Top-level typed configuration for the orchestrator.&quot;&quot;&quot;
    schema_version: int = 1
    providers: dict[str, ProviderAliasConfig] = field(default_factory=dict)
    stage_routing: dict[str, PlanStageRoutingConfig | CodeStageRoutingConfig | AuditStageRoutingConfig] = field(default_factory=dict)
    timeouts: dict[str, StageTimeoutConfig] = field(default_factory=dict)
    retry_policy: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)
    # ...
```

`src/orchestrator/models.py:117-130` (TaskSnapshot):
```python
@dataclass(slots=True)
class TaskSnapshot:
    &quot;&quot;&quot;Typed snapshot of a Kanban2Code task file.&quot;&quot;&quot;
    path: Path = field(default_factory=lambda: Path(&quot;.&quot;))
    task_id: str = &quot;&quot;
    stage: str = &quot;&quot;
    agent: str = &quot;&quot;
    bounces: int = 0
    # ...
```

`src/orchestrator/state.py:84-100` (load_run_state):
```python
def load_run_state(path: Path) -&gt; RunState:
    &quot;&quot;&quot;Load a run state from JSON.&quot;&quot;&quot;
    raw_state = json.loads(path.read_text(encoding=&quot;utf-8&quot;))
    task_states = {
        task_path: TaskRunState(**task_state)
        for task_path, task_state in raw_state.get(&quot;task_states&quot;, {}).items()
    }
    # ...
```

### Dependency Graph
- `Dispatcher` -&gt; `BaseProvider`, `PromptAssembler`, `SessionManager`, `Evaluator`, `TaskSnapshot`
- `CodexProvider` -&gt; `BaseProvider`, `libtmux`, `subprocess`
- `AutoCommit` -&gt; `Git CLI`, `TaskSnapshot`

### Patterns to Follow
- Use `pathlib.Path` for all file operations.
- Follow the `load_config` pattern for parsing provider configurations from Markdown files.
- Use `logging` for execution events, following the `RunEvent` model.

### Test Patterns
- Mock `subprocess` and `libtmux` for provider and session tests.
- Use temporary directories for testing file mutations and Git commits.

### Gotchas
- `libtmux` versions: Ensure compatibility with version `0.46+` as listed in `pyproject.toml`.
- Git staging: Never use `git add .`. Always stage specific files.

### Scope Boundaries
This task covers the entire core execution loop for a single task. It should NOT touch account rotation rules (Phase 3) or multi-task concurrency (Phase 4).

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
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating &lt; 8 + back to code
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
- [ ] Only stage files listed in the task&apos;s Audit section + task file + architecture.md if changed
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
- [ ] Audit rework detected when rating &lt; 8 and stage: code
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
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating &lt; 8 + back to code
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
- [ ] Audit rework detected when rating &lt; 8 and stage: code
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
- [ ] Only stage files listed in the task&apos;s Audit section + task file + architecture.md if changed
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

Phase 2: Single-Task Execution Engine</content></task></system>

###
GLM 5  plan
<system><task><metadata><id>task2</id><filePath>/home/cynicus/code/orchestration/.kanban2code/projects/orchestration/phase2-single-task-execution-engine/task2.md</filePath><target-file>/home/cynicus/code/orchestration/.kanban2code/projects/orchestration/phase2-single-task-execution-engine/task2.md</target-file><title>Task 2: Single-Task Execution Engine</title><stage>code</stage><project>orchestration</project><phase>phase2-single-task-execution-engine</phase><agent>coder</agent><tags><tag>feature</tag><tag>p2</tag></tags><contexts></contexts></metadata><content>
# Task 2: Single-Task Execution Engine

Build the core execution loop: provider abstraction, prompt assembly, tmux sessions, stage dispatch, result evaluation, bounce tracking, and auto-commit. End result: one task can go through plan → code → audit → completed using configured providers.

---

## Unified Goal

Implement a complete single-task execution engine that can take a Kanban2Code task from plan through code to audit and completion. This includes:

1. **Provider abstraction** — A pluggable interface with a working Codex implementation first; other providers arrive in later phases
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
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating &lt; 8 + back to code
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
- [ ] Only stage files listed in the task&apos;s Audit section + task file + architecture.md if changed
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
- [ ] Audit rework detected when rating &lt; 8 and stage: code
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
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating &lt; 8 + back to code
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
- [ ] Audit rework detected when rating &lt; 8 and stage: code
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
- [ ] Only stage files listed in the task&apos;s Audit section + task file + architecture.md if changed
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

---

## Refined Prompt

Objective: Build a complete single-task execution engine that processes Kanban2Code tasks through plan → code → audit → completed using provider CLIs in tmux sessions.

Implementation approach:
1. **Provider abstraction (2.1)**: Create `BaseProvider` ABC with `invoke()` method returning `InvocationResult`. Implement `CodexProvider` that loads config from `.kanban2code/_providers/*.md` frontmatter, validates binary on PATH, builds CLI command, and executes via subprocess.
2. **Prompt assembler (2.2)**: Build `assemble_prompt()` that reads role file, ai-guide.md, task file, and context files from task frontmatter — injecting actual contents verbatim. Include run metadata header with run ID, repo root, task path, stage, and expected transition.
3. **tmux session manager (2.3)**: Use `libtmux` to create named sessions (`orch-{run_id}-{task_id}-{stage}`), run provider commands, poll for process exit and task file mutation, enforce wall/idle timeouts with SIGTERM→SIGKILL escalation.
4. **Stage dispatcher and evaluator (2.4)**: Build `Dispatcher` class that orchestrates a single stage: take before snapshot, assemble prompt, select provider from config, spawn session, wait, take after snapshot, evaluate transition. Build `Evaluator` that compares snapshots to determine result kind (success, quality_failure, transport_failure, blocked).
5. **Run loop and bounce tracking (2.5)**: Implement `RunLoop` class that processes ordered queue, tracks audit bounces per task in `TaskRunState`, enforces max 2 bounces before handoff, retries transport failures up to 3 times, persists state after each stage, and supports `continue` from saved state.
6. **Auto-commit (2.6)**: Build `commit_after_audit()` that parses Audit section for file list, stages only those files plus task file plus architecture.md if changed, formats commit message per spec, and optionally creates milestone branches.

Key decisions:
- **libtmux over raw subprocess**: Use `libtmux` library for session management — provides Pythonic API for creating, monitoring, and killing tmux sessions with proper cleanup.
- **Snapshot-based evaluation**: Compare `TaskSnapshot` before/after to detect stage transitions — avoids parsing provider output and relies on the authoritative frontmatter.
- **Config-driven provider selection**: Provider aliases in `config.json` map to `.kanban2code/_providers/*.md` files — allows per-stage provider config without code changes.
- **Separate InvocationResult from StageResult**: `InvocationResult` captures CLI execution (exit code, timeout, output), `StageResult` captures semantic outcome (success, quality_failure, transport_failure, blocked).

Edge cases:
- Provider binary missing on PATH: raise clear error before attempting invocation.
- Context file missing: raise `PromptAssemblyError` with file path — never silently omit.
- Session hangs: enforce wall timeout with SIGTERM→SIGKILL escalation after 5-second grace period.
- Task file not mutated after provider exits: treat as transport failure, retry.
- Audit rating missing or unparsable: default to 0 (triggers rework).
- Git repository dirty: warn but proceed with commit (do not block).
- Run state file corrupted: start fresh run, log warning.

---

## Context

### File Tree (scoped)

```
src/orchestrator/
├── __init__.py                    # ← read-only reference (exports)
├── cli.py                         # ← modify (wire run/continue commands)
├── config.py                      # ← read-only reference
├── logger.py                      # ← read-only reference
├── models.py                      # ← modify (add InvocationResult, StageResult, ProviderConfig)
├── scanner.py                     # ← read-only reference
├── state.py                       # ← modify (add handoff readme generation)
├── prompts.py                     # ← create
├── sessions.py                    # ← create
├── dispatcher.py                  # ← create
├── evaluator.py                   # ← create
├── commits.py                     # ← create
└── providers/
    ├── __init__.py                # ← create
    ├── base.py                    # ← create
    └── codex.py                   # ← create

.kanban2code/
├── _providers/
│   ├── codex.md                   # ← read-only reference (provider config format)
│   ├── codex-high.md              # ← read-only reference
│   └── codex-low.md               # ← read-only reference
├── _context/
│   └── ai-guide.md                # ← read-only reference (prompt assembly context)
└── projects/orchestration/
    └── phase1-core-infrastructure/
        └── task1.md               # ← read-only reference (sibling phase context)

tests/
├── test_config.py                 # ← read-only reference (test patterns)
├── test_prompts.py                # ← create
├── test_sessions.py               # ← create
├── test_providers.py              # ← create
├── test_dispatcher.py             # ← create
├── test_evaluator.py              # ← create
└── test_commits.py                # ← create
```

### Architecture Excerpts

From `orchestrator.md` (project root):
- **Task frontmatter is source of truth**: Orchestrator reads but never writes frontmatter; agents update their own task state.
- **MVP execution scope**: plan → code → audit only.
- **Max 2 audit bounces**: Third cycle stops and escalates to Dan.
- **No silent waiting**: Every blocked/stalled state must be logged and notified.
- **Safe concurrency only**: Tasks touching same files must not run in parallel (Phase 4).
- **Auto-commit after audit pass**: Only stage files from Audit section + task file + architecture.md.

From `config.json`:
- `providers.{planner,coder,auditor}` map to provider aliases (e.g., `codex`, `codex-high`).
- `stage_routing.{plan,code,audit}` defines success transitions and required sections.
- `timeouts.{plan,code,audit}` defines wall_seconds and idle_seconds per stage.
- `retry_policy.transport_max_attempts = 3`, `audit_failure_cycles_before_handoff = 2`.

From `.kanban2code/_providers/codex.md`:
```yaml
cli: codex
subcommand: exec
model: gpt-5.3-codex
unattended_flags: [&apos;--yolo&apos;]
output_flags: [&apos;--json&apos;]
prompt_style: stdin
config_overrides:
  model_reasoning_effort: medium
```

### Skill Excerpts

From `skills/python-core-skills`:
- Use `snake_case` for modules, functions, variables (`invoke_provider`, `build_command`).
- Use `PascalCase` for classes (`BaseProvider`, `CodexProvider`, `InvocationResult`).
- All public functions must have type hints and Google-style docstrings.
- Use `from __future__ import annotations` in all modules.
- Avoid mutable default arguments — use `None` defaults.
- Private members use `_leading_underscore`.
- Specific exception handling — no bare `except:`.

### Code Excerpts

**models.py:TaskSnapshot** (lines 97-124) — Core dataclass for task state, used by evaluator for before/after comparison:
```python
@dataclass(slots=True)
class TaskSnapshot:
    path: Path = field(default_factory=lambda: Path(&quot;.&quot;))
    task_id: str = &quot;&quot;
    project: str = &quot;&quot;
    stage: str = &quot;&quot;
    agent: str = &quot;&quot;
    bounces: int = 0
    tags: list[str] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)
    # ... __post_init__ normalizes stage/agent to lowercase
```

**models.py:TaskRunState** (lines 136-144) — Tracks per-task execution state including audit_failures counter:
```python
@dataclass(slots=True)
class TaskRunState:
    status: str = &quot;pending&quot;
    last_stage: str | None = None
    last_error: str | None = None
    audit_failures: int = 0
    transport_attempts: dict[str, int] = field(default_factory=dict)
```

**config.py:load_config** (lines 24-53) — Pattern for loading typed config from JSON, use similar pattern for provider config:
```python
def load_config(path: str | Path = &quot;config.json&quot;) -&gt; OrchestratorConfig:
    config_path = Path(path)
    raw_text = config_path.read_text(encoding=&quot;utf-8&quot;)
    raw_config = json.loads(raw_text)
    return OrchestratorConfig(...)
```

**scanner.py:split_frontmatter** (lines 20-42) — Reuse for parsing provider .md files:
```python
FRONTMATTER_PATTERN = re.compile(r&quot;\A---\s*\r?\n(?P&lt;metadata&gt;.*?)(?:\r?\n)---\s*&quot;, re.DOTALL)
def split_frontmatter(text: str) -&gt; tuple[dict[str, object], str]:
    # Returns parsed metadata dict and body string
```

**state.py:save_run_state / load_run_state** (lines 44-82) — Pattern for persisting run state to JSON:
```python
def save_run_state(path: Path, run_state: RunState) -&gt; None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(run_state), indent=2) + &quot;\n&quot;)
```

**logger.py:JsonlLogger.append** (lines 22-42) — Pattern for structured logging:
```python
def append(self, event_type: str, message: str, **extras: object) -&gt; RunEvent:
    event = RunEvent(timestamp=_utc_now_iso(), type=event_type, message=message, extras=dict(extras))
    # Write to JSONL file
```

### Dependency Graph

```
providers/base.py
    └── (no internal deps)

providers/codex.py
    ├── providers/base.py
    ├── models.py (InvocationResult, ProviderConfig)
    └── scanner.py (split_frontmatter for provider .md parsing)

prompts.py
    ├── models.py (TaskSnapshot)
    └── config.py (OrchestratorConfig for context paths)

sessions.py
    ├── libtmux (external)
    └── models.py (SessionConfig, SessionResult)

evaluator.py
    ├── models.py (TaskSnapshot, StageResult)
    └── config.py (stage_routing config)

dispatcher.py
    ├── providers/base.py
    ├── prompts.py
    ├── sessions.py
    ├── evaluator.py
    ├── models.py (RunState, TaskRunState)
    ├── state.py (save_run_state, append_recent_event)
    └── logger.py (JsonlLogger)

commits.py
    └── (subprocess for git commands)

cli.py (modify)
    ├── dispatcher.py
    └── state.py (load_run_state for continue command)
```

### Patterns to Follow

- **Dataclass models**: All new models use `@dataclass(slots=True)` with `from __future__ import annotations`.
- **Config loading**: Use `Path.read_text()` + `json.loads()` + manual validation (no Pydantic).
- **Error handling**: Define custom exceptions (`ProviderError`, `PromptAssemblyError`, `SessionError`) inheriting from `Exception`.
- **Logging**: Use `JsonlLogger` for structured events, log stage transitions and errors.
- **Tests**: Use `pytest` with `tmp_path` fixture for file operations, mock external dependencies.

### Test Patterns

From `tests/test_config.py`:
- Use `tmp_path` fixture for temporary config files.
- Test happy path, missing keys, invalid types, and integration with shipped config.
- Use `pytest.raises(ConfigError, match=r&quot;pattern&quot;)` for error assertions.

From `tests/test_scanner.py`:
- Create sample task files in temp directory structure.
- Test discovery, exclusion, parsing, and edge cases.

### Gotchas

- **libtmux Server attachment**: `libtmux.Server()` creates/attaches to tmux server — ensure cleanup in tests with `server.kill_server()`.
- **Codex CLI `--json` flag**: Changes output format; may need to parse JSON for structured results.
- **Frontmatter normalization**: `TaskSnapshot.__post_init__` lowercases stage/agent — evaluator must compare normalized values.
- **Session naming**: Must be unique per invocation; include run_id, task_id, stage, and timestamp or counter.
- **Git operations**: Run from repo root (`Path.cwd()` or detect via `git rev-parse --show-toplevel`).
- **Timeout handling**: libtmux `session.attached_window.attached_pane` for process monitoring; wall timeout vs idle timeout are different.

### Scope Boundaries

This task (Phase 2) should NOT touch:
- **Account rotation** (Phase 3): `accounts.py`, account switching logic.
- **Additional providers** (Phase 3): Claude, Gemini, Qwen providers.
- **Model routing/fallback** (Phase 3): Fallback chain logic in dispatcher.
- **Concurrent scheduling** (Phase 4): `scheduler.py`, multi-threaded dispatch.
- **Conflict detection** (Phase 4): File-level conflict analysis.
- **Telegram notifications** (Phase 5): `notifier.py`.
- **Smoke tests** (Phase 5): `smoke.py`.
- **Memory system** (Phase 6): `memory.py`.

Phase 1 (task1.md) is complete — scaffold, config, scanner, logger, state are available for use.</content></task></system>