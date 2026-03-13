---
stage: inbox
agent: "02-\U0001F3DB️architect"
bounces: 0
tags:
  - orchestration
  - roadmap
  - supervisor
contexts:
  - .kanban2code/how-it-works.md
  - .kanban2code/architecture.md
updated: 2026-03-13T00:00:00.000Z
skills: []
---

# Roadmap — Orchestration project

## Goal
Design a brand new orchestrator for Kanban2Code-first workflows.

## Working decisions
- Kanban2Code-first, not generic-first.
- Kanban2Code task frontmatter remains the source of truth.
- Kanban2Code should mutate its own task state.
- The orchestrator acts as a supervisor, not the owner of task truth.
- Supplemental orchestrator state (DB/JSON) is allowed for queue/run metadata only.
- The new project lives separately at `/home/cynicus/code/orchestration`.

## Open questions
- Should the supervisor run one task at a time serially or support parallel runs from day one?
- What should be the first runnable MVP loop?
- What exact metadata belongs in orchestrator-only state?
- How should notifications/reporting be emitted?

## Notes
Use this file to capture decisions as we make them so conversation context loss does not reset the design.

## New decisions
- Add an orchestrator memory system with hot, warm, and cold layers.
- Orchestrator memory should hold operational/project context so Kadee can stay lighter and link into it when needed.
- The orchestrator should be a smart but bounded supervisor.
- It may detect blockers, choose among eligible tasks, and keep unrelated work moving concurrently.
- It must not skip stages, rewrite task truth loosely, or bypass guardrails.
- Communication is a first-class requirement: Dan wants to stay on top of development in real time.
- Python should communicate through state files and/or OpenClaw session messages, with Kadee acting as the human-facing supervisor.
- Tunnel-based oversight enables a kill switch if something starts going south.

## Additional decisions
- The orchestrator should maintain a programmatic state view of Kanban2Code tasks by project and stage (inbox, plan, code, audit, completed).
- This state view should be easy for Kadee to read so she can understand board status quickly without re-reading every task file.
- The orchestrator should own queueing/eligibility/concurrency decisions within guardrails.
- The orchestrator should log what is being run, including provider/model/account used per run.
- Account switching should be part of the MVP.
- Account usage/status lookup should be part of the MVP if it is easy to query.
- Logs/state should be readable enough that Kadee can translate them into real-time updates for Dan.

- Agent runs should use tmux-managed visible sessions rather than hidden subprocess-only execution.
- The orchestrator should support multiple concurrent tasks from day one, with guardrails.
- Tasks marked as blocking or governed by rules that require waiting (for example UI-dependent tasks) should not be auto-run concurrently.
- Concurrency should be decided dynamically rather than by a fixed low cap.
- Dynamic concurrency decisions should still respect explicit guardrails and task eligibility rules.
- The orchestrator may pause or deprioritize a task when it detects the task is waiting on Dan.
- When this happens, it should notify Dan on Telegram and continue with other eligible work.
- MVP notification policy: notify Dan on every stage change.
- Notification verbosity can be reduced later if it becomes noisy.
- Stage-change notifications should include the account and model/provider used for that run.
- Max audit bounces = 2, then stop and notify Dan.
- No silent waiting: blocked/waiting/stalled states must be logged and notified.
- No hidden stage jumps unless an explicit rule allows it.
- Safe concurrency only: do not run tasks together if they touch the same files or area.
- Commit rules are explicit: after each audit pass, auto-commit.
- After each phase or major project milestone, create a new branch for safety.
- Everything should be logged: stage, account, model, start, finish, error, and reason.
- Auto-commit is enabled after audit pass.
- The orchestrator DB/state must not override Kanban2Code task truth, especially in MVP.
- Blocked states include: waiting on human, expected outcome did not happen, or auth/provider issues after fallback attempts.
- If a stage runs and the expected outcome does not happen (example: planner runs but does not update the task), mark it clearly rather than pretending progress.
- On auth/provider issues, try fallback or a different account first, then notify Dan if still blocked.
- MVP execution scope is only: plan -> code -> audit.
- Architecture remains human-led; the orchestrator itself should not own architecture decisions.
- Kadee may be involved in architecture or splitter work directly, but that is separate from the orchestrator runtime.
- Projects are entered explicitly by Kadee from Dan-provided name and location; the orchestrator should not auto-scan arbitrary projects by default.
- Conflict detection/concurrency safety will be decided by the orchestrator within guardrails.
- Planning model preference: Google Flash 3.0/3.1; avoid 2.5. Fallbacks may include Qwen Kimi 2.5, MiniMax, other Qwen models, or Haiku.
- Coding model preference: Codex 5.4 with medium reasoning; fallbacks include Sonnet 4.6 or GLM via Qwen CLI.
- Stage success should be validated by task metadata/frontmatter changes; agents must update task state clearly when done.
- Notification format can be decided by Kadee/orchestrator design during implementation.
- Add a smoke test as part of the orchestrator.
- The smoke test should call Qwen, Gemini, Claude, and Codex once each during development.
- Minimal expected response can be something simple like saying hi back, just to verify wiring/auth/runtime health.

## Kadee role in the system
- Kadee is the smart supervisory layer, not the primary executor.
- Kadee reads orchestrator state, logs, and Kanban2Code task truth to understand what is happening.
- Kadee helps decide queueing, blocker handling, escalation, and communication within guardrails.
- Kadee does not own task truth and should not casually override Kanban2Code state.
- Kadee communicates progress, blockers, stage changes, account/model usage, and critical events to Dan.
- Kadee can inspect live runs through tunnel access and tmux-managed sessions, and act as a kill switch if a run is going south.
- Kadee may participate directly in architecture/splitter discussions, but that is separate from the orchestrator runtime itself.
