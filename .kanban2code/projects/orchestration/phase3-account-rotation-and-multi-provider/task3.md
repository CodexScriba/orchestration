---
stage: plan
tags: [feature, p3]
agent: planner
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
- [ ] Account pool loaded from config (list of account names)
- [ ] Rotation: pick next account per task, keep same through bounces
- [ ] Switch mechanism: symlink `~/.codex/auth.json` to `~/.codex/accounts/TARGET.json`
- [ ] Health check: run `codex login status` after switch, parse result
- [ ] Round-robin fallback: if account fails, try next; if all fail, escalate
- [ ] Log which account is active for each task

### Claude Provider
- [ ] `ClaudeProvider` implements `BaseProvider`
- [ ] Loads config from `.kanban2code/_providers/opus.md`, `sonnet.md`, `haiku.md`
- [ ] Builds correct `claude` CLI command with model, flags, and prompt
- [ ] Supports stdin prompt delivery
- [ ] Captures output for evaluation

### Gemini and Qwen Providers
- [ ] `GeminiProvider` implements `BaseProvider` for Google Gemini CLI
- [ ] `QwenProvider` implements `BaseProvider` for Qwen CLI
- [ ] Each loads config from its respective `_providers/*.md` file
- [ ] Qwen supports model aliases (kimi-k2.5, minimax, etc.)
- [ ] Gemini supports model name format (`gemini-3-flash-preview`)

### Model Routing
- [ ] Config defines provider preference per stage with ordered fallback list
- [ ] Planning: Gemini Flash 3.0/3.1 primary (not 2.5) → Qwen Kimi 2.5 → Haiku / MiniMax / other Qwen fallback
- [ ] Coding: Codex 5.4 medium → Sonnet 4.6 → GLM via Qwen CLI
- [ ] Auditing: Opus 4.6 thinking → Codex 5.4 xhigh
- [ ] On provider failure, automatically try next in fallback chain
- [ ] Log which provider/model was actually used

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