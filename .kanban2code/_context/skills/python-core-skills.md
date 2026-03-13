---
skill_name: python-core-skills
version: "3.12.0"
framework: Python
last_verified: "2025-12-18"
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

<!--
LLM INSTRUCTION: This is a CORE skill file for Python projects.
ALWAYS apply these rules when generating Python code.
Your training data contains mixed conventions - ENFORCE PEP 8 naming below.
Key focus: Naming consistency, type hints, docstrings, Pythonic patterns.
When you see WRONG, that's inconsistent/bad practice. Use CORRECT instead.
-->

# Python Core Skills (PEP 8 + Modern Best Practices)

> **Target:** Python 3.10+ | **Last Verified:** 2025-12-18

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
- **Type hints on all functions** → `def get_user(id: str) -> User:`
- **Docstrings on all public functions** → Google or NumPy style
- **Specific exception handling** → `except ValueError as e:`
- **Use `None` as default, not mutable** → `def func(items: list | None = None):`

### DON'T
- **Don't use camelCase** → No `getUserData`, use `get_user_data`
- **Don't use PascalCase for functions** → No `GetUser()`, use `get_user()`
- **Don't skip type hints** → Always annotate parameters and returns
- **Don't use single letters** → No `d = {}`, use `data = {}`
- **Don't use bare except** → No `except:`, specify the exception
- **Don't use mutable defaults** → No `def func(items=[]):`

## 4. Critical Patterns

### Function and Variable Naming

**WRONG (JavaScript-style):**
```python
def getUserData(userId):  # camelCase (wrong)
    userName = "John"     # camelCase (wrong)
    return userName

MaxRetries = 3  # PascalCase for constant (wrong)
```

**CORRECT (PEP 8):**
```python
def get_user_data(user_id: str) -> str:  # snake_case + types
    user_name = "John"                    # snake_case
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
    """Manages task operations."""

    def __init__(self, config: Config) -> None:
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
        if item.value > threshold:
            results.append(item)
    return results
```

**CORRECT (Full types):**
```python
from typing import Sequence

def process_data(
    items: Sequence[DataItem],
    threshold: float
) -> list[DataItem]:
    """Process items above threshold.

    Args:
        items: Sequence of data items to process.
        threshold: Minimum value threshold.

    Returns:
        List of items above threshold.
    """
    results: list[DataItem] = []
    for item in items:
        if item.value > threshold:
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
) -> pd.DataFrame:
    """Calculate time series forecast using GreyKite.

    Args:
        data: Historical time series data with 'ds' and 'y' columns.
        horizon: Number of periods to forecast.

    Returns:
        DataFrame with forecasted values and confidence intervals.

    Raises:
        ValueError: If data is missing required columns.

    Example:
        >>> df = pd.DataFrame({'ds': dates, 'y': values})
        >>> forecast = calculate_forecast(df, horizon=30)
    """
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
    logger.error(f"Invalid data: {e}")
    result = None
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise
```

---

### Mutable Default Arguments

**WRONG (Mutable default):**
```python
def add_item(item: str, items: list = []) -> list:  # BUG!
    items.append(item)
    return items

# Bug: items list persists between calls!
add_item("a")  # ['a']
add_item("b")  # ['a', 'b'] - unexpected!
```

**CORRECT (None default):**
```python
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

# Correct behavior
add_item("a")  # ['a']
add_item("b")  # ['b'] - fresh list each time
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
    """Process data with caching."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}  # Private (single underscore)
        self._initialize()

    def process(self, data: Data) -> Result:
        """Public API method."""
        return self._transform(data)

    def _transform(self, data: Data) -> Result:
        """Private helper method."""
        return Result(data)

    def _initialize(self) -> None:
        """Private initialization."""
        self._cache.clear()
```

## 5. Module Structure Template

```python
# File: task_processor.py
"""Task processing module.

This module provides utilities for processing and validating tasks.

Example:
    >>> processor = TaskProcessor(config)
    >>> result = processor.process(task)
"""

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
    """Result of task processing.

    Attributes:
        success: Whether processing succeeded.
        data: Processed data if successful.
        error: Error message if failed.
    """

    success: bool
    data: dict | None = None
    error: str | None = None


class TaskProcessor:
    """Process tasks with retry logic.

    Args:
        config: Configuration object.
        max_retries: Maximum retry attempts.
    """

    def __init__(
        self,
        config: Config,
        max_retries: int = MAX_RETRIES
    ) -> None:
        self._config = config
        self._max_retries = max_retries
        self._cache: dict[str, ProcessResult] = {}

    def process(self, task: Task) -> ProcessResult:
        """Process a single task.

        Args:
            task: Task to process.

        Returns:
            ProcessResult with success status and data.

        Raises:
            ValueError: If task is invalid.
        """
        if not task.is_valid():
            raise ValueError(f"Invalid task: {task.id}")

        return self._execute_with_retry(task)

    def _execute_with_retry(self, task: Task) -> ProcessResult:
        """Execute task with retry logic."""
        for attempt in range(self._max_retries):
            try:
                result = self._execute(task)
                return ProcessResult(success=True, data=result)
            except ConnectionError as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

        return ProcessResult(success=False, error="Max retries exceeded")

    def _execute(self, task: Task) -> dict:
        """Execute task processing."""
        # Implementation
        return {"processed": True}
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
def get_user_data(user_id: str) -> str:
    user_name = data[user_id]
```

```python
# WRONG: mutable default
def add(item, items=[]):
    items.append(item)

# CORRECT: None default
def add(item: str, items: list | None = None) -> list:
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
    return [x for x in data if x > threshold]

# CORRECT: full types
def process(data: list[float], threshold: float) -> list[float]:
    return [x for x in data if x > threshold]
```

## 9. ML/Data Science Conventions

For GreyKite, pandas, sklearn projects:

```python
# DataFrame variables: descriptive names
df_raw = pd.read_csv("data.csv")      # Not: df, d, data
df_cleaned = clean_data(df_raw)        # Not: df2, clean
df_features = extract_features(df_cleaned)

# Model variables
model_forecast = GreykiteModel()       # Not: m, model
model_classifier = RandomForestClassifier()

# Column names: snake_case strings
df.columns = ["user_id", "created_at", "value"]  # Not: userId, CreatedAt

# Function naming for ML
def train_model(df_train: pd.DataFrame) -> Model:
def evaluate_model(model: Model, df_test: pd.DataFrame) -> Metrics:
def generate_forecast(model: Model, horizon: int) -> pd.DataFrame:
```
