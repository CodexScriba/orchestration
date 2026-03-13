---
name: Architecture
description: Codebase and project description
scope: global
created: '2025-12-17'
file_references:
  - docs/architecture.md
---

# Architecture Context

This context file links to the main architecture documentation. When the auditor accepts a task (rating 8+), they should update this file or the linked documentation to reflect any new files created.

See: [docs/architecture.md](docs/architecture.md) for the full architecture documentation including directory structure.

## Accepted Task Updates

- date: 2026-02-11
  - task: `task1.1-add-agent-and-attempts-fields-to-task-interface`
  - files-updated:
    - `src/types/task.ts` (`Task` now includes optional `agent?: string` and `attempts?: number`)
    - `src/services/frontmatter.ts` (parse + stringify support for `agent` and `attempts`)
  - new-files-created: none

- date: 2026-02-11
  - task: `task1.2-define-providerconfig-and-agentconfig-types-with-zod-schemas`
  - files-updated: none
  - new-files-created:
    - `src/types/provider.ts` - Defines `ProviderConfig` interface and Zod schema for CLI configuration
    - `src/types/agent.ts` - Defines `AgentConfig` interface and Zod schema for agent configuration
    - `tests/provider-agent-schemas.test.ts` - Tests for the provider and agent schema validation

- date: 2026-02-11
  - task: `task1.3-add-agents-folder-and-logs-folder-constants`
  - files-updated:
    - `src/core/constants.ts` (added `AGENTS_FOLDER = '_agents'` and `LOGS_FOLDER = '_logs'`)
  - new-files-created: none

- date: 2026-02-11
  - task: `task2.1-create-agentservice-crud-for-agents`
  - files-updated:
    - `docs/architecture.md` (added `agent-service.ts` to service list)
  - new-files-created:
    - `src/services/agent-service.ts` - Service for CRUD operations on agent files
    - `tests/agent-service.test.ts` - Tests for agent files CRUD operations

- date: 2026-02-11
  - task: `task2.2-create-providerservice-crud-for-new-providers-cli-config-files`
  - files-updated: none
  - new-files-created:
    - `src/services/provider-service.ts` - CRUD service for provider CLI configuration files in `_providers/`
    - `tests/provider-service.test.ts` - Tests for provider CLI config CRUD operations

- date: 2026-02-11
  - task: `task2.3-update-frontmatter-parser-for-agent-and-attempts`
  - files-updated:
    - `src/services/frontmatter.ts` (parse/serialize `agent` and `attempts` fields)
    - `src/services/task-content.ts` (`saveTaskWithMetadata` metadata interface now includes `agent`)
    - `src/webview/KanbanPanel.ts` (threads `agent` through `FullTaskDataLoaded` and `SaveTaskWithMetadata`)
    - `src/webview/SidebarProvider.ts` (threads `agent` through `FullTaskDataLoaded` and `SaveTaskWithMetadata`)
    - `src/webview/ui/components/TaskEditorModal.tsx` (manages `agent` state, dirty checking, save)
    - `tests/frontmatter.test.ts` (4 new tests for agent/attempts parsing, serialization, round-trip)
  - new-files-created: none

- date: 2026-02-11
  - task: `task2.4-update-prompt-builder-for-agent-aware-context-loading`
  - files-updated:
    - `src/services/prompt-builder.ts` (added `loadAgentInstructions` with 3-step fallback chain, `buildRunnerPrompt` export, runner `<runner automated="true" />` injection)
  - new-files-created: none
  - tests-added:
    - `tests/prompt-builder.test.ts` (5 new tests: agent loading, provider-to-agent fallback, provider fallback, runner prompt shape, runner automated flag)

- date: 2026-02-11
  - task: `task2.5-update-stage-manager-for-agent-aware-auto-assignment`
  - files-updated:
    - `src/services/stage-manager.ts` (added `AgentInfo`, `listAgentsWithStage`, `getDefaultAgentForStage`, `getDefaultProviderForAgent`, `shouldAutoUpdateAgent`; updated `updateTaskStage` to auto-set `agent` and `provider` from agent defaults with fallback to stage-based provider assignment)
  - new-files-created: none
  - tests-added:
    - `tests/stage-manager.test.ts` (5 new tests: agent-for-stage lookup, provider-for-agent config lookup, auto-set agent+provider on code/audit stages, manual agent preservation)

- date: 2026-02-11
  - task: `task3.1-create-migration-service-providers-to-agents-new-providers`
  - files-updated:
    - `.kanban2code/.gitignore` (added `_logs/` entry)
  - new-files-created:
    - `src/services/migration.ts` - Atomic migration service for providers → agents transition
    - `tests/migration.test.ts` - Tests for migration service functionality
  - tests-added:
    - 4 tests: migration success, idempotence, rollback, gitignore update

- date: 2026-02-11
  - task: `task3.2-update-build-script-to-bundle-agents`
  - files-updated:
    - `build.ts` (added `_agents/` directory reading to `generateBundledContent()`)
  - new-files-created:
    - `src/assets/agents.ts` - Auto-generated file containing bundled agent files

- date: 2026-02-11
  - task: `task3.3-update-scaffolder-for-agents-directory`
  - files-updated:
    - `src/services/scaffolder.ts` (added `_agents/` to scaffold and sync functions)
    - `tests/scaffolder.test.ts` (added tests for agent scaffolding)
  - new-files-created: none
  - tests-added:
    - 2 tests: scaffold creates agents, sync preserves existing agents

- date: 2026-02-11
  - task: `task3.4-register-migration-command-verify-file-watcher-coverage`
  - files-updated:
    - `src/commands/index.ts` (registered `kanban2code.migrateProvidersAgents` command with VS Code progress notification)
    - `src/services/task-watcher.ts` (added `_agents/` and `_providers/` exclusion in `isTaskFile()`)
    - `package.json` (added command declaration and activation event)
  - new-files-created: none
  - tests-added:
    - 2 tests in `tests/task-watcher.test.ts`: `_agents/` and `_providers/` exclusion from task events

- date: 2026-02-11
  - task: `task4.0-deterministic-task-ordering-in-scanner`
  - files-updated:
    - `src/services/scanner.ts` (added `sortTasks` and `getOrderedTasksForStage` exports; `loadAllTasks` now returns sorted results)
    - `tests/scanner.test.ts` (added 10 tests for deterministic ordering)
  - new-files-created: none
  - tests-added:
    - 10 tests: order field sorting, undefined order handling, filename tiebreaker, stage filtering, immutability

- date: 2026-02-11
  - task: `task4.1-cli-adapter-interface-claude-adapter`
  - files-updated: none
  - new-files-created:
    - `src/runner/cli-adapter.ts` - `CliAdapter` interface, `CliResponse`, `CliCommandResult`, `CliAdapterOptions` types
    - `src/runner/adapters/claude-adapter.ts` - Claude CLI adapter implementation
    - `tests/claude-adapter.test.ts` - Tests for Claude adapter

- date: 2026-02-11
  - task: `task4.2-codex-kimi-and-kilo-cli-adapters-adapter-factory`
  - files-updated: none
  - new-files-created:
    - `src/runner/adapters/codex-adapter.ts` - Codex CLI adapter (stdin prompt, JSONL output)
    - `src/runner/adapters/kimi-adapter.ts` - KIMI CLI adapter (-p flag, plain text output)
    - `src/runner/adapters/kilo-adapter.ts` - Kilo CLI adapter (positional prompt, JSONL output)
    - `src/runner/adapter-factory.ts` - Factory function `getAdapterForCli(cli) → CliAdapter`
    - `tests/other-cli-adapters.test.ts` - Tests for Codex, KIMI, Kilo adapters and factory

- date: 2026-02-11
  - task: `task4.3-structured-output-parser`
  - files-updated: none
  - new-files-created:
    - `src/runner/output-parser.ts` - Structured marker extraction for LLM output
    - `tests/output-parser.test.ts` - Tests for output-parser
  - tests-added:
    - 8 tests: stage transitions, audit ratings, verdicts, file lists, and fallbacks

- date: 2026-02-11
  - task: `task4.5-git-operations-for-runner`
  - files-updated: none
  - new-files-created:
    - `src/runner/git-ops.ts` - Git helper functions for runner (`isWorkingTreeClean`, `hasUncommittedChanges`, `commitRunnerChanges`)
    - `tests/git-ops.test.ts` - Tests for git operations (3 tests)

- date: 2026-02-11
  - task: `task4.4-runner-execution-engine`
  - files-updated: none
  - new-files-created:
    - `src/runner/runner-engine.ts` - Core runner execution engine with sequential pipeline logic
    - `tests/runner-engine.test.ts` - Tests for RunnerEngine
  - tests-added:
    - 6 tests: pipeline execution, audit failure loops, CLI crash handling, dirty git check

- date: 2026-02-11
  - task: `task4.6-runner-log-report-generator`
  - files-updated: none
  - new-files-created:
    - `src/runner/runner-log.ts` - `RunnerLog` class for generating markdown run reports
    - `tests/runner-log.test.ts` - Tests for runner log generation and persistence
  - tests-added:
    - 4 tests: markdown headers, summary counts, per-task fields, zero-task handling

- date: 2026-02-11
  - task: `task4.7-register-runner-vs-code-commands`
  - files-updated:
    - `src/commands/index.ts` (registered runner commands)
    - `src/extension.ts` (runner singleton lifecycle, progress API)
    - `package.json` (added runner commands)
  - new-files-created:
    - `tests/runner-singleton.test.ts` - Tests for runner singleton and cancellation

- date: 2026-02-11
  - task: `task5.1-update-messaging-protocol-for-modes-and-runner`
  - files-updated:
    - `src/webview/messaging.ts` (added mode-management and runner-control message types; added `RunnerState` type/schema/parser)
    - `tests/webview.test.ts` (added EnvelopeSchema coverage for new message types and RunnerState validation tests)
  - new-files-created: none

- date: 2026-02-11
  - task: `task5.2-modepicker-component-update-agentpicker`
  - files-updated:
    - `src/webview/ui/components/AgentPicker.tsx` (Agent picker now targets LLM providers, updates label to "Agent (LLM Provider)", and keeps provider description hint behavior)
    - `src/webview/ui/components/TaskEditorModal.tsx` (uses provider-based AgentPicker wiring)
    - `src/webview/ui/components/TaskModal.tsx` (uses provider-based AgentPicker wiring)
    - `tests/webview/components/AgentPicker.test.tsx` (covers provider rendering, label text, no-selection behavior, and canonical name resolution)
  - new-files-created:
    - `src/webview/ui/components/ModePicker.tsx` - Mode dropdown component with mode description hint and "Create new mode" action
    - `tests/webview/components/ModePicker.test.tsx` - ModePicker component tests for rendering, selection, callbacks, and no-selection behavior

- date: 2026-02-11
  - task: `task5.3-runner-controls-on-column-headers`
  - files-updated:
    - `src/webview/ui/components/Column.tsx` (added runner control buttons: play, play-all, stop; visibility logic based on `isRunnerActive` and `stage`)
    - `src/webview/ui/components/BoardHorizontal.tsx` (passed down runner control props to Column)
    - `src/webview/ui/styles/main.css` (styles for runner controls and buttons)
    - `tests/webview/column.test.tsx` (added 6 tests for runner control visibility, behavior, and callbacks)
  - new-files-created: none

- date: 2026-02-12
  - task: `task5.4-update-taskcard-for-mode-runner-status`
  - files-updated:
    - `src/webview/ui/components/TaskCard.tsx` (footer now renders `mode | agent` when both exist, shows agent-only fallback, adds per-card run action and running-state indicator)
    - `src/webview/ui/components/Icons.tsx` (added `PlayIcon` for card-level run action)
    - `src/webview/ui/components/Column.tsx` (threads `runningTaskId` and `onRunTask` into TaskCard)
    - `src/webview/ui/components/BoardHorizontal.tsx` (threads `runningTaskId` and `onRunTask` into Column)
    - `src/webview/ui/styles/main.css` (added running card pulse border, spinner, and disabled action styling)
    - `tests/webview/taskcard.test.tsx` (added tests for mode+agent footer display, run button stage visibility, and active runner indicator)
  - new-files-created: none

- date: 2026-02-12
  - task: `task5.5-update-taskmodal-and-taskeditormodal-for-mode-field`
  - files-updated:
    - `src/webview/ui/components/TaskModal.tsx` (added ModePicker below AgentPicker, `mode` in form data and CreateTask payload)
    - `src/webview/ui/components/TaskEditorModal.tsx` (added ModePicker to Assignment section, `mode` in metadata state, dirty checking, and SaveTaskWithMetadata payload)
    - `src/webview/ui/components/Sidebar.tsx` (threads `modes` from `useTaskData` to `TaskModal`)
    - `src/webview/ui/components/Board.tsx` (threads `modes` from `useTaskData` to `TaskModal`)
    - `src/webview/ui/hooks/useTaskData.ts` (exposes `modes` in return value, handles `InitState` modes payload)
    - `src/webview/SidebarProvider.ts` (loads modes via `listAvailableModes`, sends in `InitState` and `FullTaskDataLoaded`)
    - `src/webview/KanbanPanel.ts` (loads modes via `listAvailableModes`, sends in `InitState` and `FullTaskDataLoaded`)
    - `src/commands/index.ts` (writes `mode` to frontmatter in `newTask` command)
    - `tests/webview/task-modal-create-project.test.tsx` (added tests for mode+agent picker rendering and CreateTask payload)
    - `tests/webview/task-editor-modal.test.tsx` (added tests for mode+agent picker rendering, SaveTaskWithMetadata payload with mode, null mode backward compat)
  - new-files-created: none

- date: 2026-02-12
  - task: `task5.6-wire-runner-messages-through-webview-hosts`
  - files-updated:
    - `src/webview/KanbanPanel.ts` (added `RunTask`, `RunColumn`, `StopRunner` message handlers; subscribes to `onRunnerStateChanged` and posts `RunnerStateChanged` to webview; includes runner state in `InitState`)
    - `src/webview/SidebarProvider.ts` (added `RequestModes`, `CreateMode`, `RunTask`, `RunColumn`, `StopRunner` message handlers; subscribes to `onRunnerStateChanged` and posts `RunnerStateChanged` to webview; includes runner state in `InitState`)
    - `src/webview/ui/hooks/useTaskData.ts` (exposes `modes`, `isRunnerActive`, `activeRunnerTaskId` in return value; handles `RunnerStateChanged` and `ModesLoaded` messages)
  - new-files-created:
    - `src/runner/runner-state.ts` - Simple event emitter module for runner state (get/set/subscribe)
    - `tests/webview-host-runner.test.ts` - Tests for webview host runner message handling
    - `tests/webview/useTaskData.runner.test.tsx` - Tests for useTaskData runner state tracking

- date: 2026-02-12
  - task: `task5.7-modemodal-component-create-edit-mode`
  - files-updated:
    - `src/webview/ui/components/index.ts` (added `ModeModal` barrel export)
    - `src/webview/ui/styles/main.css` (added `.mode-modal` size class alongside `.agent-modal`)
  - new-files-created:
    - `src/webview/ui/components/ModeModal.tsx` - Modal for creating and editing mode files (glassmorphic pattern)
    - `tests/webview/components/ModeModal.test.tsx` - Tests for ModeModal (field rendering, validation, edit mode pre-population)

- date: 2026-02-12
  - task: `task5.8-update-context-menu-for-mode-and-runner-actions`
  - files-updated:
    - `src/webview/ui/components/TaskContextMenu.tsx` (added "Run Task" action with runner-active/stage guard, "Change Mode" submenu, "Change Agent" submenu, and `updateTaskMetadata` helper for `SaveTaskWithMetadata`)
    - `src/webview/ui/components/Sidebar.tsx` (passes `modes`, `agents`, `isRunnerActive` to TaskContextMenu)
    - `src/webview/ui/components/Board.tsx` (passes `modes`, `agents`, `isRunnerActive` to TaskContextMenu)
    - `tests/webview/components/TaskContextMenu.test.tsx` (4 tests: Run Task visibility, disabled state, mode submenu, agent submenu)
  - new-files-created: none

- date: 2026-02-12
  - task: `task6.2-redesign-coder-mode-for-structured-output`
  - files-updated:
    - `.kanban2code/_modes/coder.md` (added dual-mode instructions: Mode Detection, Manual/Automated output and workflow sections; explicit no-commit rule in automated mode)
  - new-files-created: none

- date: 2026-02-12
  - task: `refactor-mode-to-agent-and-agent-to-provider`
  - description: Comprehensive refactoring to align terminology with industry standards.
  - files-updated:
    - `src/types/*.ts`, `src/services/*.ts`, `src/runner/*.ts`, `src/webview/*.tsx`, `tests/*.ts`
    - `package.json`, `build.ts`, `scaffolder.ts`
  - new-files-created:
    - `.kanban2code/_providers/` (moved from defunct modes)
    - `src/assets/providers.ts` (replaced `modes.ts`)
  - status: completed

- date: 2026-02-13
  - task: `1770933535169-create-a-coming-soon-page`
  - files-updated: none
  - new-files-created:
    - `docs/design/coming-soon.html` - Standalone modern glassmorphic landing page with hero, 6-feature teaser grid, preview placeholder, CTA, and footer

- date: 2026-02-13
  - task: `1771012835226-add-more-codex-providers`
  - files-updated:
    - `src/assets/providers.ts` (regenerated bundled providers now include codex reasoning-effort variants)
    - `tests/provider-service.test.ts` (added coverage for parsing `config_overrides.model_reasoning_effort`)
    - `tests/scaffolder.test.ts` (added assertions that new codex variant provider files scaffold correctly)
  - new-files-created:
    - `.kanban2code/_providers/codex-low.md` - Codex provider preset with `model_reasoning_effort: low`
    - `.kanban2code/_providers/codex-high.md` - Codex provider preset with `model_reasoning_effort: high`
    - `.kanban2code/_providers/codex-xhigh.md` - Codex provider preset with `model_reasoning_effort: xhigh`
