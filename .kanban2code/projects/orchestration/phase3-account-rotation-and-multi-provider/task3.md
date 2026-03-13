---
stage: audit
tags: [feature, p3]
agent: auditor
contexts: [skills/python-core-skills]
---

# Task 3: Account Rotation and Multi-Provider

Add account management for Codex and additional CLI providers for Claude, Gemini, and Qwen. Add model routing configuration with fallback chains.

---

## Unified Goal

Implement the multi-provider/account layer with explicit stage routing and fallback chains:

1. **Account manager** — Rotate Codex auth tokens per task, with health checks and fallback
2. **Claude CLI provider** — Support for Anthropic models (Opus, Sonnet, Haiku)
3. **Gemini and Qwen CLI providers** — Support for Google Gemini and Qwen CLI with model aliases
4. **Model routing with fallback chains** — Per-stage provider preferences with ordered fallback

---

## Unified Task List

| # | Subtask | Description | Files |
|---|---------|-------------|-------|
| 3.1 | Account manager with Codex rotation | Implement account pool, rotation per task, health checks, and fallback | `accounts.py` |
| 3.2 | Claude CLI provider | Implement `ClaudeProvider` for Anthropic models | `providers/claude.py` |
| 3.3 | Gemini and Qwen CLI providers | Implement `GeminiProvider` and `QwenProvider` | `providers/gemini.py`, `providers/qwen.py` |
| 3.4 | Model routing with fallback chains | Per-stage provider preferences with ordered fallback | `dispatcher.py` (modify), `config.json` (modify) |

---

## Unified Definition of Done

### Account Management
- [x] Account pool loaded from config (list of account names)
- [x] Rotation: pick next account per task, keep same through bounces
- [x] Switch mechanism: symlink `~/.codex/auth.json` to `~/.codex/accounts/TARGET.json`
- [x] Health check: run `codex login status` after switch, parse result
- [x] Round-robin fallback: if account fails, try next; if all fail, escalate
- [x] Log which account is active for each task

### Claude Provider
- [x] `ClaudeProvider` implements `BaseProvider`
- [x] Loads config from `.kanban2code/_providers/opus.md`, `sonnet.md`, `haiku.md`
- [x] Builds correct `claude` CLI command with model, flags, and prompt
- [x] Supports stdin prompt delivery
- [x] Captures output for evaluation

### Gemini and Qwen Providers
- [x] `GeminiProvider` implements `BaseProvider` for Google Gemini CLI
- [x] `QwenProvider` implements `BaseProvider` for Qwen CLI
- [x] Each loads config from its respective `_providers/*.md` file
- [x] Qwen supports model aliases (kimi-k2.5, minimax, etc.)
- [x] Gemini supports model name format (`gemini-3-flash-preview`)

### Model Routing
- [x] Config defines provider preference per stage with ordered fallback list
- [x] Planning: Gemini Flash 3.0/3.1 primary (not 2.5) → Qwen Kimi 2.5 → Haiku / MiniMax / other Qwen fallback
- [x] Coding: Codex 5.4 medium → Sonnet 4.6 → GLM via Qwen CLI
- [x] Auditing: Opus 4.6 thinking → Codex 5.4 xhigh
- [x] On provider failure, automatically try next in fallback chain
- [x] Log which provider/model was actually used

---

## Execution Order / Dependencies

```
3.1 Account manager ──────────────────────────────────────────────┐
                                                                  │
3.2 Claude provider ─────┐                                       │
                         │                                       │
3.3 Gemini/Qwen providers├──► 3.4 Model routing (integrates all) ─┘
                         │           │
                         └───────────┘
```

**Dependencies:**
- **3.1, 3.2, 3.3** can be built in parallel (each is an independent provider/module)
- **3.4** depends on all providers being available to configure routing

**Recommended build order:**
1. Build 3.1, 3.2, 3.3 in parallel or sequentially
2. Build 3.4 (integrates all providers into routing system)

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/orchestrator/accounts.py` | create | Account rotation and health checking |
| `src/orchestrator/providers/claude.py` | create | Claude CLI implementation |
| `src/orchestrator/providers/gemini.py` | create | Gemini CLI implementation |
| `src/orchestrator/providers/qwen.py` | create | Qwen CLI implementation |
| `src/orchestrator/dispatcher.py` | modify | Add fallback chain logic |
| `config.json` | modify | Add fallback chain configuration |

---

## Tests

### Account Manager Tests
- [ ] Account rotation picks the next account in pool order
- [ ] Same account persists through bounces of a task
- [ ] Failed account triggers fallback to next
- [ ] All accounts failing triggers escalation
- [ ] Health check parses codex login status output

### Claude Provider Tests
- [ ] ClaudeProvider builds correct command for opus/sonnet/haiku
- [ ] ClaudeProvider handles stdin prompt delivery
- [ ] Missing claude binary detected gracefully

### Gemini/Qwen Provider Tests
- [ ] GeminiProvider builds correct command with model name
- [ ] QwenProvider builds correct command with model alias
- [ ] Both detect missing binary gracefully

### Model Routing Tests
- [ ] Primary provider selected for each stage
- [ ] Fallback triggered on provider failure
- [ ] All fallbacks exhausted triggers escalation
- [ ] Correct provider/model logged for each invocation

---

## Model Routing Configuration

### Stage Preferences

| Stage | Primary | Fallback 1 | Fallback 2 |
|-------|---------|------------|------------|
| Planning | Gemini Flash 3.0 / 3.1 | Qwen Kimi 2.5 | Haiku / MiniMax / other Qwen fallback |
| Coding | Codex 5.4 medium | Sonnet 4.6 | GLM via Qwen CLI |
| Auditing | Opus 4.6 thinking | Codex 5.4 xhigh | — |

### Account Rotation Pattern

```bash
# Switch mechanism
ln -sf ~/.codex/accounts/TARGET.json ~/.codex/auth.json
echo "TARGET" > ~/.codex/current
codex login status
```

**Account pool example:** personal, work, home, karlas, estela, annual, LanguageLine

**Rotation rules:**
- Rotate once per task (not per stage)
- Keep same account through bounces for that task
- Verify login after switching
- If account fails, try next in round-robin
- If all fail, escalate

---

## Original Source Content

The sections below contain the original task definitions preserved for reference.

---

### Task 3.1: Account manager with Codex rotation

#### Goal

Implement the account manager that rotates Codex auth tokens per task.

#### Definition of Done

- [ ] Account pool loaded from config (list of account names)
- [ ] Rotation: pick next account per task, keep same through bounces
- [ ] Switch mechanism: symlink `~/.codex/auth.json` to `~/.codex/accounts/TARGET.json`
- [ ] Health check: run `codex login status` after switch, parse result
- [ ] Round-robin fallback: if account fails, try next; if all fail, escalate
- [ ] Log which account is active for each task

#### Files

- `src/orchestrator/accounts.py` - create - account rotation and health checking

#### Tests

- [ ] Account rotation picks the next account in pool order
- [ ] Same account persists through bounces of a task
- [ ] Failed account triggers fallback to next
- [ ] All accounts failing triggers escalation
- [ ] Health check parses codex login status output

#### Context

Phase 3: Account Rotation and Multi-Provider

---

### Task 3.2: Claude CLI provider

#### Goal

Implement the Claude CLI provider for Anthropic models.

#### Definition of Done

- [ ] `ClaudeProvider` implements `BaseProvider`
- [ ] Loads config from `.kanban2code/_providers/opus.md`, `sonnet.md`, `haiku.md`
- [ ] Builds correct `claude` CLI command with model, flags, and prompt
- [ ] Supports stdin prompt delivery
- [ ] Captures output for evaluation

#### Files

- `src/orchestrator/providers/claude.py` - create - Claude CLI implementation

#### Tests

- [ ] ClaudeProvider builds correct command for opus/sonnet/haiku
- [ ] ClaudeProvider handles stdin prompt delivery
- [ ] Missing claude binary detected gracefully

#### Context

Phase 3: Account Rotation and Multi-Provider

---

### Task 3.3: Gemini and Qwen CLI providers

#### Goal

Implement the Gemini and Qwen CLI providers.

#### Definition of Done

- [ ] `GeminiProvider` implements `BaseProvider` for Google Gemini CLI
- [ ] `QwenProvider` implements `BaseProvider` for Qwen CLI
- [ ] Each loads config from its respective `_providers/*.md` file
- [ ] Qwen supports model aliases (kimi-k2.5, minimax, etc.)
- [ ] Gemini supports model name format (`gemini-3-flash-preview`)

#### Files

- `src/orchestrator/providers/gemini.py` - create - Gemini CLI implementation
- `src/orchestrator/providers/qwen.py` - create - Qwen CLI implementation

#### Tests

- [ ] GeminiProvider builds correct command with model name
- [ ] QwenProvider builds correct command with model alias
- [ ] Both detect missing binary gracefully

#### Context

Phase 3: Account Rotation and Multi-Provider

---

### Task 3.4: Model routing with fallback chains

#### Goal

Implement model routing and ordered fallback chains in the dispatcher.

#### Definition of Done

- [ ] Config defines provider preference per stage with ordered fallback list
- [ ] Planning: Gemini Flash 3.0/3.1 primary (not 2.5) → Qwen Kimi 2.5 → Haiku / MiniMax / other Qwen fallback
- [ ] Coding: Codex 5.4 medium → Sonnet 4.6 → GLM via Qwen CLI
- [ ] Auditing: Opus 4.6 thinking → Codex 5.4 xhigh
- [ ] On provider failure, automatically try next in fallback chain
- [ ] Log which provider/model was actually used

#### Files

- `src/orchestrator/dispatcher.py` - modify - add fallback chain logic
- `config.json` - modify - add fallback chain configuration

#### Tests

- [ ] Primary provider selected for each stage
- [ ] Fallback triggered on provider failure
- [ ] All fallbacks exhausted triggers escalation
- [ ] Correct provider/model logged for each invocation

#### Context

Phase 3: Account Rotation and Multi-Provider

---

## Refined Prompt

Objective: Implement multi-provider orchestration with account rotation and fallback chains.

Implementation approach:
1. Create `accounts.py` with `AccountManager` class for Codex auth token rotation via symlinks
2. Create `ClaudeProvider`, `GeminiProvider`, `QwenProvider` following `CodexProvider` pattern
3. Extend `config.json` with `fallback_chains` per stage, update `models.py` with new config types
4. Modify `dispatcher.py` to iterate through fallback chain on provider failure
5. Update `providers/__init__.py` to export new providers

Key decisions:
- **Provider pattern**: Each provider inherits from `BaseProvider`, loads config from `_providers/*.md` frontmatter
- **Fallback chain**: Ordered list of provider aliases per stage; on failure, try next; all exhausted → handoff
- **Account rotation**: Round-robin per task, symlink `~/.codex/auth.json`, health check via `codex login status`
- **Prompt delivery**: Claude uses `--prompt` flag style; Gemini/Qwen use positional or flag based on `prompt_style` in config

Edge cases:
- Missing CLI binary: Return `InvocationResult(ok=False, error_message="...not available on PATH")`
- Account health check failure: Try next account in pool; all fail → escalate
- Provider config missing: Raise `ProviderError` with clear message
- Empty fallback chain: Use primary provider only, no fallback

---

## Context

### File Tree (scoped)

```
src/orchestrator/
├── accounts.py                    # ← create
├── dispatcher.py                  # ← modify
├── models.py                      # ← modify (add fallback chain config types)
├── config.py                      # ← modify (add fallback chain parsing)
├── providers/
│   ├── __init__.py               # ← modify (export new providers)
│   ├── base.py                   # ← read-only reference
│   ├── codex.py                  # ← read-only reference (pattern to follow)
│   ├── claude.py                 # ← create
│   ├── gemini.py                 # ← create
│   └── qwen.py                   # ← create

.kanban2code/_providers/
├── opus.md                       # ← read-only reference
├── sonnet.md                     # ← read-only reference
├── haiku.md                      # ← read-only reference
├── kimi.md                       # ← read-only reference
├── glm.md                        # ← read-only reference

config.json                       # ← modify (add fallback_chains)
```

### Architecture Excerpts

From `providers/base.py`:
- `BaseProvider` is ABC with `invoke(prompt, task_path, output_dir, timeouts) -> InvocationResult`
- `ProviderError` raised for configuration/invocation failures

From `providers/codex.py`:
- `load_provider_config(path, alias) -> ProviderConfig` parses frontmatter
- `validate_binary() -> str | None` checks CLI availability via `shutil.which`
- `build_command() -> list[str]` assembles CLI invocation
- `invoke()` returns `InvocationResult` with `ok`, `exit_code`, `error_message`, `output_paths`

From `dispatcher.py`:
- `STAGE_PROVIDER_KEYS = {"plan": "planner", "code": "coder", "audit": "auditor"}`
- `_build_provider(alias, alias_config) -> CodexProvider` — needs extension for new providers
- `dispatch_stage()` calls provider, evaluates result, returns `StageResult`

### Code Excerpts

**`providers/base.py:14-22`** — Abstract interface to implement:
```python
class BaseProvider(ABC):
    @abstractmethod
    def invoke(
        self,
        prompt: str,
        task_path: Path,
        output_dir: Path,
        timeouts: StageTimeoutConfig,
    ) -> InvocationResult:
```

**`providers/codex.py:30-55`** — Config loading pattern:
```python
@staticmethod
def load_provider_config(path: Path, alias: str | None = None) -> ProviderConfig:
    if not path.exists():
        raise ProviderError(f"Provider config not found: {path}")
    metadata, _body = split_frontmatter(path.read_text(encoding="utf-8"))
    cli = str(metadata.get("cli", "")).strip()
    subcommand = str(metadata.get("subcommand", "")).strip()
    # ... parse unattended_flags, output_flags, prompt_style, config_overrides
```

**`providers/codex.py:68-85`** — Command building pattern:
```python
def build_command(self) -> list[str]:
    command = [
        self.provider_config.cli,
        self.provider_config.subcommand,
        *self.provider_config.unattended_flags,
        *self.provider_config.output_flags,
    ]
    model = self.alias_config.model or self.provider_config.model
    if model:
        command.extend(["--model", model])
    # ... add config_overrides
```

**`dispatcher.py:45-52`** — Provider selection (modify for fallback):
```python
def dispatch_stage(self, *, task_path: Path, run_id: str) -> StageResult:
    before = parse_task_file(task_path)
    stage = before.stage
    provider_key = STAGE_PROVIDER_KEYS[stage]
    alias_config = self.config.providers[provider_key]
    provider = self._build_provider(alias_config.alias, alias_config)
```

**`config.json:3-14`** — Current provider config structure:
```json
"providers": {
  "planner": {"alias": "codex-low", "model": null, "config_overrides": {}},
  "coder": {"alias": "codex", "model": null, "config_overrides": {}},
  "auditor": {"alias": "codex-high", "model": null, "config_overrides": {}},
  "auditor_escalation": {"alias": "codex-xhigh", "model": null, "config_overrides": {}}
}
```

**`_providers/opus.md`** — Claude provider config example:
```yaml
cli: claude
model: claude-opus-4-6
unattended_flags: ['--dangerously-skip-permissions']
output_flags: ['--output-format', json]
prompt_style: flag
```

**`_providers/kimi.md`** — Qwen provider config example:
```yaml
cli: kimi
model: kimi-k2-thinking-turbo
unattended_flags: ['--print']
output_flags: ['--quiet']
prompt_style: flag
```

### Dependency Graph

**Files importing from `providers/`:**
- `dispatcher.py:14` — `from orchestrator.providers.codex import CodexProvider`
- `providers/__init__.py` — exports `BaseProvider`, `CodexProvider`, `ProviderError`
- `providers/codex.py:11` — `from orchestrator.providers.base import BaseProvider, ProviderError`

**Files importing from `dispatcher.py`:**
- `cli.py:9` — `from orchestrator.dispatcher import Dispatcher`
- `__init__.py:7` — `from orchestrator.dispatcher import Dispatcher`

**Files importing from `models.py`:**
- `config.py` — imports config dataclasses
- `dispatcher.py` — imports `RunState`, `StageResult`, `TaskRunState`
- `providers/codex.py` — imports `InvocationResult`, `ProviderAliasConfig`, `ProviderConfig`, `StageTimeoutConfig`
- `sessions.py` — imports `SessionResult`, `StageTimeoutConfig`

### Patterns to Follow

1. **Provider class structure**: Follow `CodexProvider` exactly — same `__init__`, `load_provider_config`, `validate_binary`, `build_command`, `invoke` methods
2. **Config parsing**: Use `split_frontmatter()` from `scanner.py`, validate required fields (`cli`), raise `ProviderError` on missing config
3. **Binary validation**: Use `shutil.which(cli)` to check availability before invocation
4. **Command building**: Start with `[cli, subcommand, *unattended_flags, *output_flags]`, add `--model` if specified
5. **Error handling**: Return `InvocationResult(ok=False, error_message=...)` for missing binary, wrap session errors in try/except

### Test Patterns

From `tests/test_providers.py`:
- Create temp provider config file with frontmatter
- Test `load_provider_config()` parses correctly
- Test `build_command()` produces expected CLI args
- Test missing binary detection with fake CLI name
- Use `FakeSessionManager` mock for `invoke()` tests

From `tests/test_dispatcher.py`:
- Use `ScriptedDispatcher` with `scripted_results` list
- Use `monkeypatch.setattr()` to override `dispatch_stage`
- Test handoff scenarios with `run_state.status == "handoff_required"`

### Gotchas

- **Claude `prompt_style: flag`**: Claude CLI uses `--prompt` flag, not stdin. Check `prompt_style` in config and handle accordingly.
- **Gemini model names**: Use exact model string (e.g., `gemini-3-flash-preview`), no alias resolution needed
- **Qwen model aliases**: Qwen CLI supports aliases like `kimi-k2.5`, `minimax` — pass through as-is
- **Account symlink atomicity**: Use `ln -sf` (force) to atomically switch auth files
- **Health check parsing**: `codex login status` output format may vary — check for success indicators

### Scope Boundaries

This task is standalone in phase3. No sibling tasks exist. All subtasks (3.1-3.4) are part of this single task file.

---

## Review

**Rating: 7/10**

**Verdict: NEEDS WORK**

### Summary
The previous routing and logging gaps are fixed, and the targeted provider/routing test suite now passes. One important behavior is still wrong, though: when account rotation exhausts the Codex pool, the dispatcher logs a warning and continues anyway instead of escalating the task.

### Findings

#### Blockers
- [x] Account-rotation failure is swallowed instead of escalating: `AccountManager.get_account_for_task()` already performs round-robin fallback and raises when the entire pool is unhealthy, but `dispatch_stage()` catches that exception and still invokes Codex with whatever auth state was already on disk. That violates the task rule "if all fail, escalate" and can run a task against the wrong account. - `src/orchestrator/dispatcher.py:86`

#### High Priority
- [ ] None.

#### Medium Priority
- [x] The new tests cover the happy path for `AccountManager` invocation, but there is still no dispatcher-level test that verifies an exhausted account pool produces a stage failure or handoff. That leaves the remaining blocker unguarded. - `tests/test_routing.py:311`

#### Low Priority / Nits
- [ ] None.

### Test Assessment
- Coverage: Needs improvement
- Missing tests: Dispatcher test for "all accounts failed" causing transport failure/handoff instead of continuing with Codex; integration test showing the same assigned Codex account survives an audit bounce end-to-end

### What's Good
- [ ] The prior issues around frontmatter-based OpenAI provider resolution and persisted provider alias/model logging are fixed, and the targeted suites for accounts/providers/routing now pass.

### Recommendations
- [ ] Treat `AccountError` from `get_account_for_task()` as a real stage failure so the normal retry/handoff path can escalate when every Codex account is unhealthy, then add a regression test for that branch.

---

## Audit

src/orchestrator/accounts.py
src/orchestrator/dispatcher.py
src/orchestrator/providers/claude.py
src/orchestrator/providers/gemini.py
src/orchestrator/providers/qwen.py
src/orchestrator/providers/__init__.py
tests/test_routing.py
config.json
