---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 2.4: Stage dispatcher and result evaluator

## Goal

Build the stage execution logic that runs providers and evaluates frontmatter transitions.

## Definition of Done

- [ ] Dispatcher takes a task path, selects provider, assembles prompt, spawns session, waits, evaluates
- [ ] Evaluator compares before/after TaskSnapshots to determine result kind
- [ ] Plan result: success if stage moved to code + required sections present; blocked if questions added
- [ ] Code result: success if stage moved to audit + Audit section present + file changed
- [ ] Audit result: success if rating ≥ 8 + completed; quality_failure if rating < 8 + back to code
- [ ] Transport failure if expected transition did not happen
- [ ] All results include provider key, alias, model, exit code, output paths

## Files

- `src/orchestrator/dispatcher.py` - create - stage execution orchestration
- `src/orchestrator/evaluator.py` - create - before/after snapshot comparison

## Tests

- [ ] Plan success detected when frontmatter changes to stage: code, agent: coder
- [ ] Plan blocked detected when Questions section added
- [ ] Code success detected when frontmatter changes to stage: audit, agent: auditor
- [ ] Audit acceptance detected when rating ≥ 8 and stage: completed
- [ ] Audit rework detected when rating < 8 and stage: code
- [ ] Transport failure detected when no expected transition occurs

## Context

Phase 2: Single-Task Execution Engine
